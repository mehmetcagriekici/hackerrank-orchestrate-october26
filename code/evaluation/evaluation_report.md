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
| Gold steps / predicted steps | 193 / 179 |
| Step precision | **0.989** |
| Step recall | **0.917** |
| Step F1 | **0.952** |

Recall by phase:

| Phase | Matched / gold |
|---|---|
| FINDING | **41 / 41** |
| REMEDIATION | **41 / 41** |
| VERIFICATION | 95 / 111 |

Field accuracy, comparing step *i* of the prediction with step *i* of the gold answer:

| Field | Accuracy |
|---|---|
| phase | 0.922 |
| system_id | 0.824 |
| resource_id | 0.824 |
| operation | 0.824 |
| state | 0.824 |
| evidence_id | 0.917 |

Positional field accuracy is lower than step F1 because a single missing verification step
shifts every later step by one position.

## 3. Sequence accuracy

| Metric | Value |
|---|---|
| Exact full-sequence match | **0.500** (16/32) |
| Cases with the correct number of steps | 17/32 |

Every finding and remediation step is correct and correctly ordered. The remaining sequence misses
come from **16 missing verification steps**: 7 anonymized `analytics_*` records and 7 `audit_record_*`
entries that no pre-`audit_at` evidence links to the person (the audit records appear only in files
captured after `audit_at`, which §6.2 forbids using, or nowhere), one deleted account with no workflow
row (case_04), and one case citing a different, also valid evidence file (case_31).

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
| Ignore non-resource IDs read from documents (order numbers); support records with a file → `SUPPORT_ATTACHMENT` (DELETE); `contact_*` lookups → `SECONDARY_IDENTIFIER` (DELETE) | 1.000 | 0.898 |
| Workflow-timing account linker (`code/organizer/account_linker.py`, below) | **1.000** | **0.952** |

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

**Workflow-timing account linker.** A deleted `account_*` profile leaves no identifier in evidence;
its only trace is the deletion worker's `DELETE_RECORD` row, logged between 75 minutes before and
8 minutes after the case's `reported_at`. AGENTS.md §6.6 lists timestamps and resource IDs as grounded
links, so rows are assigned **one-to-one across all 540 authorized requests** (sample and eval). The
assignment uses that time window, prefers rows whose result matches the reported status, excludes accounts already
linked to another person, and breaks same-slot ties by request order. It is used only to *identify*
the resource; its state is still decided from evidence.
- A naive window picked the right account in 10/32 samples. Excluding non-deletion cases and
  already-linked accounts, plus the tie-break, reached **20/20 correct, 0 wrong** (the other samples
  were already linked by identifiers; one has no workflow row). It was adopted only under a
  100%-on-samples condition.
- The same method for anonymized analytics records scored 2 right / 5 wrong, so it was **not** adopted.
