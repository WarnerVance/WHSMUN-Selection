# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Run

```bash
uv run main.py
```

Reads three input files relative to the repo root and writes `assignments.csv`:
- `WHSMUN 2027 Registration Form (Responses) - Form Responses 1 (1).csv` — Google Forms export, one row per school
- `RoomNumbers.xlsx` — sheet `Committee Numbers`, columns `(dept, committee, count, ...)`
- `lottery.json` — `{school_name: country}` for schools that drew a country in the lottery

Python 3.14+. The only runtime dep is `openpyxl`.

## Pipeline

`main.py` is a thin orchestrator. The real work is a four-stage pipeline:

1. **`loader.py`** — parses the three inputs into `dict[str, int]` capacities, `dict[str, str]` lottery, and `list[School]`. School names are normalized via `_normalize_school` (lowercase + strip non-alphanumerics) so lottery JSON keys can be loosely matched against CSV school names.
2. **`assigner.compute_requested(school)`** — derives a school's *desired* placement from its delegation size, country count, and committee Yes/No answers. Pure function, no capacity awareness.
3. **`assigner.assign_all(schools, capacities)`** — applies committee capacities **first-come-first-served in registration order**. Overflow delegates are *dropped*, not redistributed; each `Assignment` carries both `placements` and `dropped` dicts.
4. **`reporter.py`** — writes `assignments.csv` (one row per school, one column per committee in `ALL_COMMITTEES` order) and prints a usage-vs-capacity table plus the list of FCFS drops.

## Committee model

`committees.py` is the single source of truth for committee identity. Three names exist for every committee — the canonical name (used everywhere in code), the CSV column header substring (`CSV_LABEL_TO_COMMITTEE`), and the xlsx row label (`XLSX_TO_COMMITTEE`). When committees are renamed in either source format, update the mapping here, not in the loader.

Two structural facts drive the assignment algorithm:
- **`GA_COMMITTEES`** (SOCHUM, DISEC, ECOFIN, SPECPOL, GA Ad-Hoc) absorb the school's *remaining* delegates after single-seat committees are honored. A "country slot" in a GA committee seats one of the school's countries.
- **`DOUBLE_DEL`** (SOCHUM, DISEC) consume **2 delegates per country slot**; the other GAs consume 1. This makes SOCHUM/DISEC delegate counts always even.

## GA leftover distribution

`compute_requested` places `R // 7` country slots in every GA committee (where `R` is delegates left after singles), then uses `_LEFTOVER_PATTERNS` to distribute the `R % 7` leftover delegates without breaking the double-del even-count constraint. The patterns are precomputed for `R%7 ∈ 0..6` and intentionally favor single-del committees so leftovers spread across more GAs. If you change the GA committee set, double-del set, or per-committee weights, **regenerate `_LEFTOVER_PATTERNS`** — they are tightly coupled to those constants.

## Error policy

- **`AssignmentError`** in `compute_requested` (e.g. more single-seats requested than total delegates, GA remainder exceeds `7 * country_count`) halts the entire run — a single school's request being infeasible is treated as a data bug.
- Capacity overflow does **not** raise; it is recorded in `Assignment.dropped` and printed by `reporter.print_summary`.
- Unknown committee labels in `RoomNumbers.xlsx` raise `ValueError` from `load_capacities`; unknown CSV committee columns raise from `_build_committee_column_map`.