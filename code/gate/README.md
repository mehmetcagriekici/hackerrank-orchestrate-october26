# gate/ — Stage 1

Decides which requests go on to the audit stage, and collects the links needed to find their evidence.

1. **Sanity checks (code).** Checks that timestamps are ordered (`requested_at` ≤ `reported_at` ≤ `audit_at`) and other structural fields. A failure becomes `NOT_APPLICABLE`.
2. **Authorization gate (LLM).** Reads only `request_text` and answers whether the request authorizes deletion (AGENTS.md §6.5). Results are keyed by `case_id`. A "no" becomes `NOT_APPLICABLE`.
3. **Link builder (code).** For each valid case, expands `email` → `user_id` → every current and historical identifier (email, phone, email hash, name) using `user_identities.csv` and `user_audit_log.csv`, plus related resource IDs from `system_activity.csv`.

Output: one record per valid `case_id` with its links and `audit_at`, passed to `organizer/`.
