# audit/ (Stage 2, deterministic)

Turns a case bundle plus `deletion_rules.csv` into `deletion_status` and ordered steps. No LLM is involved.

| File | What it does |
|---|---|
| `rules.py` | **State:** for each resource, the latest observation at or before `audit_at` wins. When two observations share a time, a surviving copy beats an absence. Observations come from explicit results (`FOUND`/`NOT_FOUND`/`hit`/`IDENTIFIABLE`…), `404`/`rows=0`, `enabled`, `restore_allowed`/`deletion_block`, and whether PII fields hold values. Reported statuses and activity results are treated as claims and never set state. **Category:** taken from `record_type` when present, otherwise inferred from the resource prefix (`contact_*` lookups → `SECONDARY_IDENTIFIER`; support records with a file → `SUPPORT_ATTACHMENT`). **Plan:** the policy action (DELETE / REDACT / ANONYMIZE / RETAIN; data flows; backups) maps each violation to finding → remediation → verification. **Status:** any finding means `INCOMPLETE`, otherwise `COMPLETE`. COMPLETE verification steps cite evidence; INCOMPLETE future steps cite `""`. **Order:** follows the samples. Findings: REMAINING, EXPOSED, FLOW, RESTORE. Remediation: DISABLE, BLOCK, DELETE, REDACT, ANONYMIZE. Verification: ABSENT, PRESENT, REDACTED, ANONYMIZED, DISABLED, BLOCKED. Within each group, steps are sorted by `system_id` and then `resource_id`. |
| `output.py` | Contract validator (field order, consecutive `step_no`, phase order, allowed operation/state pairs, evidence rules) and `output.csv` writer. Rows are sorted by case number. |
