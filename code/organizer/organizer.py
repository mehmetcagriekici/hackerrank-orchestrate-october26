"""Organizer: turn evidence files into one audit bundle per case.

Parses every evidence file once, then for each case keeps only what was
captured at or before audit_at and links to the person. It never decides
a case's status.
"""

import csv
import re
from pathlib import Path

from helpers.normalize_text import normalize
from organizer.parsers import parse_file

DATASET_DIR = Path(__file__).resolve().parents[2] / "dataset"


def _read_csv(name: str) -> list[dict]:
    with open(DATASET_DIR / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _prefix(resource_id: str) -> str:
    return resource_id.rsplit("_", 1)[0]


TOKEN = re.compile(r"[\w.+@-]+")
EMPTY = {"", "null", "none", "n/a", "-"}


def _candidates(value: str) -> set[str]:
    """Whole value plus each token, lowercased, plus a phone form when it looks like one."""
    low = value.strip().lower()
    found = {low} | set(TOKEN.findall(low))
    digits = re.sub(r"\D", "", low)
    if len(digits) >= 8 and not re.search(r"[a-z]", low.replace("ext", "")):
        found.add(normalize("phone", low))
    return found - EMPTY


def record_matches(fields: dict, link_values: set[str]) -> bool:
    """True when a record's fields mention any of the person's link values."""
    return any(_candidates(value) & link_values for value in fields.values() if value)


class Organizer:
    def __init__(self) -> None:
        self.manifest = _read_csv("evidence_files.csv")
        self.parsed = {row["file_id"]: parse_file(DATASET_DIR / row["file_path"]) for row in self.manifest}
        self.activity = _read_csv("system_activity.csv")

    def build_bundle(self, case: dict, links: dict[str, set[str]], extra_resources: set[str] = frozenset()) -> dict | None:
        """Return the case's audit bundle, or None when no resource links to it.

        extra_resources: resources linked by other means (account_linker's workflow timing).
        """
        audit_at = case["audit_at"]
        link_values = set().union(*links.values())
        in_time = [row for row in self.manifest if row["captured_at"] <= audit_at]

        # Pass 1: records that name the person, and log lines sharing their trace;
        # their resource_ids join the links.
        resources: set[str] = set()
        for row in in_time:
            records = self.parsed[row["file_id"]].records
            hits = [r for r in records if record_matches(r["fields"], link_values)]
            traces = {r["fields"].get("trace") for r in hits} - {"", None}
            for record in records:
                if record in hits or record["fields"].get("trace") in traces:
                    resources.add(record["fields"].get("resource_id", ""))
        resources.discard("")
        resources |= set(extra_resources)
        if not resources:
            return None

        # Pass 2: every in-time record about those resources, plus same-trace lines.
        evidence = []
        for row in in_time:
            records = self.parsed[row["file_id"]].records
            traces = {r["fields"].get("trace") for r in records
                      if r["fields"].get("resource_id") in resources} - {"", None}
            for record in records:
                fields = record["fields"]
                if fields.get("resource_id") in resources or fields.get("trace") in traces:
                    evidence.append({"evidence_id": row["file_id"], "captured_at": row["captured_at"],
                                     "origin": row["origin"], **record})

        # SQL snapshots: a linked resource missing from a table of its kind.
        absences = []
        for row in in_time:
            for table, present in self.parsed[row["file_id"]].presence.items():
                kinds = {_prefix(r) for r in present}
                for resource in sorted(resources):
                    if _prefix(resource) in kinds and resource not in present:
                        absences.append({"evidence_id": row["file_id"], "captured_at": row["captured_at"],
                                         "table": table, "resource_id": resource})

        activity = [a for a in self.activity
                    if a["event_time"] <= audit_at and a["resource_id"] in resources]

        return {
            "case_id": case["case_id"],
            "requested_at": case["requested_at"],
            "reported_status": case["reported_status"],
            "reported_at": case["reported_at"],
            "audit_at": audit_at,
            "links": {key: sorted(values) for key, values in links.items()},
            "resources": sorted(resources),
            "evidence": evidence,
            "absences": absences,
            "activity": activity,
        }
