"""Load the Google Forms registration CSV into `School` objects.

The CSV format is fixed by Google Forms — its column headers contain the
question text, and we identify columns by substring match against
`CSV_LABEL_TO_COMMITTEE`. `RegistrationSchema` discovers and validates
all required columns up front so a missing/renamed question fails loudly
once instead of partway through the rows.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from whsmun.committees import CSV_LABEL_TO_COMMITTEE
from whsmun.loader._text import first_int, normalize_school_name
from whsmun.models import School


class RegistrationParseError(Exception):
    """Raised when a registration CSV row cannot be parsed."""


_DELEGATION_SIZE_PREFIX = "How large is your Delegation"
_EXTRA_COUNTRIES_PREFIX = "Besides the country you drew"
_COMMITTEE_QUESTION_TOKEN = "send a delegate to"
_SCHOOL_NAME_HEADER = "Name of School"


@dataclass(frozen=True)
class RegistrationSchema:
    """Resolved CSV column names for the registration form."""
    school_name: str
    delegation_size: str
    extra_countries: str
    committee_columns: dict[str, str]  # CSV header → canonical committee name

    @classmethod
    def from_headers(cls, headers: list[str]) -> RegistrationSchema:
        missing: list[str] = []

        if _SCHOOL_NAME_HEADER not in headers:
            missing.append(_SCHOOL_NAME_HEADER)

        delegation_size = _find_header(headers, _DELEGATION_SIZE_PREFIX)
        if delegation_size is None:
            missing.append(f"<starts with {_DELEGATION_SIZE_PREFIX!r}>")

        extra_countries = _find_header(headers, _EXTRA_COUNTRIES_PREFIX)
        if extra_countries is None:
            missing.append(f"<starts with {_EXTRA_COUNTRIES_PREFIX!r}>")

        if missing:
            raise RegistrationParseError(
                f"registration CSV missing required columns: {missing}"
            )

        committee_columns = _map_committee_columns(headers)
        return cls(
            school_name=_SCHOOL_NAME_HEADER,
            delegation_size=delegation_size,  # type: ignore[arg-type]
            extra_countries=extra_countries,  # type: ignore[arg-type]
            committee_columns=committee_columns,
        )


def _find_header(headers: list[str], prefix: str) -> str | None:
    return next((h for h in headers if h.startswith(prefix)), None)


def _map_committee_columns(headers: list[str]) -> dict[str, str]:
    """Match each committee-question column header to a canonical committee.

    Labels are tried longest-first so 'JCC Side A' wins over a hypothetical
    bare 'JCC' substring.
    """
    labels_by_length = sorted(CSV_LABEL_TO_COMMITTEE, key=len, reverse=True)
    mapping: dict[str, str] = {}
    for header in headers:
        if _COMMITTEE_QUESTION_TOKEN not in header.lower():
            continue
        header_lower = header.lower()
        for label in labels_by_length:
            if label.lower() in header_lower:
                mapping[header] = CSV_LABEL_TO_COMMITTEE[label]
                break
        else:
            raise RegistrationParseError(f"CSV committee column not recognized: {header!r}")
    return mapping


def load_schools(csv_path: Path, lottery: dict[str, str]) -> list[School]:
    """Parse registration rows into `School` objects in registration order."""
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return []

    schema = RegistrationSchema.from_headers(list(rows[0].keys()))
    return [_row_to_school(idx, row, schema, lottery) for idx, row in enumerate(rows)]


def _row_to_school(
    idx: int,
    row: dict[str, str],
    schema: RegistrationSchema,
    lottery: dict[str, str],
) -> School:
    name = (row.get(schema.school_name) or "").strip()
    if not name:
        raise RegistrationParseError(f"row {idx}: missing {schema.school_name!r}")

    try:
        total = first_int(row[schema.delegation_size])
    except ValueError as e:
        raise RegistrationParseError(f"row {idx} ({name}): {e}") from e

    extras_cell = (row[schema.extra_countries] or "").strip()
    try:
        extras = first_int(extras_cell) if extras_cell else 0
    except ValueError as e:
        raise RegistrationParseError(f"row {idx} ({name}): {e}") from e

    yes_committees = tuple(
        committee
        for header, committee in schema.committee_columns.items()
        if (row.get(header) or "").strip().lower() == "yes"
    )
    return School(
        row_index=idx,
        name=name,
        total_delegates=total,
        extra_countries=extras,
        lottery_country=lottery.get(normalize_school_name(name)),
        yes_committees=yes_committees,
    )
