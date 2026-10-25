# Ghost Data Still Exists: Deletion-Audit Agent

A deletion-audit pipeline for HackerRank Orchestrate (October 2026). For every request in
`dataset/deletion_requests.csv`, it decides whether deletion was really requested, reconstructs the person's
identifiers, collects the evidence they appear in up to `audit_at`, applies `deletion_rules.csv`, and writes
`output.csv` (`case_id,deletion_status,steps_json`).

## Setup

Requirements: **Python 3.10+** and nothing else. The code uses only the standard library (`sqlite3`, `urllib`, `csv`, `json`).

LLM calls use the Google Gemini API. Put the key in an uncommitted `.env` at the repository root:

```text
GEMINI_API_KEY=your-key-here
# optional overrides
GATE_MODEL=gemini-3.5-flash-lite
EXTRACT_MODEL=gemini-3.5-flash
```

`.env` and `.cache/` are git-ignored. Never commit the key.

## Run

From the repository root, with `dataset/` in place:

```bash
# 1. One-time: extract PNG/PDF evidence (15 files, one LLM call each, cached in .cache/extractions/)
python3 code/organizer/extract_media.py

# 2. Full run: 518 evaluation requests -> ./output.csv
python3 code/main.py

# Public samples -> .cache/sample_output.csv, then score against dataset/sample_output.csv
python3 code/main.py --split sample
python3 code/tests/evaluate.py

# Participant-made audit test cases
python3 code/tests/custom_cases.py
```

LLM answers are cached by content, so reruns are deterministic and make no new calls.
If step 1 is skipped, image and PDF evidence contribute no records and the run still completes.

## Architecture

```text
GATE (code/gate/)
  sanity.py       timestamp and field checks             fail -> NOT_APPLICABLE, []
  authorize.py    LLM: does request_text authorize deletion? (batched, cached)   no -> NOT_APPLICABLE, []
  link_builder.py email -> user_id -> every current/historical email, phone, hash, name (<= audit_at)

ORGANIZER (code/organizer/), code only, never decides
  parsers/        sql (in-memory SQLite) | json (any nesting) | log (6 styles + trace ids) | txt | png/pdf (LLM cache)
  organizer.py    evidence captured <= audit_at; pass 1 = records/traces naming the person -> resource IDs;
                  pass 2 = every record about those resources; SQL absences; activity rows
  account_linker.py  deleted account profiles <- deletion-worker rows, one-to-one by timing (20/20 on samples)
  extract_media.py   one-time vision-LLM extraction of PNG/PDF evidence

AUDIT (code/audit/), deterministic rules
  rules.py        latest observation per resource -> state; policy action by data category;
                  FINDING -> REMEDIATION -> VERIFICATION with sample-derived ordering
  output.py       contract validator + CSV writer
```

Key decisions:
- **LLMs only where language or vision is needed.** That's the multilingual request gate and reading
  screenshots/PDFs. The audit is rule-based: fast (~30 s for 518 cases), repeatable, and explainable.
- **Reported statuses and activity results are claims.** Only evidence observations set a resource's state.
- **The latest observation at or before `audit_at` wins.** A copy that still exists (for example in a failover
  replica) beats a same-time absence.
- **Grounded links only.** Resources are linked through identifiers, `user_id`, a shared log trace, or (for deleted
  account profiles) a one-to-one assignment of deletion-worker activity rows by timing, validated 20/20 on samples.

## Layout

| Path | Contents |
|---|---|
| `code/main.py` | Pipeline entry point |
| `code/gate/`, `code/organizer/`, `code/audit/` | The three stages (each has a README) |
| `code/llm/` | Gemini REST client, `.env` loader, token usage tracking |
| `code/prompts/` | Gate and extraction prompts |
| `code/helpers/normalize_text.py` | Shared identifier normalization |
| `code/tests/` | Sample scorer and custom test cases |
| `code/evaluation/` | `evaluation_report.md`, `usage_report.md` |

## Results (32 public samples)

Status accuracy **1.000**, step precision **0.989**, step recall **0.917**, step F1 **0.952**, exact sequence **0.500**.
See `code/evaluation/evaluation_report.md`.

## Packaging

```bash
zip -r code.zip README.md code -x "*/__pycache__/*" "*/.venv/*" "*/venv/*" "*/node_modules/*" "*/.git/*" "*/.DS_Store"
```

The challenge statement is in `problem_statement.md`, and the agent rules are in `AGENTS.md`.
