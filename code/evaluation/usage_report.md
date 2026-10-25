# Usage Report: final full-dataset run

## How the LLMs are used

| Stage | Provider / model | Calls | When |
|---|---|---|---|
| Gate (does the request authorize deletion?) | Google / `gemini-3.5-flash-lite` | 7 | Batched: all unique request texts (518 eval + 32 samples) in batches of 60 |
| Media extraction (PNG/PDF → records) | Google / `gemini-3.5-flash` | 10 | Once per file |
| Media extraction, after the 3.5-flash free quota ran out | Google / `gemini-3.5-flash-lite` | 5 | Once per file |
| Audit | none: deterministic rules | 0 | — |

Every LLM result is cached (`.cache/gate_decisions.json`, `.cache/extractions/`). The run that wrote
the final `output.csv` reused those caches and made **0 new calls** (runtime 27 s). The table below
therefore reports the calls that produced the cached results the final run depends on.

## Tokens

| Model | Calls | Input tokens | Output tokens | Notes |
|---|---|---|---|---|
| `gemini-3.5-flash-lite` (gate) | 7 | 22,762 | 8,036 | measured (`usageMetadata`) |
| `gemini-3.5-flash-lite` (extraction) | 5 | 6,988 | 4,017 | measured |
| `gemini-3.5-flash` (extraction) | 10 | ~14,000 | ~8,000 | **estimated**: the run stopped on HTTP 429 before its counters were saved; estimated from the 5 measured extraction calls (~1.4k in / ~0.8k out per file). Thinking tokens for this model were not recorded. |
| **Total** | **22** | **~43,750** | **~20,053** | ~63,800 tokens |

| Per request (518 evaluation cases) | Value |
|---|---|
| Model calls | 0.04 |
| Tokens | ~123 (~84 input, ~39 output) |

Per-request numbers divide the totals by 518. The gate totals also include the 32 sample texts
classified in the same batches.

## Cost

| | Total | Per request |
|---|---|---|
| Billed cost | **$0.00** (Gemini API free tier) | $0.00 |

Per-model totals: `gemini-3.5-flash-lite` $0.00 (12 calls), `gemini-3.5-flash` $0.00 (10 calls).
Paid-tier prices for these models were not verified, so no paid-equivalent estimate is given.
At ~64k tokens in total, the cost on any paid tier would be at most cents.

Since this run, usage is also appended per call to `.cache/usage_calls.jsonl`, so future runs record
exact counts even if they stop early.
