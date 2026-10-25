"""Log files in mixed styles: logfmt, quoted key="value", pipe-delimited,
syslog, and lines with an embedded JSON object.

Each line becomes one record. A "trace" field (trace_id / requestId / bare
tr-*/rb-* token) lets the organizer group lines of the same request, since a
lookup key and its resource_id often sit on different lines of one trace.
"""

import json
import re
from pathlib import Path

from organizer.parsers.common import ParsedFile, first_time, make_record

PAIR = re.compile(r'([A-Za-z_][\w.]*)=("(?:[^"\\]|\\.)*"|\S+)')
TRACE_TOKEN = re.compile(r"\b(?:tr|rb)-[\w-]+\b")
TRACE_KEYS = ("trace_id", "requestId", "trace")


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1].replace('\\"', '"')
    return value


def _pairs(text: str) -> dict:
    fields = {}
    for key, raw in PAIR.findall(text):
        value = _unquote(raw)
        if "=" in value and " " in value:
            fields.update(_pairs(value))  # e.g. message="k=\"v\" k2=\"v2\""
        else:
            fields[key] = value
    return fields


def parse_line(line: str) -> dict:
    fields = {}
    brace = line.find("{")
    if brace != -1 and line.rstrip().endswith("}"):
        try:
            fields.update(json.loads(line[brace:]))
        except json.JSONDecodeError:
            pass
    fields.update(_pairs(line))

    parts = [p.strip() for p in line.split(" | ")]
    if len(parts) >= 5:  # ts | LEVEL | service | trace | event | k=v ...
        fields.setdefault("level", parts[1])
        fields.setdefault("service", parts[2])
        fields.setdefault("event", parts[4])

    trace = next((fields[k] for k in TRACE_KEYS if fields.get(k)), "")
    if not trace:
        match = TRACE_TOKEN.search(line)
        trace = match.group(0) if match else ""
    fields["trace"] = trace
    return fields


def parse_log(path: Path) -> ParsedFile:
    parsed = ParsedFile()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parsed.records.append(make_record(f"line {number}", parse_line(line), first_time(line)))
    return parsed
