"""Assignment strategies — policies for resolving capacity conflicts.

A strategy takes the schools and committee capacities and produces an
`AssignmentResult`. New policies (priority-based, randomized, optimization)
can be added by implementing the `AssignmentStrategy` protocol.
"""
from __future__ import annotations

from typing import Mapping, Protocol

from whsmun.assignment.errors import AssignmentError
from whsmun.assignment.request import compute_requested
from whsmun.models import Assignment, AssignmentResult, PlacementMap, School


class AssignmentStrategy(Protocol):
    def assign(self, schools: list[School], capacities: Mapping[str, int]) -> AssignmentResult: ...


class FCFSStrategy:
    """First-come-first-served: process schools in registration order.

    A single school's infeasible request halts the whole run (data bug).
    Committee-capacity overflows are NOT errors — overflowing delegates are
    recorded in `Assignment.dropped` so the operator can react.
    """

    def assign(
        self, schools: list[School], capacities: Mapping[str, int]
    ) -> AssignmentResult:
        used: dict[str, int] = {c: 0 for c in capacities}
        assignments: list[Assignment] = []

        for school in schools:
            requested = compute_requested(school)
            placements, dropped = self._apply_capacity(school, requested, capacities, used)
            assignments.append(
                Assignment(school=school, placements=placements, dropped=dropped)
            )

        return AssignmentResult(assignments=assignments, used=used)

    @staticmethod
    def _apply_capacity(
        school: School,
        requested: PlacementMap,
        capacities: Mapping[str, int],
        used: dict[str, int],
    ) -> tuple[PlacementMap, PlacementMap]:
        placements: PlacementMap = {}
        dropped: PlacementMap = {}
        for committee, count in requested.items():
            if committee not in capacities:
                raise AssignmentError(
                    f"{school.name}: assigned to committee {committee!r} which has no "
                    f"capacity defined in RoomNumbers.xlsx"
                )
            available = max(capacities[committee] - used[committee], 0)
            placed = min(count, available)
            if placed:
                placements[committee] = placed
                used[committee] += placed
            if placed < count:
                dropped[committee] = count - placed
        return placements, dropped
