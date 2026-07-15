#!/usr/bin/env python3
"""
Run TimeCP / TimeCAP LLM agents on a saved dataset window.

Examples:
  python scripts/run_agents.py --mode contextualize --index 0
  python scripts/run_agents.py --mode predict --index 0 --summary-file /tmp/sum.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents import AgentConfig, ContextualizerAgent, LLMClient, PredictorAgent
from src.utils import load_config


def load_window(npz_path: Path, index: int, channels: list[str]) -> dict:
    blob = np.load(npz_path, allow_pickle=True)
    series = blob["time_series"]
    indices = blob["indices"]
    window_size = int(blob["window_size"][0])
    start = int(indices[index])
    window = series[start : start + window_size]
    return {ch: window[:, i] for i, ch in enumerate(channels)}


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--mode", choices=["contextualize", "predict", "both"], default="both")
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--data-root", default="data/sample/finance_daily")
    parser.add_argument("--summary-file", default=None)
    args = parser.parse_args()

    cfg = load_config(args.config)
    agent_cfg = AgentConfig(
        model=cfg.get("agents", {}).get("model", "gpt-4o-mini"),
        temperature=float(cfg.get("agents", {}).get("temperature", 0.2)),
        max_tokens=int(cfg.get("agents", {}).get("max_tokens", 400)),
    )
    client = LLMClient(agent_cfg)
    data_mode = cfg["data"].get("mode", "daily_event")
    channels = cfg["data"].get("channels")

    npz = Path(args.data_root) / "dataset.npz"
    window = load_window(npz, args.index, channels)
    meta = {
        "window_size": cfg["data"].get("window_size", 20),
        "symbol": cfg.get("forecast", {}).get("symbol", "SPY"),
        "horizon": cfg.get("forecast", {}).get("horizon", 5),
    }

    summary = None
    if args.mode in {"contextualize", "both"}:
        ac = ContextualizerAgent(client, mode=data_mode)
        summary = ac.run(window, meta=meta)
        print("=== Contextual summary ===")
        print(summary)

    if args.mode in {"predict", "both"}:
        if summary is None:
            if args.summary_file:
                summary = Path(args.summary_file).read_text(encoding="utf-8")
            else:
                summaries = (Path(args.data_root) / "summaries.txt").read_text(encoding="utf-8").split("\n-----\n")
                summary = summaries[args.index]
        ap = PredictorAgent(client, mode=data_mode)
        pred = ap.run(summary, indicator=cfg["data"].get("target_indicator", "sp500"), meta=meta)
        print("=== Prediction ===")
        print(pred)
        print("parsed_label=", ap.parse_label(pred))

    if not client.available:
        print("\nNote: running in dry-run mode (OPENAI_API_KEY not set).")


if __name__ == "__main__":
    main()
