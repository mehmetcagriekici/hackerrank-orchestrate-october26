"""Common shape every parser emits.

A record is one row, log line, or JSON object that carries facts:
    {"where": <table / line / json path>, "time": <ISO time or "">, "fields": {key: str}}
"""

import re
from dataclasses import dataclass, field

ISO_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
RESOURCE_ID = re.compile(r"\b[a-z]+(?:_[a-z]+)*_\d+\b")


@dataclass
class ParsedFile:
    meta: dict = field(default_factory=dict)
    records: list[dict] = field(default_factory=list)
    # SQL only: table name -> resource_ids present, used to prove absence.
    presence: dict[str, set[str]] = field(default_factory=dict)


def make_record(where: str, fields: dict, time: str = "", kind: str = "line") -> dict:
    """kind is "snapshot" for SQL rows / JSON objects (existence = present) or "line" for logs/text."""
    clean = {str(k): "" if v is None else str(v) for k, v in fields.items()}
    return {"where": where, "time": time, "kind": kind, "fields": clean}


def first_time(*values: str) -> str:
    for value in values:
        match = ISO_TIME.search(value or "")
        if match:
            return match.group(0)
    return ""
