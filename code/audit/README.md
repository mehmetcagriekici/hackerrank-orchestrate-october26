# audit/ — Stage 2

Receives the organizer's per-case JSON bundle together with `deletion_rules.csv` and the case's claims (`reported_status`, `reported_at`).

- **Audit LLM.** Decides `COMPLETE` or `INCOMPLETE` and produces the ordered `FINDING` → `REMEDIATION` → `VERIFICATION` steps (AGENTS.md §6.3–§6.6).
- **Output (code).** Validates every step (allowed operations and states, consecutive `step_no`, evidence rules), then writes `output.csv` at the repository root: 518 rows, sorted by `case_id`.
