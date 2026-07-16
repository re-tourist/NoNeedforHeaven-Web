"""Pure domain contracts for authoritative game-time transitions."""

from dataclasses import dataclass
from enum import StrEnum

MAX_ADVANCE_DAYS = 1_000_000
MAX_ELAPSED_DAYS = (1 << 63) - 1


@dataclass(frozen=True, slots=True)
class GameState:
    """Complete current authoritative game facts."""

    revision: int
    elapsed_days: int

    def __post_init__(self) -> None:
        if type(self.revision) is not int or self.revision < 0:
            raise ValueError("revision must be a non-negative integer")
        if (
            type(self.elapsed_days) is not int
            or self.elapsed_days < 0
            or self.elapsed_days > MAX_ELAPSED_DAYS
        ):
            raise ValueError("elapsed_days must be a non-negative signed 64-bit integer")


@dataclass(frozen=True, slots=True)
class AdvanceTime:
    """Request that authoritative game time advance by a number of days."""

    days: int


type Command = AdvanceTime


@dataclass(frozen=True, slots=True)
class TimeAdvanced:
    """Fact that authoritative game time advanced successfully."""

    previous_elapsed_days: int
    current_elapsed_days: int
    days_elapsed: int


type DomainEvent = TimeAdvanced


class RejectionReason(StrEnum):
    """Stable reasons for expected command rejection."""

    INVALID_DAY_COUNT = "invalid_day_count"
    DAY_COUNT_OUT_OF_RANGE = "day_count_out_of_range"


@dataclass(frozen=True, slots=True)
class Accepted:
    """Complete state and facts produced by an atomic successful transition."""

    state: GameState
    events: tuple[DomainEvent, ...]


@dataclass(frozen=True, slots=True)
class Rejected:
    """Original state and reason produced by an expected invalid request."""

    state: GameState
    reason: RejectionReason


type TransitionResult = Accepted | Rejected
