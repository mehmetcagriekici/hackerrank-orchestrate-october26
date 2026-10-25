"""Rule-based audit: bundle facts + deletion_rules.csv -> status and ordered steps.

For each linked resource, the latest observation at or before audit_at decides
its state. The policy action for its data category decides whether that state
is compliant. Any violation makes the case INCOMPLETE.
"""

import csv
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parents[2] / "dataset"

# resource prefix -> (system_id, default data category)
KINDS = {
    "account": ("account_service", "USER_PROFILE"),
    "search": ("search_service", "SEARCH_INDEX_ENTRY"),
    "support": ("support_platform", "SUPPORT_MESSAGE"),
    "analytics": ("analytics_platform", "ANALYTICS_PROFILE"),
    "export": ("export_service", "USER_EXPORT"),
    "data_flow": ("integration_service", "DATA_FLOW"),
    "backup": ("backup_service", "BACKUP_ARCHIVE"),
    "tombstone": ("identity_service", "ACCOUNT_TOMBSTONE"),
    "audit_record": ("security_service", "SECURITY_AUDIT_LOG"),
    "legal": ("legal_service", "LEGAL_HOLD_RECORD"),
    "marketing": ("marketing_service", "MARKETING_PROFILE"),
    "cache": ("cache_service", "CACHE_ENTRY"),
}

EXPLICIT = {
    "found": "PRESENT", "hit": "PRESENT", "not_found": "ABSENT", "miss": "ABSENT",
    "identifiable": "EXPOSED", "anonymized": "CLEAN", "redacted": "CLEAN",
    "active": "ACTIVE", "disabled": "DISABLED", "blocked": "BLOCKED",
}
PII_KEYS = ("email", "phone", "email_hash", "full_name", "name", "customer_email",
            "requester_email", "requester_name", "requester_phone", "owner_email", "display_name")
NULLS = {"", "null", "none", "0", "false"}
TRUE = {"true", "1", "yes"}

# (finding, remediation, verification) per violation; state of each op.
FINDING = {"REMAINING": "REPORT_REMAINING_RECORD", "EXPOSED": "REPORT_EXPOSED_PII",
           "FLOW": "REPORT_ACTIVE_DATA_FLOW", "RESTORE": "REPORT_RESTORE_RISK"}
OP_STATE = {
    "REPORT_REMAINING_RECORD": "PRESENT", "REPORT_EXPOSED_PII": "PRESENT",
    "REPORT_ACTIVE_DATA_FLOW": "ACTIVE", "REPORT_RESTORE_RISK": "ACTIVE",
    "DISABLE_DATA_FLOW": "DISABLED", "BLOCK_RESTORE": "BLOCKED", "DELETE_RECORD": "ABSENT",
    "REDACT_RECORD": "REDACTED", "ANONYMIZE_RECORD": "ANONYMIZED",
    "VERIFY_RECORD_ABSENT": "ABSENT", "VERIFY_RECORD_PRESENT": "PRESENT",
    "VERIFY_RECORD_REDACTED": "REDACTED", "VERIFY_RECORD_ANONYMIZED": "ANONYMIZED",
    "VERIFY_DATA_FLOW_DISABLED": "DISABLED", "VERIFY_RESTORE_BLOCKED": "BLOCKED",
}
ORDER = {
    "FINDING": ["REPORT_REMAINING_RECORD", "REPORT_EXPOSED_PII", "REPORT_ACTIVE_DATA_FLOW", "REPORT_RESTORE_RISK"],
    "REMEDIATION": ["DISABLE_DATA_FLOW", "BLOCK_RESTORE", "DELETE_RECORD", "REDACT_RECORD", "ANONYMIZE_RECORD"],
    "VERIFICATION": ["VERIFY_RECORD_ABSENT", "VERIFY_RECORD_PRESENT", "VERIFY_RECORD_REDACTED",
                     "VERIFY_RECORD_ANONYMIZED", "VERIFY_DATA_FLOW_DISABLED", "VERIFY_RESTORE_BLOCKED"],
}


def load_policy() -> dict[str, str]:
    with open(DATASET_DIR / "deletion_rules.csv", newline="", encoding="utf-8") as f:
        return {row["data_category"]: row["required_action"] for row in csv.DictReader(f)}


def _prefix(resource_id: str) -> str:
    return resource_id.rsplit("_", 1)[0]


def _has_pii(fields: dict) -> bool | None:
    seen = False
    for key, value in fields.items():
        leaf = key.rsplit(".", 1)[-1].lower()
        if leaf in PII_KEYS:
            seen = True
            if value.strip().lower() not in NULLS:
                return True
    if fields.get("direct_identifiers", "") not in ("", None):
        return fields["direct_identifiers"].strip() not in ("0",)
    return False if seen else None


def observe(fields: dict) -> str | None:
    """Map one record's fields to a state, or None when it carries no outcome."""
    for key in ("result", "col_4"):
        state = EXPLICIT.get(fields.get(key, "").strip().lower())
        if state:
            return state
    if "restore_allowed" in fields:
        return "RESTORABLE" if fields["restore_allowed"].lower() in TRUE else "BLOCKED"
    if "deletion_block" in fields:
        return "BLOCKED" if fields["deletion_block"].lower() in TRUE else "RESTORABLE"
    if "enabled" in fields:
        return "ACTIVE" if fields["enabled"].lower() in TRUE else "DISABLED"
    status = fields.get("http_status") or fields.get("status_code") or ""
    rows = fields.get("rows", "")
    if status == "404" or rows == "0" or fields.get("profile", "x") == "":
        return "ABSENT"
    if status == "200" or rows.isdigit() or "updated_at" in fields or fields.get("event", "").endswith("_completed") \
            or fields.get("event") in ("message_pii_scan", "analytics_profile_read"):
        pii = _has_pii(fields)
        if fields.get("event") == "message_pii_scan":
            pii = True
        return "EXPOSED" if pii else ("CLEAN" if pii is False else "PRESENT")
    return None


