"""Shared normalization for identifiers.

The gate's link builder and the organizer must both call these, so that
link values and evidence contents compare in the same form.
"""

import re
import unicodedata


def normalize_email(value: str) -> str:
    """Trim and lowercase an email address."""
    return value.strip().lower()


def normalize_hash(value: str) -> str:
    """Trim and lowercase a hex email hash."""
    return value.strip().lower()


def normalize_name(value: str) -> str:
    """Unicode-normalize, casefold, and collapse whitespace in a person's name."""
    value = unicodedata.normalize("NFKC", value)
    return re.sub(r"\s+", " ", value).strip().casefold()


def normalize_phone(value: str) -> str:
    """Bring a phone number into the single form used for matching."""
    digits = re.sub(r'\D', '', value)
    if not digits:
        return ""
    return f"+{digits}"

NORMALIZERS = {
    "email": normalize_email,
    "email_hash": normalize_hash,
    "name": normalize_name,
    "phone": normalize_phone,
}


def normalize(key: str, value: str) -> str:
    """Normalize a value by its link key; unknown keys are only trimmed."""
    fn = NORMALIZERS.get(key)
    return fn(value) if fn else value.strip()
