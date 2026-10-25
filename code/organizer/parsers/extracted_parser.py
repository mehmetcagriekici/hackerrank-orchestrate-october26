"""PNG / PDF evidence, read from the extraction cache.

The extraction LLM (not built yet) reads each image or PDF once and writes
.cache/extractions/<file name>.json as {"records": [{"where", "time", "fields"}]}.
Until a cache file exists, the evidence yields no records.
"""

import json
from pathlib import Path

from organizer.parsers.common import ParsedFile, make_record

CACHE_DIR = Path(__file__).resolve().parents[3] / ".cache" / "extractions"


def parse_extracted(path: Path) -> ParsedFile:
    cached = CACHE_DIR / f"{path.name}.json"
    if not cached.exists():
        return ParsedFile(meta={"extraction": "missing"})
    data = json.loads(cached.read_text(encoding="utf-8"))
    records = [make_record(r.get("where", "page"), r.get("fields", {}), r.get("time", ""), "snapshot")
               for r in data.get("records", []) if isinstance(r, dict)]
    return ParsedFile(meta=data.get("meta", {}), records=records)
