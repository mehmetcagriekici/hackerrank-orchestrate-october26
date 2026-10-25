# helpers/

`normalize_text.py`: shared identifier normalization, used by both the link builder and the organizer so that links and evidence values are compared in the same form.

| Key | Normalization |
|---|---|
| `email` | trim + lowercase |
| `email_hash` | trim + lowercase |
| `name` | NFKC + casefold + collapse whitespace |
| `phone` | `+` followed by every digit; empty input stays empty, so it can never match everything |

`normalize(key, value)` picks the normalizer for a key; unknown keys are only trimmed.
