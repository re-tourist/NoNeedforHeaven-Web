"""Transactional behavior tests for authoritative time in a persistent session."""

from pathlib import Path

import pytest

import buxianxian.infrastructure.save_repository as save_repository_module
from buxianxian.application import (
    CommandRejected,
    CommitSucceeded,
    PersistenceError,
    PersistenceFailed,
    PersistentGameSession,
    RevisionConflict,
)
from buxianxian.domain import (
    AdvanceTime,
    Command,
    DomainEngine,
    GameState,
    RandomSource,
    RejectionReason,
    TimeAdvanced,
    TransitionResult,
)
from buxianxian.infrastructure import (
    JsonFileSaveRepository,
    LoadedSave,
    SaveError,
    SaveErrorCode,
    XorShift64StarRandom,
)


class CountingDomainEngine(DomainEngine):
    """Record whether a submission reached domain execution."""

    calls: int

    def __init__(self) -> None:
        self.calls = 0

    def transition(
        self,
        state: GameState,
        command: Command,
        random_source: RandomSource,
    ) -> TransitionResult:
        self.calls += 1
        return super().transition(state, command, random_source)


class RecordingRepository:
    """Small in-memory repository double with observable save attempts."""

    save_calls: int
    fail_saves: bool
    attempts: list[LoadedSave]
    _loaded: LoadedSave | None

    def __init__(self, loaded: LoadedSave | None = None, *, fail_saves: bool = False) -> None:
        self.save_calls = 0
        self.fail_saves = fail_saves
        self.attempts = []
        self._loaded = loaded

    def save(self, state: GameState, random_source: XorShift64StarRandom) -> None:
        self.save_calls += 1
        attempted = LoadedSave(state=state, random_source=random_source.fork())
        self.attempts.append(attempted)
        if self.fail_saves:
            raise PersistenceError("simulated persistence failure")
        self._loaded = attempted

    def load(self) -> LoadedSave:
        if self._loaded is None:
            raise PersistenceError("no in-memory save")
        return LoadedSave(
            state=self._loaded.state,
            random_source=self._loaded.random_source.fork(),
        )


def test_session_can_start_from_explicit_formal_state_and_rng_without_saving() -> None:
    state = GameState(revision=3, elapsed_days=8)
    random_source = XorShift64StarRandom.from_seed(11)
    repository = RecordingRepository()

    session: PersistentGameSession[XorShift64StarRandom] = PersistentGameSession[
        XorShift64StarRandom
    ].from_initial(state, random_source, repository)

    assert session.state == state
    assert session.fork_random_source().snapshot() == random_source.snapshot()
    assert repository.save_calls == 0

    exposed_fork = session.fork_random_source()
    exposed_fork.integer_inclusive(1, 3)
    assert session.fork_random_source().snapshot() == random_source.snapshot()


def test_session_can_start_from_existing_schema_v2_save(tmp_path: Path) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    state = GameState(revision=5, elapsed_days=13)
    random_source = XorShift64StarRandom.from_seed(0x1234)
    random_source.integer_inclusive(1, 10)
    repository.save(state, random_source)

    session: PersistentGameSession[XorShift64StarRandom] = PersistentGameSession[
        XorShift64StarRandom
    ].from_save(repository)

    assert session.state == state
    assert session.fork_random_source().snapshot() == random_source.snapshot()


def test_valid_revision_commits_time_to_memory_and_disk_without_advancing_rng(
    tmp_path: Path,
) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    random_source = XorShift64StarRandom.from_seed(0xCAFE)
    original_random_state = random_source.snapshot()
    session: PersistentGameSession[XorShift64StarRandom] = PersistentGameSession[
        XorShift64StarRandom
    ].from_initial(
        GameState(revision=0, elapsed_days=10),
        random_source,
        repository,
    )

    result = session.submit(AdvanceTime(days=3), expected_revision=0)

    assert isinstance(result, CommitSucceeded)
    assert result == CommitSucceeded(
        state=GameState(revision=1, elapsed_days=13),
        events=(
            TimeAdvanced(
                previous_elapsed_days=10,
                current_elapsed_days=13,
                days_elapsed=3,
            ),
        ),
    )
    assert session.state == result.state
    assert session.fork_random_source().snapshot() == original_random_state

    loaded = repository.load()
    assert loaded.state == session.state
    assert loaded.random_source.snapshot() == original_random_state


