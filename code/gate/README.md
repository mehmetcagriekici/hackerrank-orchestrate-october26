# gate/ (Stage 1)

Decides which requests go on to the audit stage, and collects the identifiers needed to find their evidence.

| File | What it does |
|---|---|
| `sanity.py` | Structural checks: case_id, email, request text, ISO timestamps, and `requested_at ≤ reported_at ≤ audit_at`. Any failure → `NOT_APPLICABLE`. |
| `authorize.py` | LLM gate (`gemini-3.5-flash-lite`, prompt in `prompts/gate_system.md`). Reads only `request_text` (AGENTS.md §6.5) and returns true/false for every key. Unique texts are sent in batches of 60, and answers are cached by text hash in `.cache/gate_decisions.json`, so reruns make no calls. A missing key is reported and treated as `NOT_APPLICABLE`. |
| `link_builder.py` | Expands the request `email` → `user_id` → every current and historical email, phone, email hash and name. It uses `user_identities.csv` and the `user_audit_log.csv` rows with `event_time ≤ audit_at`. Values are normalized with `helpers/normalize_text.py` and returned as `{key: set(values)}`. |

Output: for each authorized case, its links, which `organizer/` uses to find evidence.
