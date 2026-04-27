"""Load the lottery JSON: {school_name: country}."""
from __future__ import annotations

import json
from pathlib import Path

from whsmun.loader._text import normalize_school_name


def load_lottery(path: Path) -> dict[str, str]:
    """Return {normalized_school_name: country}.

    Names are normalized so loose JSON keys still match CSV rows.
    """
    raw = json.loads(path.read_text())
    return {normalize_school_name(school): country for school, country in raw.items()}
