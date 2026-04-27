# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Run

```bash
uv run python -m whsmun
```

Reads three input files relative to the repo root and writes `assignments.csv`:
- `WHSMUN 2026 Cleaned.csv` — Google Forms export (cleaned), one row per school
- `RoomNumbers.xlsx` — sheet `Committee Numbers`, columns `(dept, committee, count, ...)`
- `lottery.json` — `{school_name: country}` for schools that drew a country in the lottery

Override any of the four paths with `--registrations`, `--rooms`, `--lottery`, `--output`.

Python 3.14+. Runtime dep: `openpyxl`. Dev dep: `pytest` (`pip install -e ".[dev]"`).

## Layout

```
whsmun/                   the package
  cli.py                  argparse entry; `python -m whsmun` runs this
  committees.py           Committee dataclass + COMMITTEES registry (single source of truth)
  models.py               School, Assignment, AssignmentResult, PlacementMap
  loader/
    lottery.py            lottery.json → {normalized_name: country}
    capacities.py         RoomNumbers.xlsx → {committee: capacity}
    registrations.py      Forms CSV → list[School] via RegistrationSchema
    _text.py              normalize_school_name, first_int helpers
  assignment/
    request.py            compute_requested + _LEFTOVER_PATTERNS table
    strategy.py           AssignmentStrategy protocol + FCFSStrategy
    errors.py             AssignmentError
  reporting/
    csv_writer.py         write_assignments_csv
    summary.py            print_summary (capacity table + drops)
tests/                    pytest unit + end-to-end tests
scripts/convert_2026.py   one-off migration (kept for reference)
```

## Pipeline

The CLI is a thin orchestrator over a four-stage pipeline:

1. **`whsmun.loader`** — parses the three inputs. School names are normalized (lowercase + strip non-alphanumerics) so lottery JSON keys loosely match CSV rows. CSV column discovery and validation are centralized in `RegistrationSchema.from_headers`, which raises a single `RegistrationParseError` listing every missing/unrecognized column.
2. **`whsmun.assignment.compute_requested(school)`** — derives a school's *desired* placement from delegation size, country count, and committee Yes/No answers. Pure function, capacity-unaware.
3. **`whsmun.assignment.FCFSStrategy().assign(schools, capacities)`** — applies committee capacities **first-come-first-served in registration order**. Returns an `AssignmentResult(assignments, used)`. Overflow delegates are recorded in `Assignment.dropped`, not redistributed.
4. **`whsmun.reporting`** — `write_assignments_csv` writes one row per school in `ALL_COMMITTEES` order; `print_summary` prints a usage-vs-capacity table and the list of FCFS drops.

## Committee model

`whsmun/committees.py` defines a `Committee` dataclass and a single `COMMITTEES` tuple holding every fact about each committee (canonical name, GA vs single-seat, delegate weight, CSV-header substring, xlsx-row label). All other names — `GA_COMMITTEES`, `SINGLE_SEAT_COMMITTEES`, `DOUBLE_DEL`, `WEIGHT`, `CSV_LABEL_TO_COMMITTEE`, `XLSX_TO_COMMITTEE` — are derived from `COMMITTEES`. **When committees are renamed in either source format, edit the relevant `Committee` row and the derived views update automatically.** The registry self-validates at import (no duplicate names/labels).

Two structural facts drive the assignment algorithm:
- **GA committees** (SOCHUM, DISEC, ECOFIN, SPECPOL, GA Ad-Hoc) absorb the school's *remaining* delegates after single-seat committees are honored. A "country slot" in a GA committee seats one of the school's countries.
- **Double-del committees** (SOCHUM, DISEC) consume **2 delegates per country slot**; the other GAs consume 1. This makes SOCHUM/DISEC delegate counts always even.

## GA leftover distribution

`compute_requested` places `R // 7` country slots in every GA committee (where `R` is delegates left after singles), then uses `_LEFTOVER_PATTERNS` in `whsmun/assignment/request.py` to distribute the `R % 7` leftover delegates. Each row of the table is annotated with which committees absorb the leftovers. The table is **hand-tuned** — it encodes WHSMUN's preference for which committees absorb leftovers, and there is no single objective that reproduces all 7 rows. A `_validate_patterns()` check at import time verifies each row's weighted delegate count matches its key, so any change to GA membership or per-committee weights immediately fails the import. If you intentionally change the table, update `tests/test_request.py` — every row is pinned by a test.

## Error policy

- **`AssignmentError`** in `compute_requested` (negative delegation, more single-seats than delegates, 0 countries with GA leftover, GA remainder exceeds `7 * country_count`) halts the entire run — a single school's request being infeasible is a data bug.
- **`AssignmentError`** in `FCFSStrategy.assign` if a school requests a committee with no capacity defined in `RoomNumbers.xlsx` (registry/xlsx drift).
- Capacity overflow does **not** raise; it is recorded in `Assignment.dropped` and printed by `print_summary`.
- **`RegistrationParseError`** for any malformed registration CSV (missing required columns, unrecognized committee column, non-integer cell where a count is required). Includes row index and school name when available.
- **`ValueError`** from `load_capacities` for unknown xlsx committee labels (lists every offender at once).
