"""Score a predicted output against sample_output.csv.

    python code/tests/evaluate.py [predicted.csv]
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ("phase", "system_id", "resource_id", "operation", "state", "evidence_id")


def _load(path: Path) -> dict[str, tuple[str, list[dict]]]:
    with open(path, newline="", encoding="utf-8") as f:
        return {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}


def _key(step: dict) -> tuple:
    return tuple(step[k] for k in FIELDS)


def score(pred: dict, gold: dict) -> dict:
    status = sum(pred.get(c, ("",))[0] == g[0] for c, g in gold.items())
    exact_seq = sum(pred.get(c, ("", []))[1] and [_key(s) for s in pred[c][1]] == [_key(s) for s in g[1]]
                    or (not g[1] and not pred.get(c, ("", [None]))[1]) for c, g in gold.items())
    tp = fp = fn = 0
    field_hits = field_total = 0
    for case_id, (_, gold_steps) in gold.items():
        pred_steps = pred.get(case_id, ("", []))[1]
        gold_keys = [_key(s) for s in gold_steps]
        pred_keys = [_key(s) for s in pred_steps]
        matched = sum(min(gold_keys.count(k), pred_keys.count(k)) for k in set(gold_keys))
        tp += matched
        fp += len(pred_keys) - matched
        fn += len(gold_keys) - matched
        for i, g in enumerate(gold_steps):
            p = pred_steps[i] if i < len(pred_steps) else {}
            field_hits += sum(p.get(k) == g[k] for k in FIELDS)
            field_total += len(FIELDS)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "cases": len(gold),
        "status_accuracy": status / len(gold),
        "step_precision": precision,
        "step_recall": recall,
        "step_f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "field_accuracy_by_position": field_hits / field_total if field_total else 0.0,
        "exact_sequence_accuracy": exact_seq / len(gold),
    }


if __name__ == "__main__":
    predicted = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".cache" / "sample_output.csv"
    gold = _load(ROOT / "dataset" / "sample_output.csv")
    pred = _load(predicted)
    for key, value in score(pred, gold).items():
        print(f"{key:28} {value:.3f}" if isinstance(value, float) else f"{key:28} {value}")
    for case_id, (gold_status, gold_steps) in gold.items():
        status, steps = pred.get(case_id, ("MISSING", []))
        if status != gold_status:
            print(f"  status {case_id}: predicted {status}, expected {gold_status}")
