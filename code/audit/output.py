"""Validate steps against the output contract and write output.csv."""

import csv
import json
from pathlib import Path

from audit.rules import OP_STATE, ORDER

ROOT = Path(__file__).resolve().parents[2]
STATUSES = {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}
FIELDS = ("step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id")
PHASES = ["FINDING", "REMEDIATION", "VERIFICATION"]


def validate(status: str, steps: list[dict]) -> list[str]:
    errors = []
    if status not in STATUSES:
        errors.append(f"bad status {status}")
    if status == "NOT_APPLICABLE" and steps:
        errors.append("NOT_APPLICABLE must have []")
    last_phase = 0
    for i, step in enumerate(steps, start=1):
        if tuple(step) != FIELDS:
            errors.append(f"step {i}: fields {list(step)}")
        if step["step_no"] != i:
            errors.append(f"step {i}: step_no {step['step_no']}")
        phase = PHASES.index(step["phase"])
        if phase < last_phase:
            errors.append(f"step {i}: phase out of order")
        last_phase = phase
        if step["operation"] not in ORDER[step["phase"]] or OP_STATE[step["operation"]] != step["state"]:
            errors.append(f"step {i}: bad operation/state")
        if step["phase"] != "FINDING" and status == "INCOMPLETE" and step["evidence_id"]:
            errors.append(f"step {i}: future step cites evidence")
    return errors


def write_output(rows: dict[str, tuple[str, list[dict]]], path: Path = ROOT / "output.csv") -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        for case_id in sorted(rows, key=lambda c: (len(c), c)):
            status, steps = rows[case_id]
            writer.writerow([case_id, status, json.dumps(steps, ensure_ascii=False, separators=(",", ":"))])
