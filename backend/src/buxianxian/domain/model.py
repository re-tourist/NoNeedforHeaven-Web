"""Pure domain data contracts for deterministic state transitions."""

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class GameState:
    """Minimal authoritative facts used to verify the domain-kernel contract."""

    revision: int
    counter: int

    def __post_init__(self) -> None:
        if self.revision < 0:
            raise ValueError("revision must be non-negative")
        if self.counter < 0:
            raise ValueError("counter must be non-negative")


@dataclass(frozen=True, slots=True)
class ConsumeCounter:
    """Request consumption of an exact synthetic counter amount."""

    amount: int


@dataclass(frozen=True, slots=True)
class ConsumeRandomCounter:
    """Request consumption of a source-selected inclusive counter amount."""

    minimum: int
    maximum: int


type Command = ConsumeCounter | ConsumeRandomCounter


@dataclass(frozen=True, slots=True)
class CounterConsumed:
    """Fact that a synthetic counter amount was consumed successfully."""

    amount: int


type DomainEvent = CounterConsumed


class RejectionReason(StrEnum):
    """Stable reasons for expected command rejection."""

    INVALID_AMOUNT = "invalid_amount"
    INVALID_RANDOM_RANGE = "invalid_random_range"
    INSUFFICIENT_COUNTER = "insufficient_counter"


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
