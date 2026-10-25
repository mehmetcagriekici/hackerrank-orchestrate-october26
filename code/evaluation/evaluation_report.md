# Evaluation Report: Ghost Data Still Exists

All numbers come from the final pipeline (`python code/main.py --split sample`) scored with
`python code/tests/evaluate.py` against `dataset/sample_output.csv` (32 public cases).
No organizer-only files were used.

## 1. Case-level deletion-status accuracy

| Metric | Value |
|---|---|
| Cases | 32 |
| Status accuracy | **1.000** (32/32) |
| Gold mix | 22 INCOMPLETE, 10 COMPLETE |

On the 518 evaluation cases, the final run produced 151 COMPLETE, 357 INCOMPLETE and 10 NOT_APPLICABLE.
The 10 NOT_APPLICABLE cases (`case_533`–`case_542`) were checked by hand: all are correction,
marketing opt-out, export or access requests, several of which say "do not delete" outright.

## 2. Step-level and field-level accuracy

Step match = an identical `(phase, system_id, resource_id, operation, state, evidence_id)` tuple.

| Metric | Value |
|---|---|
| Gold steps / predicted steps | 193 / 159 |
| Step precision | **0.994** |
| Step recall | **0.819** |
| Step F1 | **0.898** |

Recall by phase:

| Phase | Matched / gold |
|---|---|
| FINDING | **41 / 41** |
| REMEDIATION | **41 / 41** |
| VERIFICATION | 76 / 111 |

Field accuracy, comparing step *i* of the prediction with step *i* of the gold answer:

| Field | Accuracy |
|---|---|
| phase | 0.819 |
| system_id | 0.591 |
| resource_id | 0.591 |
| operation | 0.648 |
| state | 0.648 |
| evidence_id | 0.819 |

Positional field accuracy is lower than step F1 because a single missing verification step
shifts every later step by one position.

## 3. Sequence accuracy

| Metric | Value |
|---|---|
| Exact full-sequence match | **0.250** (8/32) |
| Cases with the correct number of steps | 8/32 |

Every finding and remediation step is correct and correctly ordered. The sequence misses all come
from **missing verification steps**, mostly `VERIFY_RECORD_ABSENT` on a deleted `account_*`
profile and `VERIFY_RECORD_PRESENT` on some `audit_record_*` entries (see §5).

## 4. Participant-created evaluation cases

`python code/tests/custom_cases.py` runs 5 hand-built bundles through the audit and checks
status, exact operation sequence, contract validity and evidence citation. **5/5 pass.**

| # | Scenario | Expected |
|---|---|---|
| 1 | Replica drift: profile absent from the primary table but still present in the failover replica in the same snapshot | INCOMPLETE: report → delete → verify absent |
| 2 | Index entry was absent before `audit_at`; a *later* capture shows it restored | COMPLETE: later evidence ignored |
| 3 | Account tombstone keeps `user_id` but still shows an email; audit record retained | INCOMPLETE: REDACT (not delete) + verify retained record present |
| 4 | Active sync, restorable backup and a remaining export | INCOMPLETE: disable flow and block restore *before* deleting the export |
| 5 | Absent account, anonymized analytics, retained audit record | COMPLETE, with every verification step citing evidence |

## 5. Failures found and improvements made

Scores on the samples after each change:

| Change | Status | Step F1 |
|---|---|---|
| First end-to-end run | 0.719 | 0.601 |
| SQL rows and JSON objects count as *presence at capture time*; a replica copy beats a same-time absence; log lines sharing a trace pass links along; backup `deletion_block` handled | 0.969 | 0.854 |
| PNG/PDF evidence extracted once by a vision LLM (fixed case_07, a support attachment only visible in a PDF) | 0.969 | 0.816 |
| Ignore non-resource IDs read from documents (order numbers); support records with a file → `SUPPORT_ATTACHMENT` (DELETE); `contact_*` lookups → `SECONDARY_IDENTIFIER` (DELETE) | **1.000** | **0.898** |

Other failures found during development:

- **Phone normalization collisions.** An early normalizer added `+1` to every number, and later stripped
  the US country code. Tested against all 942 phones in the data; the final version keeps all digits
  with a leading `+`, and empty input stays empty (so it can never match everything).
- **Substring false matches.** `user_18` is a substring of `user_180`, so matching compares whole
  tokens, never substrings.
- **Empty-bundle handling.** Treating "no linked resources" as NOT_APPLICABLE mislabeled 5 sample
  cases, 3 of them COMPLETE (a clean deletion leaves no identifiers to find). Changed to COMPLETE.
- **Gate batching.** Missing keys in a batched LLM answer would silently become NOT_APPLICABLE;
  the gate now asks for a label for *every* key and reports any that are missing.

Known limitation: a deleted `account_*` profile is often linked to its person only by a
`system_activity.csv` row timed near `reported_at`. A timing heuristic chose the correct account in only
10/32 samples, so it was not adopted; those verification steps are missed instead of guessed.
