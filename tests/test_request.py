"""Pin the behavior of compute_requested for every R%7 leftover and error path."""
from __future__ import annotations

import pytest

from whsmun.assignment import AssignmentError, compute_requested
from whsmun.models import School


def _school(
    total: int,
    *,
    countries: int = 1,
    yes: tuple[str, ...] = (),
    name: str = "Test School",
) -> School:
    return School(
        row_index=0,
        name=name,
        total_delegates=total,
        extra_countries=countries - 1,  # +1 for lottery
        lottery_country="Foo",
        yes_committees=yes,
    )


# --- Leftover-pattern pinning: one school per R%7 case, C=1, no singles. ---

def test_leftover_zero_no_dels():
    assert compute_requested(_school(0)) == {}


def test_leftover_one_del_goes_to_ecofin():
    assert compute_requested(_school(1)) == {"ECOFIN": 1}


def test_leftover_two_dels_ecofin_and_specpol():
    assert compute_requested(_school(2)) == {"ECOFIN": 1, "SPECPOL": 1}


def test_leftover_three_dels_all_single_del_gas():
    assert compute_requested(_school(3)) == {
        "ECOFIN": 1, "SPECPOL": 1, "GA Ad-Hoc": 1,
    }


def test_leftover_four_dels_sochum_specpol_adhoc():
    assert compute_requested(_school(4)) == {
        "SOCHUM": 2, "SPECPOL": 1, "GA Ad-Hoc": 1,
    }


def test_leftover_five_dels_sochum_plus_all_single_del_gas():
    assert compute_requested(_school(5)) == {
        "SOCHUM": 2, "ECOFIN": 1, "SPECPOL": 1, "GA Ad-Hoc": 1,
    }


def test_leftover_six_dels_both_double_del_plus_specpol_adhoc():
    assert compute_requested(_school(6)) == {
        "SOCHUM": 2, "DISEC": 2, "SPECPOL": 1, "GA Ad-Hoc": 1,
    }


def test_full_round_one_country():
    """7 dels with 1 country → 1 slot in every GA committee."""
    assert compute_requested(_school(7)) == {
        "SOCHUM": 2, "DISEC": 2, "ECOFIN": 1, "SPECPOL": 1, "GA Ad-Hoc": 1,
    }


def test_two_full_rounds_two_countries():
    """14 dels with 2 countries → 2 slots in every GA committee."""
    assert compute_requested(_school(14, countries=2)) == {
        "SOCHUM": 4, "DISEC": 4, "ECOFIN": 2, "SPECPOL": 2, "GA Ad-Hoc": 2,
    }


# --- Single-seat handling ---

def test_single_seat_yes_consumes_one_delegate_each():
    placements = compute_requested(_school(3, yes=("ICJ", "EU"), countries=1))
    # 2 singles + 1 leftover for GA → ECOFIN
    assert placements == {"ICJ": 1, "EU": 1, "ECOFIN": 1}


def test_all_delegates_used_by_singles():
    placements = compute_requested(_school(2, yes=("ICJ", "EU")))
    assert placements == {"ICJ": 1, "EU": 1}


# --- Error paths ---

def test_negative_delegates_raises():
    with pytest.raises(AssignmentError, match="negative"):
        compute_requested(_school(-1))


def test_too_many_singles_raises():
    with pytest.raises(AssignmentError, match="single-seat"):
        compute_requested(_school(1, yes=("ICJ", "EU")))


def test_zero_countries_with_ga_leftover_raises():
    school = School(
        row_index=0, name="X", total_delegates=3,
        extra_countries=0, lottery_country=None, yes_committees=(),
    )
    with pytest.raises(AssignmentError, match="0 countries"):
        compute_requested(school)


def test_ga_remainder_exceeds_capacity_raises():
    # 8 dels with 1 country: ga_capacity=7, but remaining=8 > 7
    with pytest.raises(AssignmentError, match="GA seats"):
        compute_requested(_school(8, countries=1))
