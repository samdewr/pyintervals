from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

T = TypeVar("T", covariant=True)


@runtime_checkable
class TotallyOrdered(Protocol[T]):
    def __lt__(self, other: T) -> bool: ...
    def __le__(self, other: T) -> bool: ...
    def __gt__(self, other: T) -> bool: ...
    def __ge__(self, other: T) -> bool: ...


IntervalBoundaryT = TypeVar("IntervalBoundaryT", bound=TotallyOrdered[Any])


@dataclass(frozen=True, order=True)
class Interval(Generic[IntervalBoundaryT]):
    start: TotallyOrdered
    end: TotallyOrdered
    value: float = field(default=0)

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise RuntimeError(
                f"Invalid interval: {self.end=} is earlier than {self.start=}"
            )

    def is_degenerate(self) -> bool:
        return self.start == self.end

    def duration(self) -> timedelta:
        return self.end - self.start

    def overlaps_with(self, other: Interval) -> bool:
        return overlaps(self, other)

    def contains(self, other: Interval) -> bool:
        return contains(self, other)


def _get_ordered(
    interval: Interval, other: Interval
) -> tuple[Interval, Interval]:
    return (
        (interval, other)
        if interval.start <= other.start
        else (other, interval)
    )


def contains_point(interval: Interval, point: datetime) -> bool:
    if interval.is_degenerate():
        return interval.start == point
    else:
        return interval.start <= point < interval.end


def overlaps(interval: Interval, other: Interval) -> bool:
    # If both are degenerate, then we should check
    # whether they're at the exact same time.
    if interval.is_degenerate() and other.is_degenerate():
        return contains_point(interval, other.start)

    # If only 1 is degenerate, then we check that
    # the point is included in the other.
    if interval.is_degenerate():
        return contains_point(other, interval.start)

    if other.is_degenerate():
        return contains_point(interval, other.start)

    # We have 2 non-degenerate intervals. We take them in order
    # and check whether they're exclusive.
    first, second = _get_ordered(interval, other)
    return second.start < first.end


def contains(interval: Interval, other: Interval) -> bool:
    # If at least one is degenerate, then we can check with overlaps.
    if interval.is_degenerate() or other.is_degenerate():
        return overlaps(interval, other)

    # We have 2 non-degenerate intervals.
    return interval.start <= other.start and interval.end >= other.end
