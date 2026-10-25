"""Ghost Data Still Exists: deletion-audit pipeline.

    python code/main.py                 # 518 evaluation requests -> output.csv
    python code/main.py --split sample  # 32 public samples -> .cache/sample_output.csv
"""

import argparse
import csv
import os
from pathlib import Path

from audit.output import ROOT, validate, write_output
from audit.rules import audit, load_policy
from gate.authorize import authorize
from gate.link_builder import load_identity_data, build_links
from gate.sanity import check_request
from llm import usage
from llm.gemini_client import GeminiClient
from organizer.account_linker import assign_accounts
from organizer.organizer import Organizer

INPUTS = {"eval": "deletion_requests.csv", "sample": "sample_deletion_requests.csv"}
GATE_MODEL = os.environ.get("GATE_MODEL", "gemini-3.5-flash-lite")


def link_accounts(organizer: Organizer, identities: dict, history: dict) -> dict[str, str]:
    """Assign deleted account profiles across ALL authorized requests (sample + eval),
    since every deletion-worker row competes for exactly one owner."""
    everyone = []
    for name in INPUTS.values():
        with open(ROOT / "dataset" / name, newline="", encoding="utf-8") as f:
            everyone.extend(r for r in csv.DictReader(f) if not check_request(r))
    decisions = authorize([r["request_text"] for r in everyone], GeminiClient(GATE_MODEL))
    everyone = [r for r in everyone if decisions[r["request_text"]]]
    linked = {}
    for row in everyone:
        links = build_links(row["email"], row["audit_at"], identities, history)
        bundle = organizer.build_bundle(row, links) if links else None
        linked[row["case_id"]] = set(bundle["resources"]) if bundle else set()
    return assign_accounts(everyone, linked, organizer.activity)


def run(split: str) -> Path:
    with open(ROOT / "dataset" / INPUTS[split], newline="", encoding="utf-8") as f:
        requests = list(csv.DictReader(f))

    results: dict[str, tuple[str, list[dict]]] = {}
    sane = []
    for row in requests:
        if check_request(row):
            results[row["case_id"]] = ("NOT_APPLICABLE", [])
        else:
            sane.append(row)

    decisions = authorize([r["request_text"] for r in sane], GeminiClient(GATE_MODEL))
    valid = [r for r in sane if decisions[r["request_text"]]]
    for row in sane:
        if not decisions[row["request_text"]]:
            results[row["case_id"]] = ("NOT_APPLICABLE", [])

    identities, history = load_identity_data()
    organizer = Organizer()
    policy = load_policy()
    accounts = link_accounts(organizer, identities, history)
    for row in valid:
        links = build_links(row["email"], row["audit_at"], identities, history)
        extra = {accounts[row["case_id"]]} if row["case_id"] in accounts else set()
        bundle = organizer.build_bundle(row, links, extra) if links else None
        status, steps = audit(bundle, policy)
        errors = validate(status, steps)
        if errors:
            raise ValueError(f"{row['case_id']}: {errors}")
        results[row["case_id"]] = (status, steps)

    out = ROOT / "output.csv" if split == "eval" else ROOT / ".cache" / "sample_output.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_output(results, out)
    usage.save()
    counts = {s: sum(1 for v in results.values() if v[0] == s) for s in ("COMPLETE", "INCOMPLETE", "NOT_APPLICABLE")}
    print(f"{split}: {len(results)} rows -> {out} {counts}")
    print("usage:", usage.snapshot())
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=sorted(INPUTS), default="eval")
    run(parser.parse_args().split)
