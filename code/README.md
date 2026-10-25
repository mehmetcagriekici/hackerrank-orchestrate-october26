# code/

Solution source for the Ghost Data Still Exists deletion-audit agent.

Pipeline: `gate/` → `organizer/` → `audit/`, run end to end by `main.py`.

| Folder | Role | Uses an LLM? |
|---|---|---|
| `gate/` | Stage 1: sanity checks, deletion-authorization gate, link builder | Yes: the gate classifier only |
| `organizer/` | Parses evidence into common records; builds one audit bundle per case; links deleted accounts by workflow timing | Only the one-time PNG/PDF extraction (`extract_media.py`) |
| `audit/` | Stage 2: deterministic policy rules decide status and steps; output validated and written | No |
| `helpers/` | Shared identifier normalization (`normalize_text.py`) | — |
| `llm/` | Gemini REST client, `.env` loader, per-call token usage | — |
| `prompts/` | Prompt text for the gate and the media extraction | — |
| `tests/` | Sample scorer and participant-made audit test cases | — |
| `evaluation/` | Required `evaluation_report.md` and `usage_report.md` | — |

Outcomes:
- A failed sanity check, or a request that doesn't authorize deletion → `NOT_APPLICABLE`, `[]`.
- An authorized request where no resource links to the person → `COMPLETE`, `[]`. The data supports this: a clean deletion leaves nothing to find.
- Otherwise the audit rules decide `COMPLETE` or `INCOMPLETE`, with ordered steps.

Run from the repository root: `python3 code/main.py` (see the root `README.md`).