def _category(resource_id: str, records: list[dict]) -> str:
    for record in records:
        fields = record["fields"]
        for key in ("record_type", "col_3"):
            if fields.get(key, "").isupper():
                return fields[key]
        if "attachment" in (fields.get("collection", "") + fields.get("section", "")):
            return "SUPPORT_ATTACHMENT"
        if _prefix(resource_id) == "support" and ({"file", "file_name"} & set(fields)):
            return "SUPPORT_ATTACHMENT"
        if fields.get("event", "").startswith("contact_"):
            return "SECONDARY_IDENTIFIER"  # contact copies of identifiers are deleted outright
    return KINDS.get(_prefix(resource_id), ("", "USER_PROFILE"))[1]


def _resource_state(resource_id: str, bundle: dict) -> tuple[str, str, str] | None:
    """Return (state, evidence_id, category) from the latest observation."""
    records = [e for e in bundle["evidence"] if e["fields"].get("resource_id") == resource_id]
    observations = []
    for record in records:
        state = observe(record["fields"])
        if not state and record.get("kind") == "snapshot":
            pii = _has_pii(record["fields"])
            state = "EXPOSED" if pii else ("CLEAN" if pii is False else "PRESENT")
        if state:
            # A snapshot shows state at capture time; a log line at its own time.
            when = record["captured_at"] if record.get("kind") == "snapshot" else (record["time"] or record["captured_at"])
            observations.append((when, state != "ABSENT", state, record["evidence_id"]))
    for absence in bundle["absences"]:
        if absence["resource_id"] == resource_id and _prefix(resource_id) == "account":
            observations.append((absence["captured_at"], False, "ABSENT", absence["evidence_id"]))
    observations = [o for o in observations if o[0] <= bundle["audit_at"]]
    if not observations:
        return None
    # Latest wins; at the same instant, a copy that still exists beats an absence.
    _, _, state, evidence_id = max(observations)
    return state, evidence_id, _category(resource_id, records)


def _plan(state: str, action: str, category: str) -> tuple[str | None, str | None, str | None]:
    """Return (finding, remediation, verification) operations for one resource."""
    if category == "DATA_FLOW":
        return ("REPORT_ACTIVE_DATA_FLOW", "DISABLE_DATA_FLOW", "VERIFY_DATA_FLOW_DISABLED") \
            if state == "ACTIVE" else (None, None, "VERIFY_DATA_FLOW_DISABLED")
    if category == "BACKUP_ARCHIVE":
        return ("REPORT_RESTORE_RISK", "BLOCK_RESTORE", "VERIFY_RESTORE_BLOCKED") \
            if state in ("RESTORABLE", "ACTIVE") else (None, None, "VERIFY_RESTORE_BLOCKED")
    if action == "RETAIN":
        return (None, None, "VERIFY_RECORD_PRESENT") if state != "ABSENT" else (None, None, None)
    if action == "DELETE":
        return (None, None, "VERIFY_RECORD_ABSENT") if state == "ABSENT" else \
            ("REPORT_REMAINING_RECORD", "DELETE_RECORD", "VERIFY_RECORD_ABSENT")
    verify = "VERIFY_RECORD_REDACTED" if action == "REDACT" else "VERIFY_RECORD_ANONYMIZED"
    fix = "REDACT_RECORD" if action == "REDACT" else "ANONYMIZE_RECORD"
    if state in ("EXPOSED", "PRESENT"):
        return "REPORT_EXPOSED_PII", fix, verify
    return (None, None, verify) if state == "CLEAN" else (None, None, None)


def audit(bundle: dict | None, policy: dict[str, str]) -> tuple[str, list[dict]]:
    """Return (deletion_status, steps) for one bundle."""
    if not bundle:
        return "COMPLETE", []

    findings, remediation, verification = [], [], []
    for resource_id in bundle["resources"]:
        if _prefix(resource_id) not in KINDS:
            continue  # e.g. order numbers read from documents are not stored resources
        resolved = _resource_state(resource_id, bundle)
        if not resolved:
            continue
        state, evidence_id, category = resolved
        system_id = KINDS.get(_prefix(resource_id), ("unknown_service",))[0]
        finding, fix, verify = _plan(state, policy.get(category, "DELETE"), category)
        if finding:
            findings.append((finding, system_id, resource_id, evidence_id))
            remediation.append((fix, system_id, resource_id, ""))
        if verify:
            verification.append((verify, system_id, resource_id, evidence_id))

    status = "INCOMPLETE" if findings else "COMPLETE"
    if status == "INCOMPLETE":
        verification = [(op, system, resource, "") for op, system, resource, _ in verification]

    steps = []
    for phase, items in (("FINDING", findings), ("REMEDIATION", remediation), ("VERIFICATION", verification)):
        for op, system_id, resource_id, evidence_id in sorted(items, key=lambda i: (ORDER[phase].index(i[0]), i[1], i[2])):
            steps.append({"step_no": len(steps) + 1, "phase": phase, "system_id": system_id,
                          "resource_id": resource_id, "operation": op, "state": OP_STATE[op],
                          "evidence_id": evidence_id})
    return status, steps
