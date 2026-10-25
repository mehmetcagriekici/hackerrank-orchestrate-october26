# llm/

| File | What it does |
|---|---|
| `gemini_client.py` | Minimal Gemini REST client using only the standard library. It sends JSON-mode requests at temperature 0, optionally with inline PNG/PDF attachments. It retries on 429/5xx and network errors, then records token usage. |
| `env.py` | Loads `KEY=VALUE` pairs from the uncommitted repo-root `.env` without overriding real environment variables. |
| `usage.py` | Per-model call and token totals (`.cache/usage.json`). Every call is also appended to `.cache/usage_calls.jsonl`, so counts survive a crashed run. |

Models used (configurable through environment variables):
- **Gate:** `GATE_MODEL`, default `gemini-3.5-flash-lite`.
- **Media extraction:** `EXTRACT_MODEL`, default `gemini-3.5-flash`. Use `gemini-3.5-flash-lite` if the free quota runs out.

The audit makes no LLM calls. Credentials come only from `GEMINI_API_KEY` (environment or `.env`).
