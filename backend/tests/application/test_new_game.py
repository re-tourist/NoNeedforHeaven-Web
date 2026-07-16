"""Pre-session new-game RNG, validation, persistence, and session tests."""

from dataclasses import dataclass
from pathlib import Path

from buxianxian.application import (
    CharacterCreationPreparationFailed,
    CharacterCreationPrepared,
    InitialSaveFailed,
    NewGameCreated,
    NewGameRejected,
    NewGameService,
    PersistenceError,
)
from buxianxian.domain import CharacterCreationErrorCode, GameState, TraitDefinition
from buxianxian.infrastructure import JsonFileSaveRepository, XorShift64StarRandom


@dataclass(frozen=True, slots=True)
class LoadedRecord:
    """Structurally compatible loaded state for the application test repository."""

    state: GameState
    random_source: XorShift64StarRandom


class RecordingRepository:
    """Small persistence double that records complete state/RNG save attempts."""

    save_calls: int
    fail_saves: bool
    saved: list[LoadedRecord]

    def __init__(self, *, fail_saves: bool = False) -> None:
        self.save_calls = 0
        self.fail_saves = fail_saves
        self.saved = []

    def save(self, state: GameState, random_source: XorShift64StarRandom) -> None:
        self.save_calls += 1
        self.saved.append(LoadedRecord(state, random_source.fork()))
        if self.fail_saves:
            raise PersistenceError("simulated initial save failure")

    def load(self) -> LoadedRecord:
        if not self.saved:
            raise PersistenceError("no saved record")
        saved = self.saved[-1]
        return LoadedRecord(saved.state, saved.random_source.fork())


def _trait_catalog(count: int = 8) -> tuple[TraitDefinition, ...]:
    return tuple(
        TraitDefinition(
            trait_id=f"trait.test_{index}",
            name=f"测试词条{index}",
            description=f"用于验证新游戏事务的中性说明{index}",
        )
        for index in range(1, count + 1)
    )


def _prepare(
    repository: RecordingRepository,
    random_source: XorShift64StarRandom,
) -> tuple[
    NewGameService[XorShift64StarRandom],
    CharacterCreationPrepared[XorShift64StarRandom],
]:
    service = NewGameService[XorShift64StarRandom](repository, _trait_catalog())
    preparation = service.begin(random_source)
    assert isinstance(preparation, CharacterCreationPrepared)
    return service, preparation


def _valid_selection(
    preparation: CharacterCreationPrepared[XorShift64StarRandom],
) -> tuple[str, tuple[str, str]]:
    candidates = preparation.draft.candidates
    return (
        candidates.aptitude_options[0].option_id,
        (
            candidates.trait_options[0].trait_id,
            candidates.trait_options[1].trait_id,
        ),
    )


def test_begin_uses_fork_and_keeps_caller_rng_unchanged() -> None:
    repository = RecordingRepository()
    random_source = XorShift64StarRandom.from_seed(101)
    original_snapshot = random_source.snapshot()

    _, preparation = _prepare(repository, random_source)

    assert random_source.snapshot() == original_snapshot
    assert preparation.draft.fork_random_source().snapshot() != original_snapshot
    assert repository.save_calls == 0


def test_insufficient_catalog_fails_without_advancing_caller_rng() -> None:
    repository = RecordingRepository()
    random_source = XorShift64StarRandom.from_seed(103)
    original_snapshot = random_source.snapshot()
    service = NewGameService[XorShift64StarRandom](repository, _trait_catalog(count=5))

    result = service.begin(random_source)

    assert result == CharacterCreationPreparationFailed(
        CharacterCreationErrorCode.INSUFFICIENT_TRAITS
    )
    assert random_source.snapshot() == original_snapshot
    assert repository.save_calls == 0


