"""Pure deterministic command dispatch and atomic state-transition handlers."""

from typing import assert_never

from buxianxian.domain.cultivation import (
    MAX_SEEK_WHEEL_DAYS,
    WHEEL_SUSPECTED_SIGHTING_THRESHOLD,
    CultivationState,
    SeekWheel,
    WheelSeekingCompleted,
    WheelSeekingStatus,
    settle_wheel_seeking_day,
)
from buxianxian.domain.model import (
    MAX_ADVANCE_DAYS,
    MAX_ELAPSED_DAYS,
    Accepted,
    AdvanceTime,
    Command,
    GameState,
    Rejected,
    RejectionReason,
    TimeAdvanced,
    TransitionResult,
)
from buxianxian.domain.random_source import RandomSource


class DomainEngine:
    """Dispatch typed commands without owning state or external resources."""

    def transition(
        self,
        state: GameState,
        command: Command,
        random_source: RandomSource,
    ) -> TransitionResult:
        """Apply one command atomically to an immutable input state."""

        match command:
            case AdvanceTime():
                return _handle_advance_time(state, command)
            case SeekWheel():
                return _handle_seek_wheel(state, command, random_source)

        assert_never(command)


def _handle_advance_time(state: GameState, command: AdvanceTime) -> TransitionResult:
    if type(command.days) is not int or command.days <= 0:
        return Rejected(state=state, reason=RejectionReason.INVALID_DAY_COUNT)
    if command.days > MAX_ADVANCE_DAYS:
        return Rejected(state=state, reason=RejectionReason.DAY_COUNT_OUT_OF_RANGE)
    if state.elapsed_days > MAX_ELAPSED_DAYS - command.days:
        return Rejected(state=state, reason=RejectionReason.DAY_COUNT_OUT_OF_RANGE)

    current_elapsed_days = state.elapsed_days + command.days
    new_state = GameState(
        revision=state.revision + 1,
        elapsed_days=current_elapsed_days,
        player=state.player,
        cultivation=state.cultivation,
    )
    return Accepted(
        state=new_state,
        events=(
            TimeAdvanced(
                previous_elapsed_days=state.elapsed_days,
                current_elapsed_days=current_elapsed_days,
                days_elapsed=command.days,
            ),
        ),
    )


def _handle_seek_wheel(
    state: GameState,
    command: SeekWheel,
    random_source: RandomSource,
) -> TransitionResult:
    if type(command.max_days) is not int or command.max_days <= 0:
        return Rejected(
            state=state,
            reason=RejectionReason.INVALID_SEEK_WHEEL_DAY_COUNT,
        )
    if command.max_days > MAX_SEEK_WHEEL_DAYS:
        return Rejected(
            state=state,
            reason=RejectionReason.SEEK_WHEEL_DAY_COUNT_OUT_OF_RANGE,
        )
    if state.cultivation.wheel_status is WheelSeekingStatus.SUSPECTED_SIGHTING:
        return Rejected(state=state, reason=RejectionReason.WHEEL_ALREADY_SUSPECTED)
    if state.elapsed_days > MAX_ELAPSED_DAYS - command.max_days:
        return Rejected(
            state=state,
            reason=RejectionReason.SEEK_WHEEL_DAY_COUNT_OUT_OF_RANGE,
        )

    insight = state.cultivation.wheel_insight
    ordinary_total = 0
    inspiration_total = 0
    actual_days = 0
    for _ in range(command.max_days):
        settlement = settle_wheel_seeking_day(
            comprehension=state.player.aptitudes.comprehension,
            spiritual_sense=state.player.aptitudes.spiritual_sense,
            temperament=state.player.aptitudes.temperament,
            fortune=state.player.aptitudes.fortune,
            random_source=random_source,
        )
        actual_days += 1
        remaining = WHEEL_SUSPECTED_SIGHTING_THRESHOLD - insight
        ordinary_applied = min(settlement.ordinary_insight, remaining)
        insight += ordinary_applied
        ordinary_total += ordinary_applied

        remaining = WHEEL_SUSPECTED_SIGHTING_THRESHOLD - insight
        inspiration_applied = min(settlement.inspiration_insight, remaining)
        insight += inspiration_applied
        inspiration_total += inspiration_applied
        if insight == WHEEL_SUSPECTED_SIGHTING_THRESHOLD:
            break

    reached_suspected_sighting = insight == WHEEL_SUSPECTED_SIGHTING_THRESHOLD
    current_elapsed_days = state.elapsed_days + actual_days
    new_state = GameState(
        revision=state.revision + 1,
        elapsed_days=current_elapsed_days,
        player=state.player,
        cultivation=CultivationState(
            stage=state.cultivation.stage,
            wheel_insight=insight,
            wheel_status=(
                WheelSeekingStatus.SUSPECTED_SIGHTING
                if reached_suspected_sighting
                else WheelSeekingStatus.SEEKING
            ),
        ),
    )
    return Accepted(
        state=new_state,
        events=(
            WheelSeekingCompleted(
                requested_max_days=command.max_days,
                actual_days_elapsed=actual_days,
                previous_insight=state.cultivation.wheel_insight,
                current_insight=insight,
                ordinary_insight_gained=ordinary_total,
                inspiration_insight_gained=inspiration_total,
                reached_suspected_sighting=reached_suspected_sighting,
                previous_elapsed_days=state.elapsed_days,
                current_elapsed_days=current_elapsed_days,
            ),
        ),
    )
