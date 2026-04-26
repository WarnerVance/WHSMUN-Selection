"""Compute per-school committee assignments and aggregate against capacities."""
from __future__ import annotations

from typing import Final

from committees import DOUBLE_DEL, GA_COMMITTEES
from models import Assignment, School


class AssignmentError(Exception):
    """Raised when a school's request cannot be fulfilled."""


# Per-committee delegate weight: double-del committees consume 2 dels per
# country slot, single-del committees consume 1.
_WEIGHT: Final[dict[str, int]] = {c: (2 if c in DOUBLE_DEL else 1) for c in GA_COMMITTEES}

# After placing `R // 7` country slots in every GA committee, the leftover R%7
# delegates need to be distributed without breaking the even-count constraint
# on SOCHUM/DISEC. Each tuple is the *additional* country slots to add to
# (SOCHUM, DISEC, ECOFIN, SPECPOL, GA Ad-Hoc), in that order. The dels they
# add (2,2,1,1,1) sum to the leftover key. Ordering favors single-del
# committees so that as many GA committees as possible receive a delegate.
_LEFTOVER_PATTERNS: Final[dict[int, tuple[int, int, int, int, int]]] = {
    0: (0, 0, 0, 0, 0),
    1: (0, 0, 1, 0, 0),
    2: (0, 0, 1, 1, 0),
    3: (0, 0, 1, 1, 1),
    4: (1, 0, 0, 1, 1),
    5: (1, 0, 1, 1, 1),
    6: (1, 1, 0, 1, 1),
}


def compute_requested(school: School) -> dict[str, int]:
    """Compute the school's requested placements (no capacity awareness).

    Phase 1: 1 delegate per single-seat 'Yes'.
    Phase 2: distribute the remainder across the 5 GA committees in
    "country slots". Each slot represents one of the school's countries
    being seated in one GA committee, and is worth 2 dels in the double-del
    committees (SOCHUM, DISEC) and 1 del elsewhere. Per-committee slot cap
    is C (the school's country count), so SOCHUM/DISEC counts are always
    multiples of 2 (i.e., even).
    """
    if school.total_delegates < 0:
        raise AssignmentError(f"{school.name}: negative delegation size")

    placements: dict[str, int] = {c: 1 for c in school.yes_committees}
    s = len(placements)

    if s > school.total_delegates:
        raise AssignmentError(
            f"{school.name}: requested {s} single-seat committees but delegation is only "
            f"{school.total_delegates} delegates"
        )

    remaining = school.total_delegates - s
    if remaining == 0:
        return placements

    c = school.country_count
    if c <= 0:
        raise AssignmentError(
            f"{school.name}: {remaining} delegates left for GA but represents 0 countries"
        )

    ga_max = 7 * c
    if remaining > ga_max:
        raise AssignmentError(
            f"{school.name}: {remaining} delegates left for GA but only {ga_max} GA seats "
            f"available with {c} countries"
        )

    base_slots = remaining // 7
    leftover = remaining - base_slots * 7
    additions = _LEFTOVER_PATTERNS[leftover]

    for committee, add in zip(GA_COMMITTEES, additions, strict=True):
        slots = base_slots + add
        if slots > c:  # defensive: the ga_max check above should prevent this
            raise AssignmentError(
                f"{school.name}: {committee} would need {slots} country slots but only {c} available"
            )
        dels = slots * _WEIGHT[committee]
        if dels > 0:
            placements[committee] = dels
    return placements


def assign_all(
    schools: list[School],
    capacities: dict[str, int],
) -> tuple[list[Assignment], dict[str, int]]:
    """Process schools in registration order. Single-school infeasibility halts
    the whole run. Committee-capacity overflows are FCFS: later schools that
    requested a full committee get those delegates dropped and reported."""
    used: dict[str, int] = {c: 0 for c in capacities}
    assignments: list[Assignment] = []

    for school in schools:
        requested = compute_requested(school)
        placements: dict[str, int] = {}
        dropped: dict[str, int] = {}
        for committee, count in requested.items():
            cap = capacities.get(committee)
            if cap is None:
                raise AssignmentError(
                    f"{school.name}: assigned to committee {committee!r} which has no capacity "
                    f"defined in RoomNumbers.xlsx"
                )
            available = max(cap - used[committee], 0)
            placed = min(count, available)
            if placed:
                placements[committee] = placed
                used[committee] += placed
            if placed < count:
                dropped[committee] = count - placed
        assignments.append(Assignment(school=school, placements=placements, dropped=dropped))

    return assignments, used