"""Command-line entry point for `python -m whsmun` and the `whsmun` script."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from whsmun.assignment import AssignmentError, FCFSStrategy
from whsmun.loader import load_capacities, load_lottery, load_schools
from whsmun.reporting import print_summary, write_assignments_csv

_REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_REGISTRATIONS = _REPO_ROOT / "WHSMUN 2026 Cleaned.csv"
DEFAULT_ROOMS = _REPO_ROOT / "RoomNumbers.xlsx"
DEFAULT_LOTTERY = _REPO_ROOT / "lottery.json"
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
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="Path to write the assignments CSV.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    lottery = load_lottery(args.lottery)
    capacities = load_capacities(args.rooms)
    schools = load_schools(args.registrations, lottery)

    try:
        result = FCFSStrategy().assign(schools, capacities)
    except AssignmentError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    write_assignments_csv(args.output, result.assignments)
    print_summary(result.assignments, capacities, result.used)
    print(f"\nWrote {args.output.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
