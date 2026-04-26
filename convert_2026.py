"""One-off: convert the 2026 registration CSV into the 2027 format the loader expects."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "WHSMUN 2026 Registration Form (Responses).csv"
DST = ROOT / "WHSMUN 2026 Cleaned.csv"

# Source column keys (exact, with trailing colons/spaces).
SCHOOL = "Registering School:"
SIZE = "How large is your Delegation? (Please input a specific number. Changes can be made up until February):"
COUNTRIES = "How many Member-States would you like to represent? (Maximum of 5) "
ICJ = "Would you like to apply for a student to participate in the International Court of Justice?"
HRC = "Would you like to apply for a student to participate in the Human Rights Council?"
WHO = "Would you like to apply for a student to participate in the World Health Organization?"
CEU = "Would you like to apply for a student to participate in the Council of the European Union?"
AU = "Would you like to apply for a student to participate in the African Union?"
ASEAN = "Would you like to apply for a student to participate in the Association of Southeast Asian Nations?"
HCC = "Would you like to apply for a student to participate in the Historic Crisis Committee?"
JCC = "Would you like to apply for one or two students to participate in the Joint Crisis Committees?"
UNSC = (
    "Would you like to apply for a student to participate in the UN Security Council? "
    "*If you are assigned a Member State which has a seat on the UNSC, you are automatically "
    "assigned that seat.  If you would NOT like to represent that Member State in this committee, "
    "than please select another Member State to represent. "
)

OUT_HEADERS = [
    "Timestamp",
    "Email Address",
    "Name of School",
    "How large is your Delegation? Changes can be made up until February. "
    "Please note there is a limit of 30 delegates per delegation",
    "Is your school on this list?",
    "Besides the country you drew in the lottery last year (if you did), how many "
    "other countries do you wish to represent in General Assembly. We will assign countries.",
    "Would you like to send a delegate to the CEU?",
    "Would you like to send a delegate to the AU?",
    "Would you like to send a delegate to the ASEAN?",
    "Would you like to send a delegate to the ICJ?",
    "Would you like to send a delegate to Specialized Agency 2?",
    "Would you like to send a delegate to Specialized Agency 3?",
    "Would you like to send a delegate to Specialized Agency 4?",
    "Would you like to send a delegate to the HCC?",
    "Would you like to send a delegate to the UNSC?",
    "Would you like to send a delegate to the JCC Side A?",
    "Would you like to send a delegate to Ad-Hoc?",
    "Would you like to send a delegate to the Wisconsin Crisis?",
    "Would you like to send a delegate to the JCC Side B?",
]
SIZE_OUT = OUT_HEADERS[3]
COUNTRIES_OUT = OUT_HEADERS[5]


def yn(value: str) -> str:
    return "Yes" if (value or "").strip().lower() == "yes" else "No"


def jcc_count(value: str) -> int:
    s = (value or "").strip().lower()
    if s in ("", "none", "0"):
        return 0
    try:
        return int(s)
    except ValueError:
        return 0


SINGLE_SEAT_OUT_HEADERS = [
    "Would you like to send a delegate to the CEU?",
    "Would you like to send a delegate to the AU?",
    "Would you like to send a delegate to the ASEAN?",
    "Would you like to send a delegate to the ICJ?",
    "Would you like to send a delegate to Specialized Agency 2?",
    "Would you like to send a delegate to Specialized Agency 3?",
    "Would you like to send a delegate to Specialized Agency 4?",
    "Would you like to send a delegate to the HCC?",
    "Would you like to send a delegate to the UNSC?",
    "Would you like to send a delegate to the JCC Side A?",
    "Would you like to send a delegate to Ad-Hoc?",
    "Would you like to send a delegate to the Wisconsin Crisis?",
    "Would you like to send a delegate to the JCC Side B?",
]
TOTAL_SINGLE_SEATS = len(SINGLE_SEAT_OUT_HEADERS)


def main() -> None:
    with SRC.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    out_rows = []
    for r in rows:
        school = (r.get(SCHOOL) or "").strip()
        if not school:
            continue
        size_str = (r.get(SIZE) or "").strip()
        countries_str = (r.get(COUNTRIES) or "").strip()
        try:
            total = int(size_str)
            countries = int(countries_str)
        except ValueError:
            total = countries = 0
        jcc = jcc_count(r.get(JCC, ""))

        original = {
            "Would you like to send a delegate to the CEU?": yn(r.get(CEU, "")),
            "Would you like to send a delegate to the AU?": yn(r.get(AU, "")),
            "Would you like to send a delegate to the ASEAN?": yn(r.get(ASEAN, "")),
            "Would you like to send a delegate to the ICJ?": yn(r.get(ICJ, "")),
            "Would you like to send a delegate to Specialized Agency 2?": yn(r.get(HRC, "")),
            "Would you like to send a delegate to Specialized Agency 3?": yn(r.get(WHO, "")),
            "Would you like to send a delegate to Specialized Agency 4?": "No",
            "Would you like to send a delegate to the HCC?": yn(r.get(HCC, "")),
            "Would you like to send a delegate to the UNSC?": yn(r.get(UNSC, "")),
            "Would you like to send a delegate to the JCC Side A?": "Yes" if jcc >= 1 else "No",
            "Would you like to send a delegate to Ad-Hoc?": "No",
            "Would you like to send a delegate to the Wisconsin Crisis?": "No",
            "Would you like to send a delegate to the JCC Side B?": "Yes" if jcc >= 2 else "No",
        }

        # Bump to all-Yes only when (a) the school is large enough to seat all
        # 13 single committees and (b) keeping the original responses would
        # leave more delegates than the GA can hold (7 * country_count).
        single_count = sum(1 for v in original.values() if v == "Yes")
        if (total - single_count) > 7 * countries and total >= TOTAL_SINGLE_SEATS:
            single_seat_values = {h: "Yes" for h in SINGLE_SEAT_OUT_HEADERS}
            single_count = TOTAL_SINGLE_SEATS
        else:
            single_seat_values = original

        # If still infeasible (small school with 1 country), bump countries to
        # the minimum needed to fit the GA leftover, capped at the form's 5.
        remaining = max(total - single_count, 0)
        needed_countries = -(-remaining // 7)  # ceil(remaining / 7)
        effective_countries = min(5, max(countries, needed_countries))
        countries_out = (
            f"{effective_countries} Countries" if effective_countries else "0 Countries"
        )

        out_rows.append({
            "Timestamp": r.get("Timestamp", ""),
            "Email Address": r.get("Email Address", ""),
            "Name of School": school,
            SIZE_OUT: size_str,
            "Is your school on this list?": "No",
            COUNTRIES_OUT: countries_out,
            **single_seat_values,
        })

    with DST.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUT_HEADERS)
        w.writeheader()
        w.writerows(out_rows)

    print(f"Wrote {DST.name} with {len(out_rows)} schools")


if __name__ == "__main__":
    main()
