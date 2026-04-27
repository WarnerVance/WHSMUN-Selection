"""Private text-normalization helpers shared across loaders."""
from __future__ import annotations

import re


def normalize_school_name(name: str) -> str:
    """Lowercase + strip non-alphanumerics so 'Madison Country Day' and
    'madison country day' compare equal."""
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def first_int(text: str) -> int:
    """Extract the first integer from a free-text cell, e.g. '15 delegates' → 15."""
    match = re.search(r"-?\d+", text or "")
    if not match:
        raise ValueError(f"no integer in {text!r}")
    return int(match.group())
