# llm/

LLM clients, one per stage, kept separate so each model does only its own job:

- **gate:** classifies whether a request authorizes deletion
- **extraction:** reads PNG/PDF evidence once; results are cached
- **audit:** produces the case verdict and steps

Credentials and model names come from environment variables only (an uncommitted `.env` is fine). This folder also records call counts and tokens for `evaluation/usage_report.md`.
