"""Link builder: expand a request email into every identifier for that person.

Output is key/value links, keyed by the audit-log field names plus user_id
and name, each holding a set of normalized values.
"""

import csv
from collections import defaultdict
from pathlib import Path

from helpers.normalize_text import normalize as normalize_text

DATASET_DIR = Path(__file__).resolve().parents[2] / "dataset"
LINK_KEYS = ("email", "email_hash", "phone", "name")


def _read_csv(name: str) -> list[dict]:
    with open(DATASET_DIR / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_identity_data() -> tuple[dict[str, dict], dict[str, list[dict]]]:
    """Return (current snapshot by user_id, audit-log rows by user_id)."""
    identities = {row["user_id"]: row for row in _read_csv("user_identities.csv")}
    history = defaultdict(list)
    for row in _read_csv("user_audit_log.csv"):
        history[row["user_id"]].append(row)
    return identities, history


def find_user_id(email: str, identities: dict, history: dict) -> str | None:
    """Resolve a current or historical email to its user_id."""
    target = normalize_text("email", email)
    for user_id, row in identities.items():
        if normalize_text("email", row["email"]) == target:
            return user_id
    for user_id, rows in history.items():
        for row in rows:
            if row["field_name"] == "email" and target in (
                normalize_text("email", row["old_value"]),
                normalize_text("email", row["new_value"]),
            ):
                return user_id
    return None


def history_rows_in_scope(rows: list[dict], audit_at: str) -> list[dict]:
    """Keep only identifier changes known at audit time (AGENTS.md §6.2)."""
    return [row for row in rows if row["event_time"] <= audit_at]


def build_links(email: str, audit_at: str, identities: dict, history: dict) -> dict[str, set[str]] | None:
    """Return {key: {values}} for one case, or None if the email is unknown."""
    user_id = find_user_id(email, identities, history)
    if user_id is None:
        return None

    links = {"user_id": {user_id}, **{key: set() for key in LINK_KEYS}}
    current = identities[user_id]
    for key in LINK_KEYS:
        links[key].add(normalize_text(key, current[key]))
    for row in history_rows_in_scope(history[user_id], audit_at):
        for value in (row["old_value"], row["new_value"]):
            links[row["field_name"]].add(normalize_text(row["field_name"], value))

    return {key: {v for v in values if v} for key, values in links.items()}
