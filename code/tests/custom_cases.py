"""Participant-made evaluation cases for the rule-based audit.

    python code/tests/custom_cases.py

Each case is a hand-built bundle (the organizer's output shape) with the
expected status and step sequence, covering behavior the 32 samples test
only lightly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from audit.output import validate  # noqa: E402
from audit.rules import audit, load_policy  # noqa: E402


def rec(evidence_id, captured_at, fields, time="", kind="line"):
    return {"evidence_id": evidence_id, "captured_at": captured_at, "origin": "custom",
            "where": "custom", "time": time, "kind": kind, "fields": fields}


def bundle(resources, evidence, audit_at="2026-09-30T00:00:00Z", absences=()):
    return {"case_id": "custom", "audit_at": audit_at, "resources": resources,
            "evidence": evidence, "absences": list(absences), "activity": []}


CASES = [
    {
        "name": "replica drift: deleted in primary, still in failover replica",
        "bundle": bundle(["account_9001"], [
            rec("ev_sql", "2026-09-20T00:00:00Z",
                {"resource_id": "account_9001", "email": "ana@example.com", "full_name": "Ana"}, kind="snapshot"),
        ], absences=[{"evidence_id": "ev_sql", "captured_at": "2026-09-20T00:00:00Z",
                      "table": "customer_profiles_primary", "resource_id": "account_9001"}]),
        "status": "INCOMPLETE",
        "ops": ["REPORT_REMAINING_RECORD", "DELETE_RECORD", "VERIFY_RECORD_ABSENT"],
    },
    {
        "name": "evidence after audit_at is ignored (later restore must not change the answer)",
        "bundle": bundle(["search_9002"], [
            rec("ev_old", "2026-09-01T00:00:00Z", {"resource_id": "search_9002", "result": "miss"},
                time="2026-09-01T00:00:00Z"),
            rec("ev_late", "2026-10-05T00:00:00Z", {"resource_id": "search_9002", "result": "hit"},
                time="2026-10-05T00:00:00Z"),
        ]),
        "status": "COMPLETE",
        "ops": ["VERIFY_RECORD_ABSENT"],
    },
    {
        "name": "tombstone keeps user_id but still exposes email -> redact, not delete",
        "bundle": bundle(["tombstone_9003", "audit_record_9003"], [
            rec("ev_json", "2026-09-10T00:00:00Z", {"resource_id": "tombstone_9003", "subject_reference": "user_9003",
                                                   "email": "kofi@example.com", "full_name": "null"}, kind="snapshot"),
            rec("ev_log", "2026-09-10T00:00:00Z", {"resource_id": "audit_record_9003", "rows": "1",
                                                  "subject_reference": "user_9003"}, time="2026-09-10T00:00:00Z"),
        ]),
        "status": "INCOMPLETE",
        "ops": ["REPORT_EXPOSED_PII", "REDACT_RECORD", "VERIFY_RECORD_PRESENT", "VERIFY_RECORD_REDACTED"],
    },
    {
        "name": "active sync + restorable backup: disable flow and block restore before deleting",
        "bundle": bundle(["data_flow_9004", "backup_9004", "export_9004"], [
            rec("ev1", "2026-09-10T00:00:00Z", {"resource_id": "data_flow_9004", "enabled": "true"}, time="2026-09-10T00:00:00Z"),
            rec("ev1", "2026-09-10T00:00:00Z", {"resource_id": "backup_9004", "restore_allowed": "true"}, time="2026-09-10T00:00:00Z"),
            rec("ev1", "2026-09-10T00:00:00Z", {"resource_id": "export_9004", "owner_email": "lee@example.com"}, kind="snapshot"),
        ]),
        "status": "INCOMPLETE",
        "ops": ["REPORT_REMAINING_RECORD", "REPORT_ACTIVE_DATA_FLOW", "REPORT_RESTORE_RISK",
                "DISABLE_DATA_FLOW", "BLOCK_RESTORE", "DELETE_RECORD",
                "VERIFY_RECORD_ABSENT", "VERIFY_DATA_FLOW_DISABLED", "VERIFY_RESTORE_BLOCKED"],
    },
    {
        "name": "anonymized analytics + retained audit record + absent account -> COMPLETE with cited evidence",
        "bundle": bundle(["account_9005", "analytics_9005", "audit_record_9005"], [
            rec("ev2", "2026-09-10T00:00:00Z", {"resource_id": "account_9005", "http_status": "404"}, time="2026-09-10T00:00:00Z"),
            rec("ev2", "2026-09-10T00:00:00Z", {"resource_id": "analytics_9005", "email": "null", "phone": "null"},
                time="2026-09-10T00:00:00Z", kind="snapshot"),
            rec("ev2", "2026-09-10T00:00:00Z", {"resource_id": "audit_record_9005", "rows": "1"}, time="2026-09-10T00:00:00Z"),
        ]),
        "status": "COMPLETE",
        "ops": ["VERIFY_RECORD_ABSENT", "VERIFY_RECORD_PRESENT", "VERIFY_RECORD_ANONYMIZED"],
    },
]


def main() -> int:
    policy = load_policy()
    failed = 0
    for case in CASES:
        status, steps = audit(case["bundle"], policy)
        ops = [s["operation"] for s in steps]
        errors = validate(status, steps)
        cited = all(s["evidence_id"] for s in steps) if status == "COMPLETE" else True
        ok = status == case["status"] and ops == case["ops"] and not errors and cited
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {case['name']}")
        if not ok:
            print(f"      got {status} {ops} {errors}")
    print(f"{len(CASES) - failed}/{len(CASES)} custom cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
