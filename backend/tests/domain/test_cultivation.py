"""Pure deterministic contracts for pre-alpha wheel-seeking cultivation."""

from dataclasses import replace

import pytest

from buxianxian.domain import (
    MAX_ELAPSED_DAYS,
    MAX_SEEK_WHEEL_DAYS,
    WHEEL_SUSPECTED_SIGHTING_THRESHOLD,
    Accepted,
    CultivationStage,
    CultivationState,
    DomainEngine,
    GameState,
    InnateAptitudes,
    PlayerCharacter,
    Rejected,
    RejectionReason,
    SeekWheel,
    WheelSeekingCompleted,
    WheelSeekingStatus,
    settle_wheel_seeking_day,
)


class SequenceRandomSource:
    """Return a finite controlled sequence and record every requested interval."""

    def __init__(self, values: list[int]) -> None:
        self._values = list(values)
        self.calls: list[tuple[int, int]] = []

    def integer_inclusive(self, minimum: int, maximum: int, /) -> int:
        self.calls.append((minimum, maximum))
        if not self._values:
            raise AssertionError("controlled random sequence was exhausted")
        value = self._values.pop(0)
        if not minimum <= value <= maximum:
            raise AssertionError(f"controlled value {value} is outside [{minimum}, {maximum}]")
        return value

    @property
    def remaining(self) -> tuple[int, ...]:
        return tuple(self._values)


def _player(aptitudes: InnateAptitudes | None = None) -> PlayerCharacter:
    return PlayerCharacter(
        name="测试角色",
        aptitudes=aptitudes or InnateAptitudes(5, 5, 5, 5, 5),
        trait_ids=("trait.alpha", "trait.beta"),
    )


def _state(
    *,
    revision: int = 0,
    elapsed_days: int = 0,
    insight: int = 0,
    aptitudes: InnateAptitudes | None = None,
) -> GameState:
    status = (
        WheelSeekingStatus.SUSPECTED_SIGHTING
        if insight == WHEEL_SUSPECTED_SIGHTING_THRESHOLD
        else WheelSeekingStatus.SEEKING
    )
    return GameState(
        revision=revision,
        elapsed_days=elapsed_days,
        player=_player(aptitudes),
        cultivation=CultivationState(
            stage=CultivationStage.SEEKING_WHEEL,
            wheel_insight=insight,
            wheel_status=status,
        ),
    )


def test_new_game_cultivation_state_starts_seeking_with_zero_insight() -> None:
    state = _state()

    assert state.cultivation == CultivationState.initial()
    assert state.cultivation.wheel_status is WheelSeekingStatus.SEEKING


def test_one_day_atomically_advances_time_insight_revision_and_event() -> None:
    state = _state(revision=4, elapsed_days=12)
    random_source = SequenceRandomSource([5, 10])

    result = DomainEngine().transition(state, SeekWheel(max_days=1), random_source)

    assert result == Accepted(
        state=_state(revision=5, elapsed_days=13, insight=8),
        events=(
            WheelSeekingCompleted(
                requested_max_days=1,
                actual_days_elapsed=1,
                previous_insight=0,
                current_insight=8,
                ordinary_insight_gained=4,
                inspiration_insight_gained=4,
                reached_suspected_sighting=False,
                previous_elapsed_days=12,
                current_elapsed_days=13,
            ),
        ),
    )
    assert result.state is not state
    assert state == _state(revision=4, elapsed_days=12)
    assert random_source.calls == [(1, 10), (1, 100)]


def test_same_inputs_produce_same_result_and_different_inspiration_rolls_differ() -> None:
    state = _state()
    command = SeekWheel(max_days=1)

    first = DomainEngine().transition(state, command, SequenceRandomSource([9, 10]))
    second = DomainEngine().transition(state, command, SequenceRandomSource([9, 10]))
    without_inspiration = DomainEngine().transition(
        state,
        command,
        SequenceRandomSource([9, 11]),
    )

    assert first == second
    assert isinstance(first, Accepted)
    assert isinstance(without_inspiration, Accepted)
    assert first.state.cultivation.wheel_insight == 7
    assert without_inspiration.state.cultivation.wheel_insight == 3


def test_pre_alpha_formula_uses_each_declared_aptitude_except_constitution() -> None:
    def settle(
        *,
        comprehension: int = 1,
        spiritual_sense: int = 1,
        temperament: int = 1,
        fortune: int = 1,
        rolls: list[int],
    ) -> tuple[int, int]:
        result = settle_wheel_seeking_day(
            comprehension=comprehension,
            spiritual_sense=spiritual_sense,
            temperament=temperament,
            fortune=fortune,
            random_source=SequenceRandomSource(rolls),
        )
        return result.ordinary_insight, result.inspiration_insight

    assert (
        settle(comprehension=10, rolls=[10, 100])[0] > settle(comprehension=1, rolls=[10, 100])[0]
    )
    assert (
        settle(spiritual_sense=10, rolls=[5, 100])[0] > settle(spiritual_sense=1, rolls=[5, 100])[0]
    )
    assert settle(temperament=10, rolls=[10, 100])[0] > settle(temperament=1, rolls=[10, 100])[0]
    assert settle(fortune=10, rolls=[10, 15])[1] > settle(fortune=1, rolls=[10, 15])[1]


