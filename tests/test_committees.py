"""Invariants over the committee registry."""
from whsmun.committees import (
    ALL_COMMITTEES,
    COMMITTEES,
    CSV_LABEL_TO_COMMITTEE,
    DOUBLE_DEL,
    GA_COMMITTEES,
    SINGLE_SEAT_COMMITTEES,
    WEIGHT,
    XLSX_TO_COMMITTEE,
)


def test_canonical_names_unique():
    names = [c.canonical for c in COMMITTEES]
    assert len(set(names)) == len(names)


def test_csv_labels_unique():
    labels = [c.csv_label for c in COMMITTEES if c.csv_label is not None]
    assert len(set(labels)) == len(labels)


def test_xlsx_labels_unique():
    labels = [c.xlsx_label for c in COMMITTEES]
    assert len(set(labels)) == len(labels)


def test_all_committees_partitions_into_ga_and_single():
    assert set(ALL_COMMITTEES) == set(GA_COMMITTEES) | set(SINGLE_SEAT_COMMITTEES)
    assert not (set(GA_COMMITTEES) & set(SINGLE_SEAT_COMMITTEES))


def test_double_del_only_in_ga():
    assert DOUBLE_DEL <= set(GA_COMMITTEES)


def test_double_del_committees_have_weight_two():
    for committee in DOUBLE_DEL:
        assert WEIGHT[committee] == 2


def test_non_double_del_have_weight_one():
    for committee in ALL_COMMITTEES:
        if committee not in DOUBLE_DEL:
            assert WEIGHT[committee] == 1


def test_ga_committees_have_no_csv_label():
    for c in COMMITTEES:
        if c.kind == "GA":
            assert c.csv_label is None


def test_single_seat_committees_have_csv_label():
    for c in COMMITTEES:
        if c.kind == "SINGLE":
            assert c.csv_label is not None


def test_label_maps_cover_registry():
    assert set(CSV_LABEL_TO_COMMITTEE.values()) == set(SINGLE_SEAT_COMMITTEES)
    assert set(XLSX_TO_COMMITTEE.values()) == set(ALL_COMMITTEES)
