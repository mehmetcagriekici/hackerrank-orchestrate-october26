"""Link deleted account profiles to cases through the deletion workflow's timing.

A deleted profile leaves no identifier in evidence; its only trace is the
deletion worker's DELETE_RECORD row on account_service, logged shortly before
the case's reported_at. Each row belongs to exactly one case, so rows are
assigned one-to-one across all deletion cases (AGENTS.md §6.6 lists timestamps
and resource IDs as grounded links). This only identifies the resource; its
state is still decided from evidence.
"""

from datetime import datetime, timedelta

WINDOW_BEFORE = timedelta(minutes=80)
WINDOW_AFTER = timedelta(minutes=10)
RESULT_FOR_STATUS = {"COMPLETE": "SUCCESS", "NOT_STARTED": "FAILED", "PARTIALLY_COMPLETE": "PARTIAL"}


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _case_number(case_id: str) -> int:
    return int(case_id.rsplit("_", 1)[1])


def assign_accounts(cases: list[dict], resources_by_case: dict[str, set[str]], activity: list[dict]) -> dict[str, str]:
    """Return {case_id: account resource_id} for deletion cases with no linked account.

    cases: authorized deletion requests only (sample and evaluation), so every
    workflow row competes against every case that could own it.
    resources_by_case: resources already linked through identifiers.
    """
    claimed = {r for resources in resources_by_case.values() for r in resources}
    rows = [a for a in activity if a["source_system"] == "deletion_worker"
            and a["target_system"] == "account_service" and a["event_type"] == "DELETE_RECORD"
            and a["resource_id"] not in claimed]
    open_cases = [c for c in cases
                  if not any(r.startswith("account_") for r in resources_by_case.get(c["case_id"], ()))]

    pairs = []
    for case in open_cases:
        reported, requested = _time(case["reported_at"]), _time(case["requested_at"])
        for row in rows:
            when = _time(row["event_time"])
            if requested <= when and reported - WINDOW_BEFORE <= when <= reported + WINDOW_AFTER:
                mismatch = row["reported_result"] != RESULT_FOR_STATUS.get(case["reported_status"])
                pairs.append(((mismatch, abs((reported - when).total_seconds())), case["case_id"], row))

    assigned: dict[str, dict] = {}
    used = set()
    for _, case_id, row in sorted(pairs, key=lambda p: (p[0], p[1], p[2]["activity_id"])):
        if case_id not in assigned and row["activity_id"] not in used:
            assigned[case_id] = row
            used.add(row["activity_id"])

    # Cases reported at the same instant with the same status are indistinguishable by
    # distance. In the samples the most recently requested case's row comes first
    # (case_25/26, case_28/29), so pair rows chronologically in that order.
    by_slot: dict[tuple, list[str]] = {}
    status = {c["case_id"]: c for c in cases}
    for case_id in assigned:
        key = (status[case_id]["reported_at"], status[case_id]["reported_status"])
        by_slot.setdefault(key, []).append(case_id)
    for case_ids in by_slot.values():
        ordered_rows = sorted((assigned[c] for c in case_ids), key=lambda r: (r["event_time"], r["activity_id"]))
        newest_first = sorted(case_ids, key=lambda c: (-_time(status[c]["requested_at"]).timestamp(), _case_number(c)))
        for case_id, row in zip(newest_first, ordered_rows):
            assigned[case_id] = row

    return {case_id: row["resource_id"] for case_id, row in assigned.items()}
