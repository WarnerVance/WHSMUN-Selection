"""Print a summary to stdout and write per-school assignments to CSV."""
from __future__ import annotations

import csv
from pathlib import Path

from committees import ALL_COMMITTEES
from models import Assignment


def write_assignments_csv(path: Path, assignments: list[Assignment]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "School", "Lottery Country", "Country Count", "Total Delegates",
            *ALL_COMMITTEES, "Assigned", "Dropped",
        ])
        for a in assignments:
            w.writerow([
                a.school.name,
                a.school.lottery_country or "",
                a.school.country_count,
                a.school.total_delegates,
                *(a.placements.get(c, 0) for c in ALL_COMMITTEES),
                a.total_assigned,
                a.total_dropped,
            ])


def print_summary(
    assignments: list[Assignment],
    capacities: dict[str, int],
    used: dict[str, int],
) -> None:
    print(f"Assigned {len(assignments)} school(s).\n")
    print(f"{'Committee':<22} {'Used':>6} {'Cap':>6}  Status")
    print("-" * 48)
    for committee in ALL_COMMITTEES:
        cap = capacities.get(committee, 0)
        u = used.get(committee, 0)
        status = "FULL" if cap and u >= cap else ""
        print(f"{committee:<22} {u:>6} {cap:>6}  {status}")

    drops = [(a, c, n) for a in assignments for c, n in a.dropped.items()]
    print("\nFCFS overflow drops:")
    if not drops:
        print("  (none)")
    else:
        for a, c, n in drops:
            print(f"  {a.school.name}: -{n} from {c}")