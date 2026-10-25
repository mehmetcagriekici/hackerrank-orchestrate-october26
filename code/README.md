# code/

Solution source for the Ghost Data Still Exists deletion-audit agent.

Pipeline: `gate/` → `organizer/` → `audit/`, run end to end by `main.py`.

| Folder | Role | Uses an LLM? |
|---|---|---|
| `gate/` | Stage 1: sanity checks, deletion-authorization gate, link builder | Yes (gate only) |
| `organizer/` | Opens evidence, parses each format into common facts per case | No (reads cached image/PDF extractions) |
| `audit/` | Stage 2: audit LLM decides status and steps; output validated and written | Yes (audit only) |
| `llm/` | One client per stage, configured from environment variables | — |
| `prompts/` | Prompt text for each LLM stage, kept outside the code | — |
| `tests/` | Per-stage tests against the 32 public samples | — |
| `evaluation/` | Required `evaluation_report.md` and `usage_report.md` | — |

Any case that fails a sanity check, or is judged a non-deletion request, is written as `NOT_APPLICABLE` with `[]`.
