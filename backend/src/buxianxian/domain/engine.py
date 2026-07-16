"""Pure deterministic command dispatch and atomic state-transition handlers."""

from typing import assert_never

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
