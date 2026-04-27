"""End-to-end: run cli.main against the real project inputs and diff the
output against the checked-in baseline."""
from __future__ import annotations

from pathlib import Path

import pytest

from whsmun import cli

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRATIONS = REPO_ROOT / "WHSMUN 2026 Cleaned.csv"
ROOMS = REPO_ROOT / "RoomNumbers.xlsx"
LOTTERY = REPO_ROOT / "lottery.json"
BASELINE = REPO_ROOT / "assignments.csv"


@pytest.mark.skipif(
    not all(p.exists() for p in (REGISTRATIONS, ROOMS, LOTTERY, BASELINE)),
    reason="real inputs not present in this checkout",
)
def test_cli_reproduces_baseline_assignments_csv(tmp_path, capsys):
    output = tmp_path / "out.csv"
    rc = cli.main([
        "--registrations", str(REGISTRATIONS),
        "--rooms", str(ROOMS),
        "--lottery", str(LOTTERY),
        "--output", str(output),
    ])
    assert rc == 0
    assert output.read_bytes() == BASELINE.read_bytes()
