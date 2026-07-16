"""Public contracts for the pure 不羡仙 deterministic domain kernel."""

from buxianxian.domain.engine import DomainEngine
from buxianxian.domain.model import (
    MAX_ADVANCE_DAYS,
    MAX_ELAPSED_DAYS,
    Accepted,
    AdvanceTime,
    Command,
    DomainEvent,
    GameState,
    Rejected,
    RejectionReason,
    TimeAdvanced,
    TransitionResult,
)
from buxianxian.domain.random_source import RandomSource

__all__ = [
    "MAX_ADVANCE_DAYS",
    "MAX_ELAPSED_DAYS",
    "Accepted",
    "AdvanceTime",
    "Command",
    "DomainEngine",
    "DomainEvent",
    "GameState",
    "RandomSource",
    "Rejected",
    "RejectionReason",
    "TimeAdvanced",
    "TransitionResult",
]
