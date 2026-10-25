"""Structural sanity checks on a request row. Any failure makes the case NOT_APPLICABLE."""

from helpers.normalize_text import normalize

ISO_LENGTH = len("2026-01-01T00:00:00Z")


def _is_iso(value: str) -> bool:
    return len(value) == ISO_LENGTH and value[4] == "-" and value[10] == "T" and value.endswith("Z")


def check_request(row: dict) -> list[str]:
    """Return the failed checks for one request (empty list = passes)."""
    failures = []
    if not row.get("case_id", "").strip():
        failures.append("missing case_id")
    if "@" not in normalize("email", row.get("email", "")):
        failures.append("invalid email")
    if not row.get("request_text", "").strip():
        failures.append("empty request_text")

    times = {key: row.get(key, "") for key in ("requested_at", "reported_at", "audit_at")}
    bad = [key for key, value in times.items() if not _is_iso(value)]
    failures.extend(f"invalid {key}" for key in bad)
    if not bad:
        if not times["requested_at"] <= times["audit_at"]:
            failures.append("requested_at after audit_at")
        if not times["requested_at"] <= times["reported_at"] <= times["audit_at"]:
            failures.append("reported_at outside requested_at..audit_at")
    return failures
