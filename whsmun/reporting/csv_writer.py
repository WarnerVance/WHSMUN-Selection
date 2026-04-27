"""Write per-school assignments to CSV."""
from __future__ import annotations

import csv
from pathlib import Path

from whsmun.committees import ALL_COMMITTEES
from whsmun.models import Assignment


_HEADER: tuple[str, ...] = (
    "School", "Lottery Country", "Country Count", "Total Delegates",
    *ALL_COMMITTEES, "Assigned", "Dropped",
)


def write_assignments_csv(path: Path, assignments: list[Assignment]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(_HEADER)
        for assignment in assignments:
            writer.writerow(_row_for(assignment))


def _row_for(a: Assignment) -> list[object]:
    return [
        a.school.name,
        a.school.lottery_country or "",
        a.school.country_count,
        a.school.total_delegates,
        *(a.placements.get(c, 0) for c in ALL_COMMITTEES),
        a.total_assigned,
        a.total_dropped,
    ]