def test_revision_conflict_does_not_advance_time_rng_or_persistence() -> None:
    state = GameState(revision=4, elapsed_days=10)
    random_source = XorShift64StarRandom.from_seed(23)
    original_random_state = random_source.snapshot()
    repository = RecordingRepository()
    engine = CountingDomainEngine()
    session: PersistentGameSession[XorShift64StarRandom] = PersistentGameSession[
        XorShift64StarRandom
    ].from_initial(state, random_source, repository, engine)

    result = session.submit(AdvanceTime(days=2), expected_revision=3)

    assert result == RevisionConflict(expected_revision=3, actual_revision=4)
    assert engine.calls == 0
    assert repository.save_calls == 0
    assert session.state == state
    assert session.fork_random_source().snapshot() == original_random_state


def test_domain_rejection_preserves_time_rng_and_skips_persistence() -> None:
    state = GameState(revision=0, elapsed_days=1)
    random_source = XorShift64StarRandom.from_seed(29)
    original_random_state = random_source.snapshot()
    repository = RecordingRepository()
    engine = CountingDomainEngine()
    session: PersistentGameSession[XorShift64StarRandom] = PersistentGameSession[
        XorShift64StarRandom
    ].from_initial(state, random_source, repository, engine)

    result = session.submit(AdvanceTime(days=0), expected_revision=0)

    assert result == CommandRejected(state=state, reason=RejectionReason.INVALID_DAY_COUNT)
    assert engine.calls == 1
    assert repository.save_calls == 0
    assert session.state == state
    assert session.fork_random_source().snapshot() == original_random_state


def test_atomic_save_failure_preserves_time_memory_rng_and_previous_disk_save(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    old_state = GameState(revision=2, elapsed_days=10)
    old_random = XorShift64StarRandom.from_seed(31)
    repository.save(old_state, old_random)
    session: PersistentGameSession[XorShift64StarRandom] = PersistentGameSession[
        XorShift64StarRandom
    ].from_save(repository)
    old_random_state = session.fork_random_source().snapshot()

    def fail_replace(source: Path, target: Path) -> None:
        del source, target
        raise OSError("simulated replacement failure")

    monkeypatch.setattr(save_repository_module, "_replace_file", fail_replace)

    result = session.submit(AdvanceTime(days=4), expected_revision=2)

    assert isinstance(result, PersistenceFailed)
    assert isinstance(result.error, SaveError)
    assert result.error.code is SaveErrorCode.IO_ERROR
    assert result.state == old_state
    assert session.state == old_state
    assert session.fork_random_source().snapshot() == old_random_state

    loaded = repository.load()
    assert loaded.state == old_state
    assert loaded.random_source.snapshot() == old_random_state


def test_retry_after_save_failure_commits_the_same_time_and_rng_candidate() -> None:
    state = GameState(revision=0, elapsed_days=10)
    repository = RecordingRepository(fail_saves=True)
    session: PersistentGameSession[XorShift64StarRandom] = PersistentGameSession[
        XorShift64StarRandom
    ].from_initial(
        state,
        XorShift64StarRandom.from_seed(37),
        repository,
    )
    command = AdvanceTime(days=3)
    official_random_state = session.fork_random_source().snapshot()

    first_result = session.submit(command, expected_revision=0)
    first_candidate = repository.attempts[0]

    assert isinstance(first_result, PersistenceFailed)
    assert session.state == state
    assert session.fork_random_source().snapshot() == official_random_state

    repository.fail_saves = False
    retry_result = session.submit(command, expected_revision=0)
    retry_candidate = repository.attempts[1]

    assert isinstance(retry_result, CommitSucceeded)
    assert retry_result.state == first_candidate.state == retry_candidate.state
    assert retry_result.state == GameState(revision=1, elapsed_days=13)
    assert (
        first_candidate.random_source.snapshot()
        == retry_candidate.random_source.snapshot()
        == session.fork_random_source().snapshot()
        == official_random_state
    )
