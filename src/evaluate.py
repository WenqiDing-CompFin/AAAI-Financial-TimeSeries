"""Evaluation / inference helpers."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data import FinanceEventDataset, MinuteForecastDataset, collate_batch
from src.models import build_model_from_config
from src.train import evaluate
from src.utils import load_config, set_seed
from src.utils.io import ensure_dir, save_json
from src.utils.metrics import format_metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--checkpoint", default=None, help="Path to best.pt; defaults to results/<exp>/checkpoints/best.pt")
    parser.add_argument("--split", default="test", choices=["train", "val", "test"])
    args = parser.parse_args()

    cfg = load_config(args.config)
    set_seed(int(cfg.get("experiment", {}).get("seed", 42)))

    mode = cfg["data"].get("mode", "daily_event")
    root = Path(cfg["data"].get("sample_root", "data/sample"))
    if mode == "minute_forecast":
        ds = MinuteForecastDataset(root / "minute", args.split)
        task = "regression"
    else:
        ds = FinanceEventDataset(root / "finance_daily", args.split)
        task = "classification"

    loader = DataLoader(
        ds,
        batch_size=int(cfg["train"].get("batch_size", 32)),
        shuffle=False,
        collate_fn=collate_batch,
    )
    device = torch.device("cuda" if torch.cuda.is_available() and cfg["train"].get("use_gpu") else "cpu")
    model = build_model_from_config(cfg, enc_in=ds.num_feature, seq_len=ds.max_seq_len).to(device)

    ckpt_path = Path(
        args.checkpoint
        or Path(cfg["experiment"]["output_dir"]) / cfg["experiment"]["name"] / "checkpoints" / "best.pt"
    )
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}. Train first via src/train.py")
    blob = torch.load(ckpt_path, map_location=device, weights_only=False)
    # handle regression head size mismatch gracefully
    state = blob["model"]
    if "projection.weight" in state and state["projection.weight"].shape != model.projection.weight.shape:
        model.projection = torch.nn.Linear(
            state["projection.weight"].shape[1],
            state["projection.weight"].shape[0],
        ).to(device)
    model.load_state_dict(state)

    metrics = evaluate(model, loader, device, task)
    print(f"[{args.split}] {format_metrics(metrics)}")
    out = ensure_dir(Path("results/metrics"))
    save_json(metrics, out / f"eval_{cfg['experiment']['name']}_{args.split}.json")


if __name__ == "__main__":
    main()
