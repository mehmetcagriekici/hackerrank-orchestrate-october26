# organizer/parsers/

One parser per evidence format. Each parser turns a file into a list of facts in the same common shape.

| Format | Count in dataset | Notes |
|---|---|---|
| `.sql` | 24 | SQLite snapshots. Compare primary/replica tables; a missing row can mean absence |
| `.json` | 28 | Record bundles with fields such as `system`, `resource_id`, `record_type`, `result` |
| `.log` | 26 | Timestamped service log lines with key="value" pairs |
| `.txt` | 1 | Plain-text handover records |
| `.png` / `.pdf` | 15 | Extracted once by an extraction LLM; parsed from the cached result |

Normalize identifiers (for example, lowercase emails) before matching.