def test_failed_confirmation_does_not_advance_draft_rng_or_save() -> None:
    repository = RecordingRepository()
    service, preparation = _prepare(
        repository,
        XorShift64StarRandom.from_seed(107),
    )
    draft_snapshot = preparation.draft.fork_random_source().snapshot()
    aptitude_option_id, trait_ids = _valid_selection(preparation)

    result = service.confirm(
        preparation.draft,
        name="   ",
        aptitude_option_id=aptitude_option_id,
        selected_trait_ids=trait_ids,
    )

    assert result == NewGameRejected(CharacterCreationErrorCode.INVALID_NAME)
    assert preparation.draft.fork_random_source().snapshot() == draft_snapshot
    assert repository.save_calls == 0


def test_success_saves_post_generation_rng_before_exposing_session() -> None:
    repository = RecordingRepository()
    original_random = XorShift64StarRandom.from_seed(109)
    original_snapshot = original_random.snapshot()
    service, preparation = _prepare(repository, original_random)
    aptitude_option_id, trait_ids = _valid_selection(preparation)
    post_generation_snapshot = preparation.draft.fork_random_source().snapshot()

    result = service.confirm(
        preparation.draft,
        name="  测试者  ",
        aptitude_option_id=aptitude_option_id,
        selected_trait_ids=trait_ids,
    )

    assert isinstance(result, NewGameCreated)
    assert repository.save_calls == 1
    assert result.session.state == repository.saved[0].state
    assert result.session.state.revision == 0
    assert result.session.state.elapsed_days == 0
    assert result.session.state.player.name == "测试者"
    assert result.session.fork_random_source().snapshot() == post_generation_snapshot
    assert repository.saved[0].random_source.snapshot() == post_generation_snapshot
    assert original_random.snapshot() == original_snapshot


def test_real_initial_save_loads_complete_profile_and_post_generation_rng(tmp_path: Path) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    service = NewGameService[XorShift64StarRandom](repository, _trait_catalog())
    preparation = service.begin(XorShift64StarRandom.from_seed(111))
    assert isinstance(preparation, CharacterCreationPrepared)
    aptitude_option_id, trait_ids = _valid_selection(preparation)
    expected_random_state = preparation.draft.fork_random_source().snapshot()

    result = service.confirm(
        preparation.draft,
        "测试者",
        aptitude_option_id,
        trait_ids,
    )

    assert isinstance(result, NewGameCreated)
    loaded = repository.load()
    assert loaded.state == result.session.state
    assert loaded.state.player.name == "测试者"
    assert loaded.state.player.aptitudes == (
        preparation.draft.candidates.aptitude_options[0].aptitudes
    )
    assert loaded.state.player.trait_ids == tuple(sorted(trait_ids))
    assert loaded.random_source.snapshot() == expected_random_state
    assert result.session.fork_random_source().snapshot() == expected_random_state


def test_initial_save_failure_creates_no_session_and_supports_deterministic_retry() -> None:
    repository = RecordingRepository(fail_saves=True)
    service, preparation = _prepare(
        repository,
        XorShift64StarRandom.from_seed(113),
    )
    aptitude_option_id, trait_ids = _valid_selection(preparation)
    draft_snapshot = preparation.draft.fork_random_source().snapshot()

    failed = service.confirm(
        preparation.draft,
        "测试者",
        aptitude_option_id,
        trait_ids,
    )
    first_attempt = repository.saved[0]

    assert isinstance(failed, InitialSaveFailed)
    assert preparation.draft.fork_random_source().snapshot() == draft_snapshot

    repository.fail_saves = False
    retried = service.confirm(
        preparation.draft,
        "测试者",
        aptitude_option_id,
        trait_ids,
    )
    second_attempt = repository.saved[1]

    assert isinstance(retried, NewGameCreated)
    assert retried.session.state == first_attempt.state == second_attempt.state
    assert (
        retried.session.fork_random_source().snapshot()
        == first_attempt.random_source.snapshot()
        == second_attempt.random_source.snapshot()
        == draft_snapshot
    )
