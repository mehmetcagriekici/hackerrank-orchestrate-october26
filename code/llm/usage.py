"""Per-model call and token counters for evaluation/usage_report.md."""

import json
from collections import defaultdict
from pathlib import Path

USAGE_FILE = Path(__file__).resolve().parents[2] / ".cache" / "usage.json"
CALLS_FILE = USAGE_FILE.with_name("usage_calls.jsonl")  # every call, across runs

_totals: dict[str, dict[str, int]] = defaultdict(lambda: {"calls": 0, "input_tokens": 0,
                                                          "output_tokens": 0, "thinking_tokens": 0})


def record(provider: str, model: str, input_tokens: int, output_tokens: int, thinking_tokens: int = 0) -> None:
    entry = _totals[f"{provider}/{model}"]
    entry["calls"] += 1
    entry["input_tokens"] += input_tokens
    entry["output_tokens"] += output_tokens
    entry["thinking_tokens"] += thinking_tokens
    CALLS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CALLS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"provider": provider, "model": model, "input_tokens": input_tokens,
                            "output_tokens": output_tokens, "thinking_tokens": thinking_tokens}) + "\n")


def snapshot() -> dict:
    return {name: dict(values) for name, values in sorted(_totals.items())}


def save() -> None:
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    USAGE_FILE.write_text(json.dumps(snapshot(), indent=2), encoding="utf-8")
