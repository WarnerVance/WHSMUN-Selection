"""Domain types: schools, placements, and assignment results."""
from __future__ import annotations

from dataclasses import dataclass, field

PlacementMap = dict[str, int]


@dataclass(frozen=True)
class School:
    row_index: int
    name: str
    total_delegates: int
    extra_countries: int
    lottery_country: str | None
    yes_committees: tuple[str, ...]

    @property
    def country_count(self) -> int:
        return self.extra_countries + (1 if self.lottery_country else 0)


@dataclass
class Assignment:
    school: School
    placements: PlacementMap = field(default_factory=dict)
    dropped: PlacementMap = field(default_factory=dict)

    @property
    def total_assigned(self) -> int:
        return sum(self.placements.values())

    @property
    def total_dropped(self) -> int:
        return sum(self.dropped.values())


@dataclass(frozen=True)
class AssignmentResult:
    """Output of an `AssignmentStrategy`: per-school assignments plus aggregate usage."""
    assignments: list[Assignment]
    used: dict[str, int]
