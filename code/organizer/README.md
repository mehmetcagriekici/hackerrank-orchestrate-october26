# organizer/ — between Stage 1 and Stage 2

Turns evidence files into per-case audit data. It only organizes data and never decides a case.

- Uses `evidence_files.csv` to locate files. Filters each case's evidence and activity to `≤ audit_at`.
- Matches file contents against the case's links: identifiers, `user_id` and resource IDs.
- Emits one JSON audit bundle per `case_id` in a common fact shape, so the audit stage never opens files.
- **Sanity check:** a valid case with zero resources found becomes `NOT_APPLICABLE`.

See `parsers/` for format handling.
