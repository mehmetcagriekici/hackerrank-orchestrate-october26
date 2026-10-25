"""Extract PNG / PDF evidence once with a vision LLM into .cache/extractions/.

    python code/organizer/extract_media.py [--force]

Each file gets one call; results are cached so the pipeline run itself spends nothing.
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from llm import usage  # noqa: E402
from llm.gemini_client import GeminiClient  # noqa: E402
from organizer.parsers.extracted_parser import CACHE_DIR  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PROMPT_FILE = ROOT / "code" / "prompts" / "extract_system.md"
MIME = {".png": "image/png", ".pdf": "application/pdf"}
EXTRACT_MODEL = os.environ.get("EXTRACT_MODEL", "gemini-3.5-flash")


def main(force: bool) -> None:
    client = GeminiClient(EXTRACT_MODEL)
    system = PROMPT_FILE.read_text(encoding="utf-8")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    media = sorted(p for p in (ROOT / "dataset" / "evidence").rglob("*") if p.suffix.lower() in MIME)
    for path in media:
        target = CACHE_DIR / f"{path.name}.json"
        if target.exists() and not force:
            continue
        result = client.generate_json(system, f"Evidence file: {path.name}",
                                      ((MIME[path.suffix.lower()], path.read_bytes()),))
        target.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{path.name}: {len(result.get('records', []))} records")
    usage.save()
    print("usage:", usage.snapshot())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    main(parser.parse_args().force)
