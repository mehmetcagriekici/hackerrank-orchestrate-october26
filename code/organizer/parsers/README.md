# organizer/parsers/

One parser per evidence format. Each one returns a `ParsedFile` (`common.py`) holding file metadata, a list of records, and, for SQL only, which resource IDs each table contains.

Record shape: `{"where": table / line / json path, "time": ISO or "", "kind": "snapshot" | "line", "fields": {str: str}}`.
A `snapshot` record (SQL row, JSON object, extracted screen/document) proves the record existed at capture time. A `line` record (log, text) proves only what it states.

| Parser | Format | Files | Notes |
|---|---|---|---|
| `sql_parser.py` | `.sql` | 24 | Loads the snapshot into in-memory SQLite. Every row is a record, and per-table presence sets detect replication drift and absence. |
| `json_parser.py` | `.json` | 28 | Recursive walk; every object with a `resource_id` is a record. It inherits context from parent objects and flattens nested objects to `a.b` keys. |
| `log_parser.py` | `.log` | 26 | Handles logfmt, quoted `key="value"`, pipe-delimited, syslog and embedded-JSON lines, plus nested `message="k=v"`. Extracts a `trace` id. |
| `text_parser.py` | `.txt` | 1 | Pipe-separated handover lines; positional `col_N` fields plus the detected `resource_id`. |
| `extracted_parser.py` | `.png` / `.pdf` | 15 | Reads `.cache/extractions/<file>.json` written by `../extract_media.py`. Yields no records if the cache is missing. |
