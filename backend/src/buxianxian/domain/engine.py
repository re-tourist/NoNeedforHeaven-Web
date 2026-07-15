"""Pure deterministic command dispatch and atomic state-transition handlers."""

from typing import assert_never

from buxianxian.domain.model import (
    Accepted,
    Command,
    ConsumeCounter,
    ConsumeRandomCounter,
    CounterConsumed,
    GameState,
    Rejected,
    RejectionReason,
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
            case ConsumeCounter():
                return _handle_consume_counter(state, command)
            case ConsumeRandomCounter():
                return _handle_consume_random_counter(state, command, random_source)

        assert_never(command)


def _handle_consume_counter(state: GameState, command: ConsumeCounter) -> TransitionResult:
    return _consume(state, command.amount)


def _handle_consume_random_counter(
    state: GameState,
    command: ConsumeRandomCounter,
    random_source: RandomSource,
) -> TransitionResult:
    if command.minimum <= 0 or command.maximum < command.minimum:
        return Rejected(state=state, reason=RejectionReason.INVALID_RANDOM_RANGE)

    amount = random_source.integer_inclusive(command.minimum, command.maximum)
    if not command.minimum <= amount <= command.maximum:
        raise ValueError("random source returned a value outside the requested bounds")

    return _consume(state, amount)


def _consume(state: GameState, amount: int) -> TransitionResult:
    if amount <= 0:
        return Rejected(state=state, reason=RejectionReason.INVALID_AMOUNT)
    if amount > state.counter:
        return Rejected(state=state, reason=RejectionReason.INSUFFICIENT_COUNTER)

    new_state = GameState(
        revision=state.revision + 1,
        counter=state.counter - amount,
    )
    return Accepted(
        state=new_state,
        events=(CounterConsumed(amount=amount),),
    )
