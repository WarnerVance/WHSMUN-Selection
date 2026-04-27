"""Load the Countries.txt pool from which non-lottery country slots are drawn."""
from __future__ import annotations

from pathlib import Path


def load_countries(path: Path) -> list[str]:
    """Return countries in file order. Blank lines are skipped; whitespace
    is stripped. Duplicates raise ValueError so the operator can fix them.
    """
    countries: list[str] = []
    seen: set[str] = set()
    duplicates: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        country = raw.strip()
        if not country:
            continue
        if country in seen:
            duplicates.append(country)
            continue
        seen.add(country)
        countries.append(country)
    if duplicates:
        raise ValueError(f"duplicate entries in {path.name}: {duplicates}")
    return countries