def test_daily_formula_stays_within_documented_integer_bounds() -> None:
    for comprehension in range(1, 11):
        for spiritual_sense in range(1, 11):
            for temperament in range(1, 11):
                for fortune in range(1, 11):
                    result = settle_wheel_seeking_day(
                        comprehension=comprehension,
                        spiritual_sense=spiritual_sense,
                        temperament=temperament,
                        fortune=fortune,
                        random_source=SequenceRandomSource([spiritual_sense, fortune * 2]),
                    )
                    assert 1 <= result.ordinary_insight <= 7
                    assert 3 <= result.inspiration_insight <= 5


def test_suspected_sighting_stops_early_and_caps_insight() -> None:
    state = _state(elapsed_days=20, insight=95)
    random_source = SequenceRandomSource([1, 1, 1, 1])

    result = DomainEngine().transition(state, SeekWheel(max_days=30), random_source)

    assert isinstance(result, Accepted)
    assert result.state.elapsed_days == 21
    assert result.state.revision == 1
    assert result.state.cultivation.wheel_insight == WHEEL_SUSPECTED_SIGHTING_THRESHOLD
    assert result.state.cultivation.wheel_status is WheelSeekingStatus.SUSPECTED_SIGHTING
    event = result.events[0]
    assert isinstance(event, WheelSeekingCompleted)
    assert event.actual_days_elapsed == 1
    assert event.ordinary_insight_gained + event.inspiration_insight_gained == 5
    assert event.reached_suspected_sighting is True
    assert random_source.calls == [(1, 10), (1, 100)]
    assert random_source.remaining == (1, 1)


def test_batch_and_one_day_commands_have_equal_core_result_and_rng_position() -> None:
    values = [5, 99, 5, 10, 9, 99, 1, 1, 10, 99, 4, 99, 8, 99]
    batch_random = SequenceRandomSource(values)
    daily_random = SequenceRandomSource(values)
    initial = _state()

    batch = DomainEngine().transition(initial, SeekWheel(max_days=7), batch_random)
    assert isinstance(batch, Accepted)

    daily_state = initial
    for _ in range(7):
        daily = DomainEngine().transition(
            daily_state,
            SeekWheel(max_days=1),
            daily_random,
        )
        assert isinstance(daily, Accepted)
        daily_state = daily.state
        if daily_state.cultivation.wheel_status is WheelSeekingStatus.SUSPECTED_SIGHTING:
            break

    assert batch.state.elapsed_days == daily_state.elapsed_days
    assert batch.state.cultivation == daily_state.cultivation
    assert batch_random.calls == daily_random.calls
    assert batch_random.remaining == daily_random.remaining


@pytest.mark.parametrize("max_days", [0, -1, True])
def test_invalid_seek_day_count_rejects_without_state_or_rng_change(max_days: int) -> None:
    state = _state(revision=3, elapsed_days=9)
    random_source = SequenceRandomSource([1, 1])

    result = DomainEngine().transition(state, SeekWheel(max_days=max_days), random_source)

    assert result == Rejected(
        state=state,
        reason=RejectionReason.INVALID_SEEK_WHEEL_DAY_COUNT,
    )
    assert result.state is state
    assert random_source.calls == []


def test_out_of_range_and_total_time_overflow_reject_without_rng() -> None:
    state = _state(elapsed_days=MAX_ELAPSED_DAYS)
    random_source = SequenceRandomSource([1, 1])

    too_many = DomainEngine().transition(
        _state(),
        SeekWheel(max_days=MAX_SEEK_WHEEL_DAYS + 1),
        random_source,
    )
    overflow = DomainEngine().transition(state, SeekWheel(max_days=1), random_source)

    expected = RejectionReason.SEEK_WHEEL_DAY_COUNT_OUT_OF_RANGE
    assert too_many == Rejected(state=_state(), reason=expected)
    assert overflow == Rejected(state=state, reason=expected)
    assert random_source.calls == []


def test_already_suspected_sighting_rejects_without_time_revision_or_rng() -> None:
    state = _state(revision=7, elapsed_days=40, insight=100)
    random_source = SequenceRandomSource([1, 1])

    result = DomainEngine().transition(state, SeekWheel(max_days=7), random_source)

    assert result == Rejected(
        state=state,
        reason=RejectionReason.WHEEL_ALREADY_SUSPECTED,
    )
    assert result.state is state
    assert random_source.calls == []


def test_cultivation_state_rejects_inconsistent_status_or_insight() -> None:
    with pytest.raises(ValueError):
        CultivationState(
            stage=CultivationStage.SEEKING_WHEEL,
            wheel_insight=99,
            wheel_status=WheelSeekingStatus.SUSPECTED_SIGHTING,
        )
    with pytest.raises(ValueError):
        replace(CultivationState.initial(), wheel_insight=101)
