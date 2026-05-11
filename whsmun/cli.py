"""Command-line entry point for `python -m whsmun` and the `whsmun` script."""
from __future__ import annotations

import argparse
import sys
from importlib.resources import as_file, files
from pathlib import Path

from whsmun.assignment import AssignmentError, FCFSStrategy, assign_countries
from whsmun.loader import load_capacities, load_countries, load_lottery, load_schools
from whsmun.reporting import (
    print_summary,
    read_assignments_csv,
    write_assignments_csv,
    write_rosters,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_REGISTRATIONS = _REPO_ROOT / "Responses.csv"
DEFAULT_ROOMS = _REPO_ROOT / "RoomNumbers.xlsx"
DEFAULT_LOTTERY = _REPO_ROOT / "lottery.json"
DEFAULT_COUNTRIES = _REPO_ROOT / "Countries.txt"
DEFAULT_OUTPUT = _REPO_ROOT / "assignments.csv"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="whsmun",
        description="Assign WHSMUN delegates to committees from registration responses.",
    )
    parser.add_argument("--registrations", type=Path, default=DEFAULT_REGISTRATIONS,
                        help="Path to the cleaned registration CSV.")
    parser.add_argument("--rooms", type=Path, default=DEFAULT_ROOMS,
                        help="Path to RoomNumbers.xlsx.")
    parser.add_argument("--lottery", type=Path, default=DEFAULT_LOTTERY,
                        help="Path to lottery.json.")
    parser.add_argument("--countries", type=Path, default=DEFAULT_COUNTRIES,
                        help="Path to the country pool (one country per line).")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="Path to write the assignments CSV.")
    parser.add_argument("--roster", action="store_true",
                        help="Generate per-school roster xlsx files from an existing "
                             "assignments.csv. Skips the assignment pipeline.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.roster:
        return _run_roster(args.output)

    lottery = load_lottery(args.lottery)
    capacities = load_capacities(args.rooms)
    country_pool = load_countries(args.countries)
    schools = load_schools(args.registrations, lottery)

    try:
        result = FCFSStrategy().assign(schools, capacities)
        countries_by_school = assign_countries(schools, country_pool)
    except AssignmentError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    for assignment in result.assignments:
        assignment.assigned_countries = countries_by_school[assignment.school.row_index]

    write_assignments_csv(args.output, result.assignments)
    print_summary(result.assignments, capacities, result.used)
    print(f"\nWrote {args.output.name}")
    return 0


def _run_roster(assignments_path: Path) -> int:
    if not assignments_path.exists():
        print(f"ERROR: {assignments_path} not found. Run `python -m whsmun` first to "
              f"generate it, then re-run with --roster.", file=sys.stderr)
        return 1
    rosters = read_assignments_csv(assignments_path)
    output_dir = assignments_path.parent / "Rosters"
    template_resource = files("whsmun.templates") / "roster_template.xlsx"
    image_resource = files("whsmun.templates") / "roster_image.png"
    with as_file(template_resource) as template_path, as_file(image_resource) as image_path:
        count = write_rosters(template_path, output_dir, rosters, image_path)
    print(f"Wrote {count} rosters to {output_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
