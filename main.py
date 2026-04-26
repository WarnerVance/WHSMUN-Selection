"""WHSMUN delegate-to-committee assignment tool."""
from __future__ import annotations

import sys
from pathlib import Path

from assigner import AssignmentError, assign_all
from loader import load_capacities, load_lottery, load_schools
from reporter import print_summary, write_assignments_csv

ROOT = Path(__file__).parent
REGISTRATIONS_CSV = ROOT / "WHSMUN 2027 Registration Form (Responses) - Form Responses 1 (1).csv"
ROOMS_XLSX = ROOT / "RoomNumbers.xlsx"
LOTTERY_JSON = ROOT / "lottery.json"
OUTPUT_CSV = ROOT / "assignments.csv"


def main() -> int:
    lottery = load_lottery(LOTTERY_JSON)
    capacities = load_capacities(ROOMS_XLSX)
    schools = load_schools(REGISTRATIONS_CSV, lottery)

    try:
        assignments, used = assign_all(schools, capacities)
    except AssignmentError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    write_assignments_csv(OUTPUT_CSV, assignments)
    print_summary(assignments, capacities, used)
    print(f"\nWrote {OUTPUT_CSV.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())