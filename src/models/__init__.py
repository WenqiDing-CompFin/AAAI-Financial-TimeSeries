"""Multi-modal TimeCAP encoder (time-series patches + text embedding)."""

from __future__ import annotations

import math
from typing import List, Optional, Tuple, Union

import torch
import torch.nn as nn
import torch.nn.functional as F


class PatchEmbedding(nn.Module):
    """Non-overlapping / strided patch projection for multivariate series."""

    def __init__(self, d_model: int, patch_len: int, stride: int, dropout: float = 0.1):
        super().__init__()
        self.patch_len = patch_len
        self.stride = stride
        self.padding = stride
        self.value_embedding = nn.Linear(patch_len, d_model, bias=False)
        self.position_embedding = nn.Parameter(torch.randn(1, 1024, d_model) * 0.02)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, int]:
        # x: [B, C, L]
        b, c, l = x.shape
        x = F.pad(x, (0, self.padding))
        x = x.unfold(dimension=-1, size=self.patch_len, step=self.stride)  # [B, C, N, P]
        n_patches = x.shape[2]
        x = x.reshape(b * c, n_patches, self.patch_len)
        x = self.value_embedding(x)
        x = x + self.position_embedding[:, :n_patches, :]
        return self.dropout(x), c


class MultiHeadAttention(nn.Module):
    def __init__(self, d_model: int, n_heads: int, dropout: float = 0.1):
        super().__init__()
        assert d_model % n_heads == 0
        self.n_heads = n_heads
        self.d_head = d_model // n_heads
        self.qkv = nn.Linear(d_model, d_model * 3)
        self.out = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, n, d = x.shape
        qkv = self.qkv(x).reshape(b, n, 3, self.n_heads, self.d_head)
        q, k, v = qkv.unbind(dim=2)
        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)
        attn = (q @ k.transpose(-2, -1)) / math.sqrt(self.d_head)
        attn = self.dropout(attn.softmax(dim=-1))
        out = (attn @ v).transpose(1, 2).reshape(b, n, d)
        return self.out(out)


class EncoderLayer(nn.Module):
    def __init__(self, d_model: int, n_heads: int, d_ff: int, dropout: float, activation: str = "gelu"):
        super().__init__()
        self.attn = MultiHeadAttention(d_model, n_heads, dropout)
        self.ff = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU() if activation == "gelu" else nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.norm1(x + self.dropout(self.attn(x)))
        x = self.norm2(x + self.dropout(self.ff(x)))
        return x


class TextEncoder(nn.Module):
    """
    Lightweight text encoder.
    Uses sentence-transformers when available; otherwise a hash bag-of-words projection
    so CPU smoke tests still run without downloading large models.
    """

    def __init__(self, lm_model: str, d_model: int, dropout: float = 0.1):
        super().__init__()
        self.lm_model_name = lm_model
        self.fallback_dim = 384
        self.proj = nn.Linear(self.fallback_dim, d_model)
        self.dropout = nn.Dropout(dropout)
        self._st_model = None
        self._use_st = False

        try:
            from sentence_transformers import SentenceTransformer

            name_map = {
                "sentence": "paraphrase-MiniLM-L6-v2",
                "minilm6": "all-MiniLM-L6-v2",
                "minilm12": "all-MiniLM-L12-v2",
                "mpnet": "all-mpnet-base-v2",
            }
            model_id = name_map.get(lm_model, "all-MiniLM-L6-v2")
            # Lazy: only mark as available; load on first encode to keep import light
            self._st_model_id = model_id
            self._SentenceTransformer = SentenceTransformer
            self._use_st = True
            in_dim = 768 if lm_model in {"mpnet"} else 384
            self.proj = nn.Linear(in_dim, d_model)
        except Exception:
            self._use_st = False
            self.proj = nn.Linear(self.fallback_dim, d_model)

    def _hashed_embed(self, texts: List[str], device: torch.device) -> torch.Tensor:
        vecs = []
        for text in texts:
            v = torch.zeros(self.fallback_dim, dtype=torch.float32)
            for token in text.lower().split():
                h = hash(token) % self.fallback_dim
                v[h] += 1.0
            if v.norm() > 0:
                v = v / v.norm()
            vecs.append(v)
        return torch.stack(vecs, dim=0).to(device)

    def encode(self, texts: List[str], device: torch.device) -> torch.Tensor:
        if self._use_st:
            if self._st_model is None:
                try:
                    self._st_model = self._SentenceTransformer(self._st_model_id)
                except Exception:
                    self._use_st = False
                    return self.proj(self._hashed_embed(texts, device))
            emb = self._st_model.encode(texts, convert_to_numpy=True)
            emb_t = torch.from_numpy(emb).float().to(device)
            return self.dropout(self.proj(emb_t))
        return self.dropout(self.proj(self._hashed_embed(texts, device)))


