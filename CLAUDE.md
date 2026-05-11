# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Run

```bash
uv run python -m whsmun                # assignment pipeline → assignments.csv
uv run python -m whsmun --roster       # roster generator → Rosters/*.xlsx (skips pipeline)
```

The assignment pipeline reads four input files relative to the repo root and writes `assignments.csv`:
- `Responses.csv` — Google Forms export (cleaned), one row per school
- `RoomNumbers.xlsx` — sheet `Committee Numbers`, columns `(dept, committee, count, ...)`
- `lottery.json` — `{school_name: country}` for schools that drew a country in the lottery
- `Countries.txt` — one country per line, the pool from which non-lottery slots are filled

Override any of the five paths with `--registrations`, `--rooms`, `--lottery`, `--countries`, `--output`.

`--roster` is a separate mode: it reads back the existing `assignments.csv` at `--output`, then writes one styled xlsx per school to `<dirname(--output)>/Rosters/`. The pipeline is skipped entirely. Re-running wipes and recreates the directory.

Python 3.14+. Runtime deps: `openpyxl`, `pillow` (openpyxl needs pillow to embed the banner image). Dev dep: `pytest` (`pip install -e ".[dev]"`).

## Layout

```
whsmun/                   the package
  cli.py                  argparse entry; `python -m whsmun` runs this
  committees.py           Committee dataclass + COMMITTEES registry (single source of truth)
  models.py               School, Assignment, AssignmentResult, PlacementMap
  loader/
    lottery.py            lottery.json → {normalized_name: country}
    capacities.py         RoomNumbers.xlsx → {committee: capacity}
    countries.py          Countries.txt → ordered list[str]
    registrations.py      Forms CSV → list[School] via RegistrationSchema
    _text.py              normalize_school_name, first_int helpers
  assignment/
    request.py            compute_requested + _LEFTOVER_PATTERNS table
    strategy.py           AssignmentStrategy protocol + FCFSStrategy
    countries.py          assign_countries: per-school country list (lottery + pool)
    errors.py             AssignmentError
  reporting/
    csv_writer.py         write_assignments_csv
    csv_reader.py         read_assignments_csv → list[SchoolRoster] (roster mode)
    roster.py             write_rosters: per-school xlsx generator
    summary.py            print_summary (capacity table + drops)
  templates/
    roster_template.xlsx  bundled blank template (formatting preserved verbatim)
    roster_image.png      banner image re-attached by roster.py (openpyxl drops it on round-trip)
tests/                    pytest unit + end-to-end tests
scripts/convert_2026.py   one-off migration (kept for reference)
```

## Pipeline

The CLI is a thin orchestrator over a four-stage pipeline:

1. **`whsmun.loader`** — parses the three inputs. School names are normalized (lowercase + strip non-alphanumerics) so lottery JSON keys loosely match CSV rows. CSV column discovery and validation are centralized in `RegistrationSchema.from_headers`, which raises a single `RegistrationParseError` listing every missing/unrecognized column.
2. **`whsmun.assignment.compute_requested(school)`** — derives a school's *desired* placement from delegation size, country count, and committee Yes/No answers. Pure function, capacity-unaware.
3. **`whsmun.assignment.FCFSStrategy().assign(schools, capacities)`** — applies committee capacities **first-come-first-served in registration order**. Returns an `AssignmentResult(assignments, used)`. Overflow delegates are recorded in `Assignment.dropped`, not redistributed.
4. **`whsmun.assignment.assign_countries(schools, country_pool)`** — picks the concrete countries each school will represent. The lottery country (if any) comes first; the remaining `extra_countries` are pulled from `Countries.txt` in file order, skipping any name already used by a lottery or earlier school. Pool exhaustion raises `AssignmentError` naming the school that ran out. The CLI writes the result onto `Assignment.assigned_countries`.
5. **`whsmun.reporting`** — `write_assignments_csv` writes one row per school in `ALL_COMMITTEES` order with a `Countries` column listing all assigned countries (lottery first, comma-separated); `print_summary` prints a usage-vs-capacity table and the list of FCFS drops.

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
- **`AssignmentError`** in `assign_countries` if `Countries.txt` runs out before every school's `extra_countries` quota is filled.
- **`ValueError`** from `load_countries` if `Countries.txt` contains duplicate entries.
- Capacity overflow does **not** raise; it is recorded in `Assignment.dropped` and printed by `print_summary`.
- **`RegistrationParseError`** for any malformed registration CSV (missing required columns, unrecognized committee column, non-integer cell where a count is required). Includes row index and school name when available.
- **`ValueError`** from `load_capacities` for unknown xlsx committee labels (lists every offender at once).

## Roster generation (`--roster`)

A separate mode from the assignment pipeline. Reads back the existing `assignments.csv` via `whsmun.reporting.csv_reader.read_assignments_csv` (into `SchoolRoster` records) and produces one styled xlsx per school under `<output_dir>/Rosters/`. Used by the secretariat to give each school a workbook for filling in delegate names.

Row generation rules in `whsmun/reporting/roster.py`:
- **Single-seat committees**: one row with `Position` left blank — humans fill these in later.
- **GA committees**: one row per country slot, with the country in `Position`. Slot count = `placements[committee] // WEIGHT[committee]`. The first N countries from the school's `Countries` field (lottery first) fill the slots.
- **Double-del GA** (SOCHUM, DISEC): two rows per country, with `Position` = `"Country, 1"` / `"Country, 2"`.
- Committees with `placements[committee] == 0` get no row.

Template handling — `_write_one` byte-copies the bundled template with `shutil.copy2` before opening it, then uses openpyxl only to write cell values. openpyxl reserializes XML on save but preserves merged cells, fonts, column widths, and row heights because those objects aren't touched. The one thing openpyxl **does** drop on round-trip is embedded images, so the banner image is bundled separately as `whsmun/templates/roster_image.png` and re-attached via `openpyxl.drawing.image.Image` at the same anchor (column C row 0, 2209800 × 2171700 EMU) as the original `drawing1.xml`.

`write_rosters` wipes `Rosters/` and recreates it on every run. Filenames are `{sanitized_school_name} WHSMUN Roster.xlsx`; sanitization replaces `/\:*?"<>|` with `_`.
