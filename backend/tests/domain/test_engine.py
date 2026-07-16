"""Behavioral contracts for authoritative deterministic game time."""

import pytest

from buxianxian.domain import (
    MAX_ADVANCE_DAYS,
    MAX_ELAPSED_DAYS,
    Accepted,
    AdvanceTime,
    DomainEngine,
    GameState,
    InnateAptitudes,
    PlayerCharacter,
    Rejected,
    RejectionReason,
    TimeAdvanced,
)


class NeverRandomSource:
    """Fail if deterministic time advancement unexpectedly asks for randomness."""

    def integer_inclusive(self, minimum: int, maximum: int, /) -> int:
        raise AssertionError(f"unexpected random request: [{minimum}, {maximum}]")


TEST_PLAYER = PlayerCharacter(
    name="测试角色",
    aptitudes=InnateAptitudes(5, 5, 5, 5, 5),
    trait_ids=("trait.alpha", "trait.beta"),
)
ENGINE = DomainEngine()


def _state(revision: int, elapsed_days: int) -> GameState:
    return GameState(revision=revision, elapsed_days=elapsed_days, player=TEST_PLAYER)


def test_minimal_initial_state_represents_game_start_at_day_zero() -> None:
    state = _state(revision=0, elapsed_days=0)

    assert state.revision == 0
    assert state.elapsed_days == 0
    assert state.player is TEST_PLAYER


def test_valid_time_command_returns_independent_state_and_complete_fact_event() -> None:
    state = _state(revision=0, elapsed_days=5)

    result = ENGINE.transition(state, AdvanceTime(days=2), NeverRandomSource())

    assert result == Accepted(
        state=_state(revision=1, elapsed_days=7),
        events=(
            TimeAdvanced(
                previous_elapsed_days=5,
                current_elapsed_days=7,
                days_elapsed=2,
            ),
        ),
    )
    assert result.state is not state
    assert result.state.player is state.player
    assert state == _state(revision=0, elapsed_days=5)


def test_advancing_many_days_increments_revision_exactly_once() -> None:
    state = _state(revision=8, elapsed_days=20)

    result = ENGINE.transition(state, AdvanceTime(days=30), NeverRandomSource())

    assert isinstance(result, Accepted)
    assert result.state == _state(revision=9, elapsed_days=50)


@pytest.mark.parametrize("days", [0, -1, True])
def test_invalid_day_count_is_structurally_rejected_without_mutation(days: int) -> None:
    state = _state(revision=3, elapsed_days=11)

    result = ENGINE.transition(state, AdvanceTime(days=days), NeverRandomSource())

    assert result == Rejected(state=state, reason=RejectionReason.INVALID_DAY_COUNT)
    assert result.state is state
    assert state == _state(revision=3, elapsed_days=11)


def test_single_command_above_reasonable_limit_is_rejected() -> None:
    state = _state(revision=0, elapsed_days=0)

    result = ENGINE.transition(
        state,
        AdvanceTime(days=MAX_ADVANCE_DAYS + 1),
        NeverRandomSource(),
    )

    assert result == Rejected(state=state, reason=RejectionReason.DAY_COUNT_OUT_OF_RANGE)


def test_total_elapsed_days_overflow_is_rejected_without_revision_change() -> None:
    state = _state(revision=12, elapsed_days=MAX_ELAPSED_DAYS)

    result = ENGINE.transition(state, AdvanceTime(days=1), NeverRandomSource())

    assert result == Rejected(state=state, reason=RejectionReason.DAY_COUNT_OUT_OF_RANGE)
    assert state == _state(revision=12, elapsed_days=MAX_ELAPSED_DAYS)


def test_identical_state_and_command_produce_identical_results_without_rng_use() -> None:
    state = _state(revision=4, elapsed_days=100)
    command = AdvanceTime(days=7)

    first = ENGINE.transition(state, command, NeverRandomSource())
    second = ENGINE.transition(state, command, NeverRandomSource())

    assert first == second
    assert state == _state(revision=4, elapsed_days=100)


@pytest.mark.parametrize(
    ("revision", "elapsed_days"),
    [(-1, 0), (True, 0), (0, -1), (0, True), (0, MAX_ELAPSED_DAYS + 1)],
)
def test_invalid_authoritative_state_is_rejected(revision: int, elapsed_days: int) -> None:
    with pytest.raises(ValueError):
        GameState(revision=revision, elapsed_days=elapsed_days, player=TEST_PLAYER)