class MultiModalEncoder(nn.Module):
    """
    TimeCAP multi-modal encoder E_φ:
      - patchify time series
      - embed contextual text summary
      - concatenate token streams per channel
      - transformer encode → prediction + embedding
    """

    def __init__(
        self,
        enc_in: int,
        seq_len: int,
        num_outputs: int,
        d_model: int = 128,
        n_heads: int = 4,
        e_layers: int = 2,
        d_ff: int = 256,
        patch_len: int = 4,
        stride: int = 2,
        dropout: float = 0.1,
        activation: str = "gelu",
        lm_model: str = "minilm6",
        task: str = "classification",
    ):
        super().__init__()
        self.enc_in = enc_in
        self.seq_len = seq_len
        self.task = task
        self.patch_embedding = PatchEmbedding(d_model, patch_len, stride, dropout)
        self.text_encoder = TextEncoder(lm_model, d_model, dropout)
        self.encoder = nn.Sequential(
            *[EncoderLayer(d_model, n_heads, d_ff, dropout, activation) for _ in range(e_layers)]
        )
        # patch count after padding ≈ floor((L+pad-patch)/stride)+1 ; +1 text token
        n_patches = int((seq_len + stride - patch_len) / stride + 1)
        self.head_nf = d_model * (n_patches + 1)
        self.flatten = nn.Flatten(start_dim=-2)
        self.dropout = nn.Dropout(dropout)
        self.projection = nn.Linear(self.head_nf * enc_in, num_outputs)

    def forward(
        self,
        x_time: torch.Tensor,
        texts: List[str],
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x_time: [B, L, C]
            texts: list[str] length B
        Returns:
            logits_or_preds: [B, num_outputs]
            embedding: [B, D] fused representation for retrieval / augmentation
        """
        # instance norm
        means = x_time.mean(1, keepdim=True).detach()
        x = x_time - means
        stdev = torch.sqrt(torch.var(x, dim=1, keepdim=True, unbiased=False) + 1e-5)
        x = x / stdev

        x = x.permute(0, 2, 1)  # [B, C, L]
        enc_out, n_vars = self.patch_embedding(x)  # [B*C, N, D]

        emb_text = self.text_encoder.encode(texts, x_time.device)  # [B, D]
        emb_text = emb_text.unsqueeze(1).repeat(1, n_vars, 1)  # [B, C, D]
        emb_text = emb_text.reshape(-1, emb_text.shape[-1]).unsqueeze(1)  # [B*C, 1, D]
        enc_out = torch.cat([enc_out, emb_text], dim=1)

        enc_out = self.encoder(enc_out)
        enc_out = enc_out.reshape(-1, n_vars, enc_out.shape[-2], enc_out.shape[-1])
        enc_out = enc_out.permute(0, 1, 3, 2)  # [B, C, D, N+1]

        flat = self.flatten(enc_out)
        flat = self.dropout(flat)
        emb = flat.reshape(flat.shape[0], -1)
        out = self.projection(emb)
        return out, emb


def build_model_from_config(cfg: dict, enc_in: int, seq_len: int) -> MultiModalEncoder:
    m = cfg.get("model", {})
    task = m.get("task", "classification")
    num_outputs = int(m.get("num_class", 3))
    return MultiModalEncoder(
        enc_in=enc_in,
        seq_len=seq_len,
        num_outputs=num_outputs,
        d_model=int(m.get("d_model", 128)),
        n_heads=int(m.get("n_heads", 4)),
        e_layers=int(m.get("e_layers", 2)),
        d_ff=int(m.get("d_ff", 256)),
        patch_len=int(m.get("patch_len", 4)),
        stride=int(m.get("stride", 2)),
        dropout=float(m.get("dropout", 0.1)),
        activation=m.get("activation", "gelu"),
        lm_model=m.get("lm_model", "minilm6"),
        task=task,
    )
