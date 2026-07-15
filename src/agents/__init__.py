"""LLM agents: contextualizer (A_C) and predictor (A_P)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

from src.prompts import (
    FINANCE_CONTEXTUALIZE_SYSTEM,
    FINANCE_CONTEXTUALIZE_USER,
    FINANCE_PREDICT_SYSTEM,
    FINANCE_PREDICT_USER,
    INDICATOR_DISPLAY,
    LABEL_MAP_DAILY,
    MINUTE_CONTEXTUALIZE_SYSTEM,
    MINUTE_CONTEXTUALIZE_USER,
    MINUTE_PREDICT_SYSTEM,
    MINUTE_PREDICT_USER,
)


def _series_to_prompt(values) -> str:
    return " | ".join(f"{float(v):.4f}" for v in values)


@dataclass
class AgentConfig:
    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    max_tokens: int = 400
    api_key: Optional[str] = None


class LLMClient:
    """Thin wrapper around the OpenAI chat API with a dry-run fallback."""

    def __init__(self, cfg: AgentConfig):
        self.cfg = cfg
        self.api_key = cfg.api_key or os.getenv("OPENAI_API_KEY")
        self._client = None
        if self.api_key:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=self.api_key)
            except Exception:
                self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def complete(self, system: str, user: str) -> str:
        if not self._client:
            return (
                "[DRY-RUN] LLM API key not configured. "
                "Set OPENAI_API_KEY to enable live contextualization/prediction."
            )
        response = self._client.chat.completions.create(
            model=self.cfg.model,
            temperature=self.cfg.temperature,
            max_tokens=self.cfg.max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content.strip()


class ContextualizerAgent:
    """A_C: turn raw financial time series into a textual context summary."""

    def __init__(self, client: LLMClient, mode: str = "daily_event"):
        self.client = client
        self.mode = mode

    def run(self, window: dict[str, Any], meta: Optional[dict[str, Any]] = None) -> str:
        meta = meta or {}
        if self.mode == "minute_forecast":
            user = MINUTE_CONTEXTUALIZE_USER.format(
                window_size=meta.get("window_size", len(next(iter(window.values())))),
                symbol=meta.get("symbol", "SPY"),
                open=_series_to_prompt(window["open"]),
                high=_series_to_prompt(window["high"]),
                low=_series_to_prompt(window["low"]),
                close=_series_to_prompt(window["close"]),
                volume=_series_to_prompt(window["volume"]),
            )
            return self.client.complete(MINUTE_CONTEXTUALIZE_SYSTEM, user)

        user = FINANCE_CONTEXTUALIZE_USER.format(
            window_size=meta.get("window_size", 20),
            sp500=_series_to_prompt(window["sp500"]),
            vix=_series_to_prompt(window["vix"]),
            nikkei=_series_to_prompt(window["nikkei"]),
            ftse=_series_to_prompt(window["ftse"]),
            gold=_series_to_prompt(window["gold"]),
            crude_oil=_series_to_prompt(window["crude_oil"]),
            eur_usd=_series_to_prompt(window["eur_usd"]),
            usd_jpy=_series_to_prompt(window["usd_jpy"]),
            usd_cny=_series_to_prompt(window["usd_cny"]),
        )
        return self.client.complete(FINANCE_CONTEXTUALIZE_SYSTEM, user)


class PredictorAgent:
    """A_P: predict event labels from contextual summaries (+ optional in-context examples)."""

    def __init__(self, client: LLMClient, mode: str = "daily_event"):
        self.client = client
        self.mode = mode

    def _format_examples(self, examples: Optional[list[dict[str, str]]]) -> str:
        if not examples:
            return ""
        blocks = []
        for i, ex in enumerate(examples, 1):
            blocks.append(
                f"Example {i}:\nSummary: {ex['summary']}\nLabel: {ex['label']}"
            )
        return "In-context examples:\n" + "\n\n".join(blocks)

    def run(
        self,
        summary: str,
        indicator: str = "sp500",
        examples: Optional[list[dict[str, str]]] = None,
        meta: Optional[dict[str, Any]] = None,
    ) -> str:
        meta = meta or {}
        examples_text = self._format_examples(examples)
        if self.mode == "minute_forecast":
            user = MINUTE_PREDICT_USER.format(
                symbol=meta.get("symbol", "SPY"),
                horizon=meta.get("horizon", 5),
                summary=summary,
                examples=examples_text,
            )
            return self.client.complete(MINUTE_PREDICT_SYSTEM, user)

        user = FINANCE_PREDICT_USER.format(
            indicator_name=INDICATOR_DISPLAY.get(indicator, indicator),
            summary=summary,
            examples=examples_text,
        )
        return self.client.complete(FINANCE_PREDICT_SYSTEM, user)

    def parse_label(self, text: str) -> int:
        token = text.strip().lower().split()[0].strip(".,:;\"'")
        mapping = LABEL_MAP_DAILY if self.mode != "minute_forecast" else {
            "down": 0,
            "flat": 1,
            "up": 2,
            "decrease": 0,
            "neutral": 1,
            "increase": 2,
        }
        return mapping.get(token, 1)
