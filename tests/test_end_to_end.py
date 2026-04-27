"""End-to-end: run cli.main against the real project inputs and verify the
output CSV's structural invariants (header, country count per school, no
country shared across schools)."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from whsmun import cli

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRATIONS = REPO_ROOT / "WHSMUN 2026 Cleaned.csv"
ROOMS = REPO_ROOT / "RoomNumbers.xlsx"
LOTTERY = REPO_ROOT / "lottery.json"
COUNTRIES = REPO_ROOT / "Countries.txt"

_REQUIRED_INPUTS = (REGISTRATIONS, ROOMS, LOTTERY, COUNTRIES)


@pytest.fixture
def cli_output(tmp_path: Path) -> list[dict[str, str]]:
    if not all(p.exists() for p in _REQUIRED_INPUTS):
        pytest.skip("real inputs not present in this checkout")
    output = tmp_path / "out.csv"
    rc = cli.main([
        "--registrations", str(REGISTRATIONS),
        "--rooms", str(ROOMS),
        "--lottery", str(LOTTERY),
        "--countries", str(COUNTRIES),
        "--output", str(output),
    ])
    assert rc == 0
    with output.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_header_includes_countries_column(cli_output):
    assert "Countries" in cli_output[0]


def test_each_row_has_country_count_matching_country_count_field(cli_output):
    for row in cli_output:
        countries = [c for c in row["Countries"].split(", ") if c]
        assert len(countries) == int(row["Country Count"]), (
            f"{row['School']}: 'Countries' has {len(countries)} entries, "
            f"'Country Count' is {row['Country Count']}"
        )


def test_lottery_country_appears_first_in_countries_field(cli_output):
    for row in cli_output:
        if not row["Lottery Country"]:
            continue
        countries = row["Countries"].split(", ")
        assert countries[0] == row["Lottery Country"], (
            f"{row['School']}: lottery country {row['Lottery Country']!r} not first "
            f"in Countries={row['Countries']!r}"
        )


def test_no_country_shared_across_schools(cli_output):
    seen: dict[str, str] = {}
    for row in cli_output:
        for country in (c for c in row["Countries"].split(", ") if c):
            if country in seen:
                pytest.fail(
                    f"country {country!r} assigned to both {seen[country]!r} "
                    f"and {row['School']!r}"
                )
            seen[country] = row["School"]
