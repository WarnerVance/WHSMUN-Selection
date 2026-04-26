"""Canonical committee names, groupings, and source-format mappings."""
from typing import Final

SOCHUM: Final = "SOCHUM"
DISEC: Final = "DISEC"
ECOFIN: Final = "ECOFIN"
SPECPOL: Final = "SPECPOL"
GA_ADHOC: Final = "GA Ad-Hoc"

GA_COMMITTEES: Final[tuple[str, ...]] = (SOCHUM, DISEC, ECOFIN, SPECPOL, GA_ADHOC)
DOUBLE_DEL: Final[frozenset[str]] = frozenset({SOCHUM, DISEC})

SINGLE_SEAT_COMMITTEES: Final[tuple[str, ...]] = (
    "EU", "AU", "ASEAN", "ICJ",
    "Spec 1", "Spec 2", "Spec 3",
    "HCC", "UNSC",
    "JCC A", "JCC B",
    "Ad-Hoc", "Wisconsin Crisis",
)

ALL_COMMITTEES: Final[tuple[str, ...]] = (*GA_COMMITTEES, *SINGLE_SEAT_COMMITTEES)

# Maps the trailing identifier in a CSV column header (e.g. "CEU" in
# "Would you like to send a delegate to the CEU?") to its canonical name.
CSV_LABEL_TO_COMMITTEE: Final[dict[str, str]] = {
    "CEU": "EU",
    "AU": "AU",
    "ASEAN": "ASEAN",
    "ICJ": "ICJ",
    "Specialized Agency 2": "Spec 1",
    "Specialized Agency 3": "Spec 2",
    "Specialized Agency 4": "Spec 3",
    "HCC": "HCC",
    "UNSC": "UNSC",
    "JCC Side A": "JCC A",
    "JCC Side B": "JCC B",
    "Ad-Hoc": "Ad-Hoc",
    "Wisconsin Crisis": "Wisconsin Crisis",
}

# Maps the "Committee" cell in RoomNumbers.xlsx to its canonical name.
# HCC is assumed to map to the xlsx "Crisis Committee" row.
XLSX_TO_COMMITTEE: Final[dict[str, str]] = {
    "sochum (double del)": SOCHUM,
    "disec (double del)": DISEC,
    "ecofin": ECOFIN,
    "specpol": SPECPOL,
    "GAdhoc/ advanced GA": GA_ADHOC,
    "AU": "AU",
    "EU": "EU",
    "ASEAN": "ASEAN",
    "Spec 1": "Spec 1",
    "Spec 2": "Spec 2",
    "Spec 3": "Spec 3",
    "ICJ": "ICJ",
    "UNSC": "UNSC",
    "JCC A": "JCC A",
    "JCC B": "JCC B",
    "Crisis Committee": "HCC",
    "AD-HOC": "Ad-Hoc",
    "Wisconsin Related": "Wisconsin Crisis",
}