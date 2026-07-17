"""Pure pre-alpha rules and contracts for wheel-seeking cultivation."""

from dataclasses import dataclass
from enum import StrEnum

from buxianxian.domain.random_source import RandomSource

MIN_SEEK_WHEEL_DAYS = 1
MAX_SEEK_WHEEL_DAYS = 30
WHEEL_SUSPECTED_SIGHTING_THRESHOLD = 100

PRE_ALPHA_BASE_DAILY_INSIGHT = 1
PRE_ALPHA_COMPREHENSION_DIVISOR = 3
PRE_ALPHA_TEMPERAMENT_DIVISOR = 5
PRE_ALPHA_SUBTLE_SENSE_BONUS = 1
PRE_ALPHA_INSPIRATION_CHANCE_PER_FORTUNE = 2
PRE_ALPHA_INSPIRATION_BASE_BONUS = 3
PRE_ALPHA_INSPIRATION_COMPREHENSION_DIVISOR = 5


class CultivationStage(StrEnum):
    """Current supported cultivation stage."""

    SEEKING_WHEEL = "seeking_wheel"


class WheelSeekingStatus(StrEnum):
    """Progress status within the first wheel-seeking stage."""

    SEEKING = "seeking"
    SUSPECTED_SIGHTING = "suspected_sighting"


@dataclass(frozen=True, slots=True)
class CultivationState:
    """Complete authoritative cultivation facts for the current pre-alpha slice."""

    stage: CultivationStage
    wheel_insight: int
    wheel_status: WheelSeekingStatus

    def __post_init__(self) -> None:
        if self.stage is not CultivationStage.SEEKING_WHEEL:
            raise ValueError("only the wheel-seeking cultivation stage is supported")
        if (
            type(self.wheel_insight) is not int
            or not 0 <= self.wheel_insight <= WHEEL_SUSPECTED_SIGHTING_THRESHOLD
        ):
            raise ValueError("wheel insight must be an integer within the supported threshold")
        expected_status = (
            WheelSeekingStatus.SUSPECTED_SIGHTING
            if self.wheel_insight == WHEEL_SUSPECTED_SIGHTING_THRESHOLD
            else WheelSeekingStatus.SEEKING
        )
        if self.wheel_status is not expected_status:
            raise ValueError("wheel status must be consistent with wheel insight")

    @classmethod
    def initial(cls) -> CultivationState:
        """Return the complete initial cultivation state for a new game."""

        return cls(
            stage=CultivationStage.SEEKING_WHEEL,
            wheel_insight=0,
            wheel_status=WheelSeekingStatus.SEEKING,
        )


@dataclass(frozen=True, slots=True)
class SeekWheel:
    """Request at most a bounded number of wheel-seeking cultivation days."""

    max_days: int


@dataclass(frozen=True, slots=True)
class WheelSeekingCompleted:
    """Summary fact produced by one atomic accepted wheel-seeking action."""

    requested_max_days: int
    actual_days_elapsed: int
    previous_insight: int
    current_insight: int
    ordinary_insight_gained: int
    inspiration_insight_gained: int
    reached_suspected_sighting: bool
    previous_elapsed_days: int
    current_elapsed_days: int


@dataclass(frozen=True, slots=True)
class WheelSeekingDailySettlement:
    """One day's bounded ordinary and occasional insight before threshold capping."""

    ordinary_insight: int
    inspiration_insight: int


def settle_wheel_seeking_day(
    *,
    comprehension: int,
    spiritual_sense: int,
    temperament: int,
    fortune: int,
    random_source: RandomSource,
) -> WheelSeekingDailySettlement:
    """Settle one day with exactly two random calls in a stable order."""

    subtle_sense_roll = random_source.integer_inclusive(1, 10)
    inspiration_roll = random_source.integer_inclusive(1, 100)
    if type(subtle_sense_roll) is not int or not 1 <= subtle_sense_roll <= 10:
        raise RuntimeError("random source violated the subtle-sense roll contract")
    if type(inspiration_roll) is not int or not 1 <= inspiration_roll <= 100:
        raise RuntimeError("random source violated the inspiration roll contract")

    ordinary_insight = (
        PRE_ALPHA_BASE_DAILY_INSIGHT
        + comprehension // PRE_ALPHA_COMPREHENSION_DIVISOR
        + temperament // PRE_ALPHA_TEMPERAMENT_DIVISOR
        + (PRE_ALPHA_SUBTLE_SENSE_BONUS if subtle_sense_roll <= spiritual_sense else 0)
    )
    inspiration_insight = (
        PRE_ALPHA_INSPIRATION_BASE_BONUS
        + comprehension // PRE_ALPHA_INSPIRATION_COMPREHENSION_DIVISOR
        if inspiration_roll <= fortune * PRE_ALPHA_INSPIRATION_CHANCE_PER_FORTUNE
        else 0
    )
    return WheelSeekingDailySettlement(
        ordinary_insight=ordinary_insight,
        inspiration_insight=inspiration_insight,
    )
