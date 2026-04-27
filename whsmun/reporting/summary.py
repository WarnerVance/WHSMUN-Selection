"""Print an end-of-run summary to stdout."""
from __future__ import annotations

from typing import Iterable, Mapping

from whsmun.committees import ALL_COMMITTEES
from whsmun.models import Assignment


def print_summary(
    assignments: list[Assignment],
    capacities: Mapping[str, int],
    used: Mapping[str, int],
) -> None:
    print(f"Assigned {len(assignments)} school(s).\n")
    for line in _format_capacity_table(capacities, used):
        print(line)
    print()
    for line in _format_drops(assignments):
        print(line)


def _format_capacity_table(
    capacities: Mapping[str, int], used: Mapping[str, int]
) -> Iterable[str]:
    yield f"{'Committee':<22} {'Used':>6} {'Cap':>6}  Status"
    yield "-" * 48
    for committee in ALL_COMMITTEES:
        cap = capacities.get(committee, 0)
        u = used.get(committee, 0)
        status = "FULL" if cap and u >= cap else ""
        yield f"{committee:<22} {u:>6} {cap:>6}  {status}"


def _format_drops(assignments: list[Assignment]) -> Iterable[str]:
    yield "FCFS overflow drops:"
    drops = [(a, c, n) for a in assignments for c, n in a.dropped.items()]
    if not drops:
        yield "  (none)"
        return
    for assignment, committee, n in drops:
        yield f"  {assignment.school.name}: -{n} from {committee}"
