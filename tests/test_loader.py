"""Loader unit tests: text helpers and registration schema discovery."""
from __future__ import annotations

import pytest

from whsmun.loader._text import first_int, normalize_school_name
from whsmun.loader.registrations import RegistrationParseError, RegistrationSchema


# --- Text helpers ---

def test_normalize_collapses_punctuation_and_case():
    assert normalize_school_name("Madison Country Day") == "madisoncountryday"
    assert normalize_school_name("madison country day") == "madisoncountryday"
    assert normalize_school_name("St. John's High-School") == "stjohnshighschool"


def test_first_int_extracts_leading_or_embedded_integer():
    assert first_int("15") == 15
    assert first_int("15 delegates") == 15
    assert first_int("about 7") == 7


def test_first_int_rejects_no_integer():
    with pytest.raises(ValueError):
        first_int("none")


# --- Registration schema discovery ---

_VALID_HEADERS = [
    "Timestamp",
    "Name of School",
    "How large is your Delegation? (number)",
    "Besides the country you drew, how many more would you like?",
    "Would you like to send a delegate to the ICJ?",
    "Would you like to send a delegate to the JCC Side A?",
]


def test_schema_resolves_required_columns():
    schema = RegistrationSchema.from_headers(_VALID_HEADERS)
    assert schema.school_name == "Name of School"
    assert schema.delegation_size.startswith("How large")
    assert schema.extra_countries.startswith("Besides")


def test_schema_maps_committee_columns_to_canonicals():
    schema = RegistrationSchema.from_headers(_VALID_HEADERS)
    canonicals = set(schema.committee_columns.values())
    assert {"ICJ", "JCC A"} <= canonicals


def test_schema_missing_columns_listed_together():
    headers = ["Timestamp"]
    with pytest.raises(RegistrationParseError, match="missing required columns"):
        RegistrationSchema.from_headers(headers)


def test_schema_unrecognized_committee_column_raises():
    headers = list(_VALID_HEADERS) + ["Would you like to send a delegate to the Mystery Committee?"]
    with pytest.raises(RegistrationParseError, match="not recognized"):
        RegistrationSchema.from_headers(headers)


def test_schema_longest_label_wins():
    """'JCC Side A' must beat any shorter substring match."""
    headers = list(_VALID_HEADERS)
    schema = RegistrationSchema.from_headers(headers)
    jcc_a_header = next(h for h in headers if "JCC Side A" in h)
    assert schema.committee_columns[jcc_a_header] == "JCC A"
