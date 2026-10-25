# organizer/ (between Stage 1 and Stage 2)

Turns evidence files into one audit bundle per case. It organizes data and never decides a case's status.

| File | What it does |
|---|---|
| `organizer.py` | Parses all 94 files once. For each case it keeps evidence with `captured_at ≤ audit_at`, then runs two passes. **Pass 1** finds records whose values match the person's links as whole tokens (lowercased, phones normalized, `null` ignored), plus log lines that share their trace id; their `resource_id`s become the case's resources. **Pass 2** collects every record about those resources, including ones with no identifier, such as a `404` lookup. It also records SQL absences and activity rows. Returns `None` when nothing links. |
| `account_linker.py` | Deleted account profiles leave no identifier in evidence. Their deletion-worker `DELETE_RECORD` rows are assigned **one-to-one across all authorized requests**, using the window `reported_at − 80 min … + 10 min` and preferring rows whose result matches the reported status. Accounts already linked to another person are excluded, and same-time ties go by request order. This only identifies the resource; evidence decides its state. Accuracy on samples: 20/20. |
| `extract_media.py` | One-time vision-LLM extraction of the 15 PNG/PDF files into `.cache/extractions/` (prompt in `prompts/extract_system.md`). |
| `parsers/` | One parser per evidence format, all emitting the same record shape. |

Bundle fields: `case_id`, the request timestamps and claims, `links`, `resources`, `evidence` (records with `evidence_id`/`captured_at`), `absences`, and `activity`.
