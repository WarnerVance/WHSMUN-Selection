# WHSMUN Committee Assignment

This tool decides which committees each school's delegates will sit on at WHSMUN, based on what schools asked for in their registration form, how big their delegation is, how many countries they represent, and how many seats are available in each committee room.

## What goes in, what comes out

**Inputs**

- The Google Form export (`...Form Responses 1 (1).csv`) — one row per school, with the size of their delegation, how many extra countries they're bringing, and a Yes/No for each committee.
- `RoomNumbers.xlsx` — the maximum number of delegates each committee room can hold.
- `lottery.json` — for each school that drew a country in the lottery, the country they drew. (A school's country count is `1 + extra countries` if they won the lottery, otherwise just the extras.)

**Output**

- `assignments.csv` — one row per school, with the number of delegates placed in each committee, plus totals for placed and dropped.
- A summary printed to the screen showing how full each committee is and listing any delegates that had to be cut because their committee filled up.

## The committees come in three flavors

1. **Single-seat committees** (EU, AU, ASEAN, ICJ, the three Specialized Agencies, HCC, UNSC, JCC A & B, Ad-Hoc, Wisconsin Crisis). A school either sends **one** delegate here or doesn't — these are the Yes/No questions on the form.
2. **GA committees** — ECOFIN, SPECPOL, and GA Ad-Hoc. These are the big rooms that absorb whatever delegates are left over after the single-seats are accounted for.
3. **Double-del GA committees** — SOCHUM and DISEC. Same as above, but each "seat" here is actually **two** delegates representing the same country (so a country always sends a pair, never a single).

## The algorithm, in plain language

For each school, taken in the order they registered:

### Step 1 — Honor the Yes answers

Every committee the school said "Yes" to on a single-seat question gets one delegate. If a school said Yes to more single-seats than they have delegates total, the program stops and reports the conflict — that's a registration mistake and a human needs to fix it.

### Step 2 — Spread the remainder across the five GA committees

Whatever delegates are left after Step 1 need to go into the five GA committees. The unit of distribution is a **country slot**: one of the school's countries getting a chair in one GA committee. A school with 3 countries can fill at most 3 slots in any single GA committee.

Here's the catch that shapes everything: in SOCHUM and DISEC, each country slot costs **2 delegates** (because those committees seat double-del pairs). In ECOFIN, SPECPOL, and GA Ad-Hoc, each slot costs **1 delegate**.

If you add up the cost of giving every one of a school's countries a seat in all five GAs, it's `2 + 2 + 1 + 1 + 1 = 7` delegates per country. So the math works like this:

- Give every GA committee `R ÷ 7` country slots, where `R` is the number of delegates left after Step 1. (Integer division — the remainder is handled next.)
- Then distribute the `R mod 7` leftover delegates using a fixed table of patterns, one per remainder from 0 to 6. The patterns are designed so that:
  - SOCHUM and DISEC always get an **even** number of delegates (because you can't break a double-del pair in half).
  - The leftovers go to single-del committees first, so as many GA committees as possible end up with at least one country represented.

If a school has more delegates than `7 × (their country count)` left over for the GAs, that's also impossible — you've run out of countries to seat — and the program stops.

### Step 3 — Apply the room capacities, first-come first-served

Now the program walks through the schools in **registration order** and tries to put each school's requested delegates into the actual rooms. If a committee still has space, the delegates go in. If the committee is already full because earlier schools used up the seats, those delegates are **dropped** — not reassigned, just recorded as cut, and reported at the end so the organizers can decide what to do.

This is why registration order matters: the schools that registered first get their full request honored, and any squeeze falls on whoever registered late.

## Running it

```
uv run main.py
```

The three input files need to be sitting next to `main.py` with the names listed at the top. The output `assignments.csv` is written into the same folder.