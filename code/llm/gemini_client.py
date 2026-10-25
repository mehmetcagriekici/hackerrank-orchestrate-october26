"""Minimal Gemini REST client returning parsed JSON, with retry on rate limits."""

import base64
import json
import os
import time
import urllib.error
import urllib.request

from llm import usage
from llm.env import load_env

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiClient:
    def __init__(self, model: str, max_retries: int = 5) -> None:
        load_env()
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not set (add it to .env or the environment)")
        self.model = model
        self.max_retries = max_retries

    def generate_json(self, system: str, prompt: str, attachments: tuple[tuple[str, bytes], ...] = ()) -> object:
        """attachments: (mime_type, raw bytes) pairs sent inline, e.g. PNG or PDF evidence."""
        parts = [{"inline_data": {"mime_type": mime, "data": base64.b64encode(raw).decode("ascii")}}
                 for mime, raw in attachments] + [{"text": prompt}]
        body = json.dumps({
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }).encode("utf-8")
        request = urllib.request.Request(
            API_URL.format(model=self.model), data=body, method="POST",
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
        )

        data: dict = {}
        for attempt in range(self.max_retries):
            try:
                with urllib.request.urlopen(request, timeout=180) as response:
                    data = json.load(response)
                break
            except urllib.error.HTTPError as error:
                if error.code in (429, 500, 503) and attempt < self.max_retries - 1:
                    time.sleep(min(60, 5 * 2 ** attempt))
                    continue
                raise RuntimeError(f"Gemini {self.model} HTTP {error.code}: {error.read()[:300]!r}") from error
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(5 * 2 ** attempt)

        meta = data.get("usageMetadata", {})
        usage.record("google", self.model, meta.get("promptTokenCount", 0),
                     meta.get("candidatesTokenCount", 0), meta.get("thoughtsTokenCount", 0))
        text = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
        return json.loads(text)
