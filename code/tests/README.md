# tests/

Run from the repository root.

| File | Command | What it checks |
|---|---|---|
| `evaluate.py` | `python3 code/tests/evaluate.py [predicted.csv]` | Scores a prediction (default `.cache/sample_output.csv`, produced by `python3 code/main.py --split sample`) against `dataset/sample_output.csv`. Reports status accuracy, step precision/recall/F1, positional field accuracy and exact-sequence accuracy, and lists status mismatches. |
| `custom_cases.py` | `python3 code/tests/custom_cases.py` | 5 hand-built audit cases: replica drift, evidence after `audit_at` ignored, tombstone redaction, flow/restore ordering before deletion, and a fully cited COMPLETE case. Checks status, exact operation sequence, contract validity and evidence citations. Needs no LLM. |
