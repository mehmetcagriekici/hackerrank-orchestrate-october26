"""JSON exports of any nesting: every object with a resource_id becomes a record.

Scalar fields of enclosing objects (captured_at, data_store, system, ...) are
inherited as context, and nested objects are flattened as "parent.child".
"""

import json
from pathlib import Path

from organizer.parsers.common import ParsedFile, first_time, make_record


def _flatten(obj: dict, prefix: str = "") -> dict:
    flat = {}
    for key, value in obj.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            flat.update(_flatten(value, f"{name}."))
        elif isinstance(value, list):
            if all(not isinstance(v, (dict, list)) for v in value):
                flat[name] = ",".join("" if v is None else str(v) for v in value)
        else:
            flat[name] = value
    return flat


def _walk(node, path: str, context: dict, out: list) -> None:
    if isinstance(node, list):
        for i, item in enumerate(node):
            _walk(item, f"{path}[{i}]", context, out)
        return
    if not isinstance(node, dict):
        return

    scalars = {k: v for k, v in node.items() if not isinstance(v, (dict, list))}
    if "resource_id" in node:
        fields = {**context, **_flatten(node)}
        time = first_time(*(str(v) for k, v in fields.items() if k.endswith(("_at", "time"))))
        out.append(make_record(path, fields, time, "snapshot"))
        return

    inherited = {**context, **scalars}
    for key, value in node.items():
        if isinstance(value, (dict, list)):
            _walk(value, f"{path}.{key}", {**inherited, "section": key}, out)


def parse_json(path: Path) -> ParsedFile:
    data = json.loads(path.read_text(encoding="utf-8"))
    parsed = ParsedFile()
    if isinstance(data, dict):
        parsed.meta = {k: v for k, v in data.items() if not isinstance(v, (dict, list))}
    _walk(data, "$", {}, parsed.records)
    return parsed
