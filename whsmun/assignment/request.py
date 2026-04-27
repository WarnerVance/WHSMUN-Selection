"""Compute a school's requested placements (capacity-unaware).

The output of `compute_requested` is what the school *would* be assigned if
no committee were ever full. The strategy layer then applies capacity limits.

# How GA delegates are distributed

After honoring single-seat Yes-answers (1 delegate each), the school has
`R` delegates left for the 5 GA committees. We distribute those as
**country slots**: each slot seats one of the school's `C` countries in
one GA committee. Slots cost 2 delegates in double-del committees
(SOCHUM, DISEC) and 1 delegate elsewhere — so the per-committee total
weights sum to 2+2+1+1+1 = 7 per "round" of slots across all 5 GAs.

We give every GA `R // 7` base slots, then distribute the `R % 7`
leftover delegates using a hand-tuned table (`_LEFTOVER_PATTERNS`) that
encodes WHSMUN's preferences for which committees absorb leftovers.
The table is small enough to read at a glance and is verified at import
time against the committee weights.
"""
from __future__ import annotations

from typing import Final

from whsmun.assignment.errors import AssignmentError
from whsmun.committees import GA_COMMITTEES, WEIGHT
from whsmun.models import PlacementMap, School

# Additional country slots to add to (SOCHUM, DISEC, ECOFIN, SPECPOL, GA Ad-Hoc)
# beyond the `R // 7` base slots already given to every GA. The keys are R % 7;
# the tuple weights (2,2,1,1,1) sum to the key. Choices are WHSMUN's preferences
# for which committees absorb leftovers — see _validate_patterns for the
# soundness check that runs at import time.
_LEFTOVER_PATTERNS: Final[dict[int, tuple[int, int, int, int, int]]] = {
    0: (0, 0, 0, 0, 0),  # nothing leftover
    1: (0, 0, 1, 0, 0),  # 1 del → ECOFIN
    2: (0, 0, 1, 1, 0),  # 2 dels → ECOFIN + SPECPOL
    3: (0, 0, 1, 1, 1),  # 3 dels → all single-del GAs
    4: (1, 0, 0, 1, 1),  # 4 dels → SOCHUM (2) + SPECPOL + Ad-Hoc; skip ECOFIN
    5: (1, 0, 1, 1, 1),  # 5 dels → SOCHUM (2) + all single-dels
    6: (1, 1, 0, 1, 1),  # 6 dels → both double-dels (4) + SPECPOL + Ad-Hoc
}


def _validate_patterns() -> None:
    """Verify each pattern's weighted delegate count matches its R%7 key."""
    weights = tuple(WEIGHT[c] for c in GA_COMMITTEES)
    for remainder, slots in _LEFTOVER_PATTERNS.items():
        if len(slots) != len(GA_COMMITTEES):
            raise ValueError(f"_LEFTOVER_PATTERNS[{remainder}] has wrong length")
        total_dels = sum(s * w for s, w in zip(slots, weights, strict=True))
        if total_dels != remainder:
            raise ValueError(
                f"_LEFTOVER_PATTERNS[{remainder}] sums to {total_dels} dels, expected {remainder}"
            )


_validate_patterns()


def compute_requested(school: School) -> PlacementMap:
    """Return what the school would be assigned with infinite capacity.

    Phase 1: 1 delegate per single-seat 'Yes' answer.
    Phase 2: distribute the remaining delegates across the 5 GA committees
    in country slots (see module docstring).
    """
    if school.total_delegates < 0:
        raise AssignmentError(f"{school.name}: negative delegation size")

    placements: PlacementMap = {c: 1 for c in school.yes_committees}
    singles_used = len(placements)

    if singles_used > school.total_delegates:
        raise AssignmentError(
            f"{school.name}: requested {singles_used} single-seat committees but delegation "
            f"is only {school.total_delegates} delegates"
        )

    remaining = school.total_delegates - singles_used
    if remaining == 0:
        return placements

    countries = school.country_count
    if countries <= 0:
        raise AssignmentError(
            f"{school.name}: {remaining} delegates left for GA but represents 0 countries"
        )

    ga_capacity = 7 * countries
    if remaining > ga_capacity:
        raise AssignmentError(
            f"{school.name}: {remaining} delegates left for GA but only {ga_capacity} GA seats "
            f"available with {countries} countries"
        )

    base_slots = remaining // 7
    leftover = remaining - base_slots * 7
    extra_slots = _LEFTOVER_PATTERNS[leftover]

    for committee, extra in zip(GA_COMMITTEES, extra_slots, strict=True):
        slots = base_slots + extra
        if slots > countries:  # defensive: ga_capacity check above should prevent this
            raise AssignmentError(
                f"{school.name}: {committee} would need {slots} country slots but only "
                f"{countries} available"
            )
        delegates = slots * WEIGHT[committee]
        if delegates > 0:
            placements[committee] = delegates

    return placements
