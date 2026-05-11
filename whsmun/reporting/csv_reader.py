"""Read assignments.csv back into structured records for roster generation."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from whsmun.committees import ALL_COMMITTEES


@dataclass(frozen=True)
class SchoolRoster:
    name: str
    lottery_country: str | None
    countries: tuple[str, ...]
    placements: dict[str, int]


def read_assignments_csv(path: Path) -> list[SchoolRoster]:
    rosters: list[SchoolRoster] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lottery = row["Lottery Country"] or None
            countries_field = row["Countries"].strip()
            countries = tuple(c for c in countries_field.split(", ") if c) if countries_field else ()
            placements = {c: int(row[c]) for c in ALL_COMMITTEES}
            rosters.append(SchoolRoster(
                name=row["School"],
                lottery_country=lottery,
                countries=countries,
                placements=placements,
            ))
    return rosters
