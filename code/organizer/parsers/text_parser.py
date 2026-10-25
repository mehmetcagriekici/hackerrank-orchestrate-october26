"""Plain-text records such as shift handovers.

Lines like "- ts | system | resource_id | type | result | subject" become
records with positional columns; the resource ID column is detected by pattern.
Header lines "Key: value" become file metadata.
"""

from pathlib import Path

from organizer.parsers.common import RESOURCE_ID, ParsedFile, first_time, make_record


def parse_text(path: Path) -> ParsedFile:
    parsed = ParsedFile()
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip().lstrip("-").strip()
        if " | " in line:
            columns = [c.strip() for c in line.split(" | ")]
            fields = {f"col_{i}": value for i, value in enumerate(columns)}
            resource = next((c for c in columns if RESOURCE_ID.fullmatch(c)), "")
            if resource:
                fields["resource_id"] = resource
            parsed.records.append(make_record(f"line {number}", fields, first_time(line)))
        elif ":" in line and not parsed.records:
            key, _, value = line.partition(":")
            parsed.meta[key.strip().lower().replace(" ", "_")] = value.strip()
    return parsed
