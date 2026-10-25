"""Gate LLM: does each request text authorize deletion?

Unique texts are sent in batches as {key: text}; answers are cached by text
hash so reruns are deterministic and spend no quota. A key the model leaves
out is treated as not authorized (NOT_APPLICABLE), and reported.
"""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROMPT_FILE = ROOT / "code" / "prompts" / "gate_system.md"
CACHE_FILE = ROOT / ".cache" / "gate_decisions.json"


def _text_key(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]


def _load_cache() -> dict[str, bool]:
    return json.loads(CACHE_FILE.read_text(encoding="utf-8")) if CACHE_FILE.exists() else {}


def _save_cache(cache: dict[str, bool]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")


def authorize(texts: list[str], client, batch_size: int = 60) -> dict[str, bool]:
    """Return {text: authorized} for every input text."""
    cache = _load_cache()
    pending = sorted({_text_key(t): t for t in texts if _text_key(t) not in cache}.items())
    system = PROMPT_FILE.read_text(encoding="utf-8")

    for start in range(0, len(pending), batch_size):
        batch = dict(pending[start:start + batch_size])
        answer = client.generate_json(system, json.dumps(batch, ensure_ascii=False))
        missing = [k for k in batch if not isinstance(answer.get(k), bool)]
        if missing:
            print(f"gate: {len(missing)} key(s) missing or non-boolean in batch; treated as NOT_APPLICABLE")
        for key in batch:
            cache[key] = answer.get(key) is True
        _save_cache(cache)

    return {t: cache.get(_text_key(t), False) for t in texts}
