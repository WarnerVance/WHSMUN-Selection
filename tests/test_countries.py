"""Tests for Countries.txt loading and the country-assignment pass."""
from __future__ import annotations

import pytest

from whsmun.assignment import AssignmentError, assign_countries
from whsmun.loader.countries import load_countries
from whsmun.models import School


def _school(
    row_index: int,
    name: str,
    *,
    extras: int,
    lottery: str | None,
) -> School:
    return School(
        row_index=row_index,
        name=name,
        total_delegates=10,
        extra_countries=extras,
        lottery_country=lottery,
        yes_committees=(),
    )


# --- load_countries ---

def test_load_countries_strips_blank_lines_and_whitespace(tmp_path):
    path = tmp_path / "c.txt"
    path.write_text("Malaysia\n\n  Portugal  \nUkraine\n\n", encoding="utf-8")
    assert load_countries(path) == ["Malaysia", "Portugal", "Ukraine"]


def test_load_countries_rejects_duplicates(tmp_path):
    path = tmp_path / "c.txt"
    path.write_text("Malaysia\nPortugal\nMalaysia\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_countries(path)


# --- assign_countries ---

def test_lottery_country_preserved_and_first():
    schools = [_school(0, "Alpha", extras=2, lottery="France")]
    pool = ["Malaysia", "Portugal", "Ukraine"]
    result = assign_countries(schools, pool)
    assert result[0] == ("France", "Malaysia", "Portugal")


def test_no_lottery_pulls_only_from_pool():
    schools = [_school(0, "Alpha", extras=3, lottery=None)]
    pool = ["Malaysia", "Portugal", "Ukraine", "Chad"]
    assert assign_countries(schools, pool)[0] == ("Malaysia", "Portugal", "Ukraine")


def test_no_two_schools_share_a_country():
    schools = [
        _school(0, "Alpha", extras=2, lottery="France"),
        _school(1, "Beta",  extras=2, lottery="Germany"),
    ]
    pool = ["Malaysia", "Portugal", "Ukraine", "Chad"]
    result = assign_countries(schools, pool)
    flat = [c for tup in result.values() for c in tup]
    assert len(flat) == len(set(flat))


def test_pool_skips_lottery_country_overlap():
    """If a lottery country also appears in the pool, the pool entry is skipped."""
    schools = [
        _school(0, "Alpha", extras=1, lottery="Portugal"),
        _school(1, "Beta",  extras=2, lottery=None),
    ]
    pool = ["Malaysia", "Portugal", "Ukraine", "Chad"]
    result = assign_countries(schools, pool)
    assert result[0] == ("Portugal", "Malaysia")
    assert result[1] == ("Ukraine", "Chad")


def test_zero_extras_yields_only_lottery():
    schools = [_school(0, "Alpha", extras=0, lottery="France")]
    assert assign_countries(schools, ["Malaysia"])[0] == ("France",)


def test_zero_extras_no_lottery_yields_empty():
    schools = [_school(0, "Alpha", extras=0, lottery=None)]
    assert assign_countries(schools, ["Malaysia"])[0] == ()


def test_pool_exhaustion_raises_with_school_name():
    schools = [
        _school(0, "Alpha", extras=2, lottery=None),
        _school(1, "Beta",  extras=2, lottery=None),
    ]
    pool = ["Malaysia", "Portugal", "Ukraine"]  # only 3 — Beta runs out
    with pytest.raises(AssignmentError, match="Beta"):
        assign_countries(schools, pool)


def test_assignment_order_follows_registration_order():
    schools = [
        _school(0, "First",  extras=1, lottery=None),
        _school(1, "Second", extras=1, lottery=None),
    ]
    pool = ["Malaysia", "Portugal"]
    result = assign_countries(schools, pool)
    assert result[0] == ("Malaysia",)
    assert result[1] == ("Portugal",)
