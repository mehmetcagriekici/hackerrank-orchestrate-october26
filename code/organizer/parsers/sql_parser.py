"""SQLite snapshot exports: every table row becomes a record."""

import re
import sqlite3
from pathlib import Path

from organizer.parsers.common import ParsedFile, make_record

HEADER = re.compile(r"^--\s*([^:]+):\s*(.+)$")


def parse_sql(path: Path) -> ParsedFile:
    script = path.read_text(encoding="utf-8")
    parsed = ParsedFile()
    for line in script.splitlines():
        match = HEADER.match(line)
        if match:
            parsed.meta[match.group(1).strip().lower().replace(" ", "_")] = match.group(2).strip()

    db = sqlite3.connect(":memory:")
    try:
        db.executescript(script)
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for table in tables:
            cursor = db.execute(f'SELECT * FROM "{table}"')
            columns = [c[0] for c in cursor.description]
            present = set()
            for row in cursor:
                fields = dict(zip(columns, row))
                present.add(str(fields.get("resource_id", "")))
                parsed.records.append(make_record(table, fields, str(fields.get("updated_at") or ""), "snapshot"))
            if "resource_id" in columns:
                parsed.presence[table] = present - {""}
    finally:
        db.close()
    return parsed
