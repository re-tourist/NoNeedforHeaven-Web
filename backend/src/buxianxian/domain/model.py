"""Pure domain contracts for the authoritative player and game state."""

import re
import unicodedata
from dataclasses import dataclass, field
from enum import StrEnum

from buxianxian.domain.cultivation import (
    CultivationState,
    SeekWheel,
    WheelSeekingCompleted,
)

MAX_ADVANCE_DAYS = 1_000_000
MAX_ELAPSED_DAYS = (1 << 63) - 1
MAX_CHARACTER_NAME_LENGTH = 32
TRAIT_SELECTION_COUNT = 2

_TRAIT_ID_PATTERN = re.compile(r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*")


@dataclass(frozen=True, slots=True)
class InnateAptitudes:
    """Five bounded opening growth tendencies, not final combat statistics."""

    constitution: int
    comprehension: int
    spiritual_sense: int
    temperament: int
    fortune: int

    def __post_init__(self) -> None:
        values = self.as_tuple()
        if any(type(value) is not int or not 1 <= value <= 10 for value in values):
            raise ValueError("each innate aptitude must be an integer from 1 through 10")
        if sum(values) != 25:
            raise ValueError("innate aptitude values must total 25")

    def as_tuple(self) -> tuple[int, int, int, int, int]:
        """Return values in the stable public field order."""

        return (
            self.constitution,
            self.comprehension,
            self.spiritual_sense,
            self.temperament,
            self.fortune,
        )


@dataclass(frozen=True, slots=True)
class PlayerCharacter:
    """Complete immutable player profile required by formal game state."""

    name: str
    aptitudes: InnateAptitudes
    trait_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        normalized_name = normalize_character_name(self.name)
        if normalized_name is None or normalized_name != self.name:
            raise ValueError("player name must be valid and normalized")
        if not _is_instance_of(self.aptitudes, InnateAptitudes):
            raise ValueError("player aptitudes must be a valid InnateAptitudes value")
        if type(self.trait_ids) is not tuple or len(self.trait_ids) != TRAIT_SELECTION_COUNT:
            raise ValueError("player must have exactly two trait IDs")
        if len(set(self.trait_ids)) != TRAIT_SELECTION_COUNT:
            raise ValueError("player trait IDs must be distinct")
        if any(not is_valid_trait_id(trait_id) for trait_id in self.trait_ids):
            raise ValueError("player trait IDs must be valid stable machine IDs")
        if self.trait_ids != tuple(sorted(self.trait_ids)):
            raise ValueError("player trait IDs must use canonical sorted order")


@dataclass(frozen=True, slots=True)
class GameState:
    """Complete current authoritative game facts."""

    revision: int
    elapsed_days: int
    player: PlayerCharacter
    cultivation: CultivationState = field(default_factory=CultivationState.initial)

    def __post_init__(self) -> None:
        if type(self.revision) is not int or self.revision < 0:
            raise ValueError("revision must be a non-negative integer")
        if (
            type(self.elapsed_days) is not int
            or self.elapsed_days < 0
            or self.elapsed_days > MAX_ELAPSED_DAYS
        ):
            raise ValueError("elapsed_days must be a non-negative signed 64-bit integer")
        if not _is_instance_of(self.player, PlayerCharacter):
            raise ValueError("player must be a complete PlayerCharacter value")
        if not _is_instance_of(self.cultivation, CultivationState):
            raise ValueError("cultivation must be a complete CultivationState value")


@dataclass(frozen=True, slots=True)
class AdvanceTime:
    """Request that authoritative game time advance by a number of days."""

    days: int


type Command = AdvanceTime | SeekWheel


@dataclass(frozen=True, slots=True)
class TimeAdvanced:
    """Fact that authoritative game time advanced successfully."""

    previous_elapsed_days: int
    current_elapsed_days: int
    days_elapsed: int


type DomainEvent = TimeAdvanced | WheelSeekingCompleted


class RejectionReason(StrEnum):
    """Stable reasons for expected command rejection."""

    INVALID_DAY_COUNT = "invalid_day_count"
    DAY_COUNT_OUT_OF_RANGE = "day_count_out_of_range"
    INVALID_SEEK_WHEEL_DAY_COUNT = "invalid_seek_wheel_day_count"
    SEEK_WHEEL_DAY_COUNT_OUT_OF_RANGE = "seek_wheel_day_count_out_of_range"
    WHEEL_ALREADY_SUSPECTED = "wheel_already_suspected"


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


def normalize_character_name(name: str) -> str | None:
    """Return one canonical valid name, or None for expected invalid input."""

    if type(name) is not str:
        return None
    normalized = unicodedata.normalize("NFC", name.strip())
    if not normalized or len(normalized) > MAX_CHARACTER_NAME_LENGTH:
        return None
    if any(unicodedata.category(character) in {"Cc", "Cs"} for character in normalized):
        return None
    return normalized


def is_valid_trait_id(trait_id: str) -> bool:
    """Return whether a trait ID is stable, portable, and machine-oriented."""

    return (
        type(trait_id) is str
        and len(trait_id) <= 128
        and _TRAIT_ID_PATTERN.fullmatch(trait_id) is not None
    )


def _is_instance_of(value: object, expected_type: type[object]) -> bool:
    return isinstance(value, expected_type)
