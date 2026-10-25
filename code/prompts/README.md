# prompts/

| File | Used by | Purpose |
|---|---|---|
| `gate_system.md` | `gate/authorize.py` | Classifies whether each request text, in any language, authorizes deletion. Input and output are JSON maps of key → text / boolean, and the model must answer every key. |
| `extract_system.md` | `organizer/extract_media.py` | Transcribes screenshots and PDFs into records (`resource_id`, identifiers, statuses and timestamps exactly as shown). |

Prompts contain no organizer-only answers and no hardcoded sample labels.
