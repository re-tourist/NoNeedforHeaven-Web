"""Behavioral contracts for the pure deterministic domain engine."""

from dataclasses import dataclass

import pytest

from buxianxian.domain import (
    Accepted,
    ConsumeCounter,
    ConsumeRandomCounter,
    CounterConsumed,
    DomainEngine,
    GameState,
    Rejected,
    RejectionReason,
)


class NeverRandomSource:
    """Fail if a command unexpectedly asks for random input."""

    def integer_inclusive(self, minimum: int, maximum: int, /) -> int:
        raise AssertionError(f"unexpected random request: [{minimum}, {maximum}]")


@dataclass(frozen=True, slots=True)
class FixedRandomSource:
    """Return one controlled value after checking the requested bounds."""

    value: int

    def integer_inclusive(self, minimum: int, maximum: int, /) -> int:
        assert minimum <= self.value <= maximum
        return self.value


class OutOfRangeRandomSource:
    """Deliberately violate the RandomSource protocol for a contract test."""

    def integer_inclusive(self, minimum: int, maximum: int, /) -> int:
        return maximum + 1


ENGINE = DomainEngine()


def test_valid_command_returns_independent_state_and_fact_event() -> None:
    state = GameState(revision=0, counter=5)

    result = ENGINE.transition(state, ConsumeCounter(amount=2), NeverRandomSource())

    assert isinstance(result, Accepted)
    assert result.state == GameState(revision=1, counter=3)
    assert result.state is not state
    assert result.events == (CounterConsumed(amount=2),)
    assert state == GameState(revision=0, counter=5)


def test_insufficient_counter_returns_structured_rejection_without_mutation() -> None:
    state = GameState(revision=0, counter=5)

    result = ENGINE.transition(state, ConsumeCounter(amount=10), NeverRandomSource())

    assert isinstance(result, Rejected)
    assert result == Rejected(state=state, reason=RejectionReason.INSUFFICIENT_COUNTER)
    assert result.state is state
    assert result.state.revision == 0
    assert result.state.counter == 5


def test_non_positive_amount_is_an_expected_rejection() -> None:
    state = GameState(revision=3, counter=5)

    result = ENGINE.transition(state, ConsumeCounter(amount=0), NeverRandomSource())

    assert result == Rejected(state=state, reason=RejectionReason.INVALID_AMOUNT)
    assert state == GameState(revision=3, counter=5)


def test_invalid_random_range_is_rejected_before_requesting_random_input() -> None:
    state = GameState(revision=0, counter=5)

    result = ENGINE.transition(
        state,
        ConsumeRandomCounter(minimum=3, maximum=2),
        NeverRandomSource(),
    )

    assert result == Rejected(state=state, reason=RejectionReason.INVALID_RANDOM_RANGE)


def test_identical_random_input_produces_identical_transition_result() -> None:
    state = GameState(revision=0, counter=5)
    command = ConsumeRandomCounter(minimum=1, maximum=3)

    first = ENGINE.transition(state, command, FixedRandomSource(value=2))
    second = ENGINE.transition(state, command, FixedRandomSource(value=2))

    expected = Accepted(
        state=GameState(revision=1, counter=3),
        events=(CounterConsumed(amount=2),),
    )
    assert first == second == expected
    assert state == GameState(revision=0, counter=5)


def test_different_controlled_random_inputs_produce_expected_different_results() -> None:
    state = GameState(revision=0, counter=5)
    command = ConsumeRandomCounter(minimum=1, maximum=3)

    low = ENGINE.transition(state, command, FixedRandomSource(value=1))
    high = ENGINE.transition(state, command, FixedRandomSource(value=3))

    assert low == Accepted(
        state=GameState(revision=1, counter=4),
        events=(CounterConsumed(amount=1),),
    )
    assert high == Accepted(
        state=GameState(revision=1, counter=2),
        events=(CounterConsumed(amount=3),),
    )
    assert low != high
    assert state == GameState(revision=0, counter=5)


def test_broken_random_source_is_a_contract_error_and_cannot_mutate_state() -> None:
    state = GameState(revision=0, counter=5)

    with pytest.raises(ValueError, match="outside the requested bounds"):
        ENGINE.transition(
            state,
            ConsumeRandomCounter(minimum=1, maximum=3),
            OutOfRangeRandomSource(),
        )

    assert state == GameState(revision=0, counter=5)
