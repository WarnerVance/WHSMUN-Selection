"""FCFS strategy: capacity overflow goes into `dropped`, not raised."""
from __future__ import annotations

import pytest

from whsmun.assignment import AssignmentError, FCFSStrategy
from whsmun.models import School


def _school(name: str, total: int, yes: tuple[str, ...]) -> School:
    return School(
        row_index=0, name=name, total_delegates=total,
        extra_countries=0, lottery_country="Foo", yes_committees=yes,
    )


def _full_capacities(**overrides: int) -> dict[str, int]:
    base = {
        "SOCHUM": 100, "DISEC": 100, "ECOFIN": 100, "SPECPOL": 100, "GA Ad-Hoc": 100,
        "EU": 5, "AU": 5, "ASEAN": 5, "ICJ": 5,
        "Spec 1": 5, "Spec 2": 5, "Spec 3": 5,
        "HCC": 5, "UNSC": 5, "JCC A": 5, "JCC B": 5,
        "Ad-Hoc": 5, "Wisconsin Crisis": 5,
    }
    base.update(overrides)
    return base


def test_first_school_fills_committee_second_school_overflows():
    capacities = _full_capacities(ICJ=1)
    schools = [
        _school("First",  total=1, yes=("ICJ",)),
        _school("Second", total=1, yes=("ICJ",)),
    ]
    result = FCFSStrategy().assign(schools, capacities)

    first, second = result.assignments
    assert first.placements == {"ICJ": 1}
    assert first.dropped == {}
    assert second.placements == {}
    assert second.dropped == {"ICJ": 1}
    assert result.used["ICJ"] == 1


def test_partial_overflow():
    """When part of a request fits, place what fits and drop the rest."""
    capacities = _full_capacities(SPECPOL=1)
    schools = [_school("Alpha", total=3, yes=())]  # R%7=3 → SPECPOL=1, ECOFIN=1, Ad-Hoc=1
    result = FCFSStrategy().assign(schools, capacities)

    a = result.assignments[0]
    assert a.placements["SPECPOL"] == 1
    assert "SPECPOL" not in a.dropped


def test_used_totals_match_placements():
    capacities = _full_capacities()
    schools = [
        _school("A", total=3, yes=("ICJ",)),
        _school("B", total=2, yes=("EU",)),
    ]
    result = FCFSStrategy().assign(schools, capacities)
    summed = {c: 0 for c in capacities}
    for a in result.assignments:
        for committee, n in a.placements.items():
            summed[committee] += n
    assert summed == result.used


def test_unknown_committee_in_capacities_raises():
    capacities = {"SOCHUM": 10}  # missing every other committee
    schools = [_school("X", total=1, yes=("ICJ",))]
    with pytest.raises(AssignmentError, match="no capacity"):
        FCFSStrategy().assign(schools, capacities)
