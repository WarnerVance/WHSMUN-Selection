"""Committee registry — the single source of truth for committee identity.

Every fact about a committee (canonical name, GA vs single-seat, delegate
weight, source-format labels) lives on its `Committee` row in `COMMITTEES`.
Other modules derive views (`GA_COMMITTEES`, `DOUBLE_DEL`, the label maps)
from this registry rather than maintaining parallel lists.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

CommitteeKind = Literal["GA", "SINGLE"]


@dataclass(frozen=True)
class Committee:
    canonical: str
    kind: CommitteeKind
    delegates_per_country_slot: int
    csv_label: str | None  # substring in CSV header; None for GA committees
    xlsx_label: str        # row label in RoomNumbers.xlsx


COMMITTEES: Final[tuple[Committee, ...]] = (
    # GA committees — absorb the school's remaining delegates as country slots.
    # SOCHUM and DISEC are double-del: each slot seats 2 delegates from one country.
    Committee("SOCHUM",          "GA",     2, None, "sochum (double del)"),
    Committee("DISEC",           "GA",     2, None, "disec (double del)"),
    Committee("ECOFIN",          "GA",     1, None, "ecofin"),
    Committee("SPECPOL",         "GA",     1, None, "specpol"),
    Committee("GA Ad-Hoc",       "GA",     1, None, "GAdhoc/ advanced GA"),
    # Single-seat committees — at most 1 delegate per Yes-answer.
    Committee("EU",              "SINGLE", 1, "CEU",              "EU"),
    Committee("AU",              "SINGLE", 1, "AU",               "AU"),
    Committee("ASEAN",           "SINGLE", 1, "ASEAN",            "ASEAN"),
    Committee("ICJ",             "SINGLE", 1, "ICJ",              "ICJ"),
    Committee("Spec 1",          "SINGLE", 1, "Specialized Agency 2", "Spec 1"),
    Committee("Spec 2",          "SINGLE", 1, "Specialized Agency 3", "Spec 2"),
    Committee("Spec 3",          "SINGLE", 1, "Specialized Agency 4", "Spec 3"),
    Committee("HCC",             "SINGLE", 1, "HCC",              "Crisis Committee"),
    Committee("UNSC",            "SINGLE", 1, "UNSC",             "UNSC"),
    Committee("JCC A",           "SINGLE", 1, "JCC Side A",       "JCC A"),
    Committee("JCC B",           "SINGLE", 1, "JCC Side B",       "JCC B"),
    Committee("Ad-Hoc",          "SINGLE", 1, "Ad-Hoc",           "AD-HOC"),
    Committee("Wisconsin Crisis","SINGLE", 1, "Wisconsin Crisis", "Wisconsin Related"),
)


# Derived views over COMMITTEES. Keep these as the only public-facing name lists
# in the rest of the codebase — never reach into COMMITTEES directly for them.

ALL_COMMITTEES: Final[tuple[str, ...]] = tuple(c.canonical for c in COMMITTEES)

GA_COMMITTEES: Final[tuple[str, ...]] = tuple(
    c.canonical for c in COMMITTEES if c.kind == "GA"
)

SINGLE_SEAT_COMMITTEES: Final[tuple[str, ...]] = tuple(
    c.canonical for c in COMMITTEES if c.kind == "SINGLE"
)

DOUBLE_DEL: Final[frozenset[str]] = frozenset(
    c.canonical for c in COMMITTEES if c.delegates_per_country_slot == 2
)

# Maps the trailing identifier in a CSV column header (e.g. "CEU" in
# "Would you like to send a delegate to the CEU?") to its canonical name.
CSV_LABEL_TO_COMMITTEE: Final[dict[str, str]] = {
    c.csv_label: c.canonical for c in COMMITTEES if c.csv_label is not None
}

# Maps the "Committee" cell in RoomNumbers.xlsx to its canonical name.
XLSX_TO_COMMITTEE: Final[dict[str, str]] = {
    c.xlsx_label: c.canonical for c in COMMITTEES
}

WEIGHT: Final[dict[str, int]] = {
    c.canonical: c.delegates_per_country_slot for c in COMMITTEES
}


def _validate_registry() -> None:
    canonicals = [c.canonical for c in COMMITTEES]
    if len(set(canonicals)) != len(canonicals):
        raise ValueError("duplicate canonical name in COMMITTEES")
    csv_labels = [c.csv_label for c in COMMITTEES if c.csv_label is not None]
    if len(set(csv_labels)) != len(csv_labels):
        raise ValueError("duplicate csv_label in COMMITTEES")
    xlsx_labels = [c.xlsx_label for c in COMMITTEES]
    if len(set(xlsx_labels)) != len(xlsx_labels):
        raise ValueError("duplicate xlsx_label in COMMITTEES")


_validate_registry()
