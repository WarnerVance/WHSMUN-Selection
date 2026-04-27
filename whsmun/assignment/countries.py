"""Assign concrete countries to each school's country slots.

Each school needs `school.country_count` countries to fill its GA slots.
One of those is the lottery country (if drawn) and stays fixed; the rest
are pulled from `Countries.txt` in file order. No two schools share a
country — lottery countries are reserved before the pool is walked, and
any pool entry already taken by a lottery (or earlier school) is skipped.
"""
from __future__ import annotations

from typing import Sequence

from whsmun.assignment.errors import AssignmentError
from whsmun.models import School


def assign_countries(
    schools: Sequence[School],
    country_pool: Sequence[str],
) -> dict[int, tuple[str, ...]]:
    """Return {school.row_index: tuple of countries} in lottery-first order.

    Raises `AssignmentError` if the pool runs out before every school's
    extra-country quota is met.
    """
    used: set[str] = {s.lottery_country for s in schools if s.lottery_country}

    pool_iter = iter(country_pool)
    result: dict[int, tuple[str, ...]] = {}

    for school in schools:
        countries: list[str] = []
        if school.lottery_country:
            countries.append(school.lottery_country)

        for _ in range(school.extra_countries):
            country = _next_unused(pool_iter, used, school)
            used.add(country)
            countries.append(country)

        result[school.row_index] = tuple(countries)

    return result


def _next_unused(pool_iter, used: set[str], school: School) -> str:
    for candidate in pool_iter:
        if candidate not in used:
            return candidate
    raise AssignmentError(
        f"{school.name}: ran out of countries in the pool while filling "
        f"extra-country slots"
    )
