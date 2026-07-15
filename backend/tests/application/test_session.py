"""Transactional behavior tests for the headless persistent game session."""

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
    Command,
    ConsumeRandomCounter,
    DomainEngine,
    GameState,
    RandomSource,
    RejectionReason,
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


def test_session_can_start_from_explicit_state_and_rng_without_saving() -> None:
    state = GameState(revision=3, counter=8)
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


def test_session_can_start_from_existing_task002_save(tmp_path: Path) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    state = GameState(revision=5, counter=13)
    random_source = XorShift64StarRandom.from_seed(0x1234)
    random_source.integer_inclusive(1, 10)
    repository.save(state, random_source)

    session: PersistentGameSession[XorShift64StarRandom] = PersistentGameSession[
        XorShift64StarRandom
    ].from_save(repository)

    assert session.state == state
    assert session.fork_random_source().snapshot() == random_source.snapshot()


def test_valid_revision_commits_state_events_and_rng_to_memory_and_disk(tmp_path: Path) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    session: PersistentGameSession[XorShift64StarRandom] = PersistentGameSession[
        XorShift64StarRandom
    ].from_initial(
        GameState(revision=0, counter=10),
        XorShift64StarRandom.from_seed(0xCAFE),
        repository,
    )

    result = session.submit(
        ConsumeRandomCounter(minimum=1, maximum=3),
        expected_revision=0,
    )

    assert isinstance(result, CommitSucceeded)
    assert result.state.revision == 1
    assert session.state == result.state
    assert len(result.events) == 1

    loaded = repository.load()
    assert loaded.state == session.state
    assert loaded.random_source.snapshot() == session.fork_random_source().snapshot()


def test_revision_conflict_skips_domain_rng_and_persistence() -> None:
    state = GameState(revision=4, counter=10)
    random_source = XorShift64StarRandom.from_seed(23)
    original_random_state = random_source.snapshot()
    repository = RecordingRepository()
    engine = CountingDomainEngine()
    session: PersistentGameSession[XorShift64StarRandom] = PersistentGameSession[
        XorShift64StarRandom
    ].from_initial(state, random_source, repository, engine)

    result = session.submit(
        ConsumeRandomCounter(minimum=1, maximum=3),
        expected_revision=3,
    )

    assert result == RevisionConflict(expected_revision=3, actual_revision=4)
    assert engine.calls == 0
    assert repository.save_calls == 0
    assert session.state == state
    assert session.fork_random_source().snapshot() == original_random_state


def test_domain_rejection_discards_random_use_and_skips_persistence() -> None:
    state = GameState(revision=0, counter=1)
    random_source = XorShift64StarRandom.from_seed(29)
    original_random_state = random_source.snapshot()
    repository = RecordingRepository()
    engine = CountingDomainEngine()
    session: PersistentGameSession[XorShift64StarRandom] = PersistentGameSession[
        XorShift64StarRandom
    ].from_initial(state, random_source, repository, engine)

    result = session.submit(
        ConsumeRandomCounter(minimum=2, maximum=3),
        expected_revision=0,
    )

    assert result == CommandRejected(state=state, reason=RejectionReason.INSUFFICIENT_COUNTER)
    assert engine.calls == 1
    assert repository.save_calls == 0
    assert session.state == state
    assert session.fork_random_source().snapshot() == original_random_state


def test_atomic_save_failure_preserves_memory_rng_and_previous_disk_save(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    old_state = GameState(revision=2, counter=10)
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

    result = session.submit(
        ConsumeRandomCounter(minimum=1, maximum=3),
        expected_revision=2,
    )

    assert isinstance(result, PersistenceFailed)
    assert isinstance(result.error, SaveError)
    assert result.error.code is SaveErrorCode.IO_ERROR
    assert result.state == old_state
    assert session.state == old_state
    assert session.fork_random_source().snapshot() == old_random_state

    loaded = repository.load()
    assert loaded.state == old_state
    assert loaded.random_source.snapshot() == old_random_state


def test_retry_after_save_failure_reproduces_and_commits_the_same_candidate() -> None:
    state = GameState(revision=0, counter=10)
    repository = RecordingRepository(fail_saves=True)
    session: PersistentGameSession[XorShift64StarRandom] = PersistentGameSession[
        XorShift64StarRandom
    ].from_initial(
        state,
        XorShift64StarRandom.from_seed(37),
        repository,
    )
    command = ConsumeRandomCounter(minimum=1, maximum=3)
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
    assert (
        first_candidate.random_source.snapshot()
        == retry_candidate.random_source.snapshot()
        == session.fork_random_source().snapshot()
    )
