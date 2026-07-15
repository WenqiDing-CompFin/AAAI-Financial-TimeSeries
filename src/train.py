"""Training entrypoint for the multi-modal encoder."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data import FinanceEventDataset, MinuteForecastDataset, collate_batch
from src.models import build_model_from_config
from src.utils import classification_metrics, load_config, regression_metrics, set_seed
from src.utils.io import ensure_dir, save_json
from src.utils.metrics import format_metrics


def build_loaders(cfg: dict):
    data_cfg = cfg["data"]
    mode = data_cfg.get("mode", "daily_event")
    root = Path(data_cfg.get("sample_root", "data/sample"))
    train_kwargs = dict(
        train_ratio=float(data_cfg.get("train_ratio", 0.6)),
        val_ratio=float(data_cfg.get("val_ratio", 0.2)),
    )
    bs = int(cfg["train"].get("batch_size", 32))
    nw = int(cfg["train"].get("num_workers", 0))

    if mode == "minute_forecast":
        data_root = root / "minute"
        ds_train = MinuteForecastDataset(data_root, "train", **train_kwargs)
        ds_val = MinuteForecastDataset(data_root, "val", **train_kwargs)
        ds_test = MinuteForecastDataset(data_root, "test", **train_kwargs)
        task = "regression"
    else:
        data_root = root / "finance_daily"
        ds_train = FinanceEventDataset(data_root, "train", **train_kwargs)
        ds_val = FinanceEventDataset(data_root, "val", **train_kwargs)
        ds_test = FinanceEventDataset(data_root, "test", **train_kwargs)
        task = "classification"

    loaders = {
        "train": DataLoader(ds_train, batch_size=bs, shuffle=True, num_workers=nw, collate_fn=collate_batch),
        "val": DataLoader(ds_val, batch_size=bs, shuffle=False, num_workers=nw, collate_fn=collate_batch),
        "test": DataLoader(ds_test, batch_size=bs, shuffle=False, num_workers=nw, collate_fn=collate_batch),
    }
    return loaders, ds_train, task


@torch.no_grad()
def evaluate(model, loader, device, task: str):
    model.eval()
    ys, preds = [], []
    total_loss = 0.0
    criterion = nn.CrossEntropyLoss() if task == "classification" else nn.MSELoss()
    for batch in loader:
        x = batch["x_time"].to(device)
        y = batch["y"].to(device)
        out, _ = model(x, batch["text"])
        loss = criterion(out, y)
        total_loss += float(loss.item()) * x.size(0)
        if task == "classification":
            pred = out.argmax(dim=-1)
            ys.append(y.cpu())
            preds.append(pred.cpu())
        else:
            ys.append(y.cpu())
            preds.append(out.cpu())
    import numpy as np

    y_true = torch.cat(ys).numpy()
    y_pred = torch.cat(preds).numpy()
    metrics = (
        classification_metrics(y_true, y_pred)
        if task == "classification"
        else regression_metrics(y_true.reshape(-1), y_pred.reshape(-1))
    )
    metrics["loss"] = total_loss / max(len(loader.dataset), 1)
    return metrics


def train(cfg: dict) -> dict:
    set_seed(int(cfg.get("experiment", {}).get("seed", 42)))
    loaders, ds_train, task = build_loaders(cfg)
    device = torch.device(
        f"cuda:{cfg['train'].get('gpu', 0)}"
        if cfg["train"].get("use_gpu", False) and torch.cuda.is_available()
        else "cpu"
    )

    model = build_model_from_config(
        cfg,
        enc_in=ds_train.num_feature,
        seq_len=ds_train.max_seq_len,
    ).to(device)

    # Align output size for regression
    if task == "regression":
        horizon = getattr(ds_train, "horizon", cfg["data"].get("pred_len", 5))
        if model.projection.out_features != horizon:
            model.projection = nn.Linear(model.projection.in_features, horizon).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=float(cfg["train"]["learning_rate"]))
    criterion = nn.CrossEntropyLoss() if task == "classification" else nn.MSELoss()

    out_dir = ensure_dir(Path(cfg["experiment"]["output_dir"]) / cfg["experiment"]["name"])
    ckpt_dir = ensure_dir(out_dir / "checkpoints")
    best_val = float("inf")
    patience = int(cfg["train"].get("patience", 5))
    bad_epochs = 0
    history = []

    epochs = int(cfg["train"].get("epochs", 20))
    for epoch in range(1, epochs + 1):
        model.train()
        running = 0.0
        pbar = tqdm(loaders["train"], desc=f"epoch {epoch}/{epochs}", leave=False)
        for batch in pbar:
            x = batch["x_time"].to(device)
            y = batch["y"].to(device)
            optimizer.zero_grad(set_to_none=True)
            out, _ = model(x, batch["text"])
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            running += float(loss.item()) * x.size(0)
            pbar.set_postfix(loss=float(loss.item()))

        train_loss = running / max(len(loaders["train"].dataset), 1)
        val_metrics = evaluate(model, loaders["val"], device, task)
        row = {"epoch": epoch, "train_loss": train_loss, **{f"val_{k}": v for k, v in val_metrics.items()}}
        history.append(row)
        print(f"[epoch {epoch}] train_loss={train_loss:.4f} | val {format_metrics(val_metrics)}")

        if val_metrics["loss"] < best_val:
            best_val = val_metrics["loss"]
            bad_epochs = 0
            torch.save(
                {"model": model.state_dict(), "cfg": cfg, "task": task},
                ckpt_dir / "best.pt",
            )
        else:
            bad_epochs += 1
            if bad_epochs >= patience:
                print(f"Early stopping at epoch {epoch}")
                break

    # Test with best checkpoint
    ckpt = torch.load(ckpt_dir / "best.pt", map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model"])
    test_metrics = evaluate(model, loaders["test"], device, task)
    print(f"[test] {format_metrics(test_metrics)}")

    save_json({"history": history, "test": test_metrics}, out_dir / "metrics" / "run.json")
    # also mirror under results/metrics
    ensure_dir(Path("results/metrics"))
    save_json({"history": history, "test": test_metrics}, Path("results/metrics") / f"{cfg['experiment']['name']}.json")
    return test_metrics


def parse_args():
    p = argparse.ArgumentParser(description="Train TimeCAP multi-modal encoder on financial data")
    p.add_argument("--config", type=str, default="configs/default.yaml")
    return p.parse_args()


def main():
    args = parse_args()
    cfg = load_config(args.config)
    train(cfg)


if __name__ == "__main__":
    main()
