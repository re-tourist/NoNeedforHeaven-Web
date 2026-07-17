"""Single-save runtime lifecycle, overwrite, restart, and command tests."""

from pathlib import Path

from buxianxian.application import (
    CommitSucceeded,
    DraftCreated,
    DraftNotFound,
    GameLoaded,
    InitialSaveFailed,
    NewGameCreated,
    NewGameRejected,
    NoActiveSession,
    PersistenceError,
    SaveOverwriteRequired,
    SingleGameRuntime,
)
from buxianxian.domain import (
    CharacterCreationErrorCode,
    GameState,
    InnateAptitudes,
    PlayerCharacter,
)
from buxianxian.infrastructure import (
    PROTOTYPE_TRAIT_CATALOG,
    JsonFileSaveRepository,
    LoadedSave,
    XorShift64StarRandom,
)


class FixedRandomFactory:
    """Return deterministic fresh RNGs while recording creation count."""

    calls: int

    def __init__(self, seed: int) -> None:
        self._seed = seed
        self.calls = 0

    def create(self) -> XorShift64StarRandom:
        self.calls += 1
        return XorShift64StarRandom.from_seed(self._seed + self.calls - 1)


class SequentialDraftIds:
    """Return stable opaque identifiers for application tests."""

    calls: int

    def __init__(self) -> None:
        self.calls = 0

    def create(self) -> str:
        self.calls += 1
        return f"opaque-draft-{self.calls}"


class FailingSaveRepository:
    """Single-save double that fails every persistence attempt."""

    def exists(self) -> bool:
        return False

    def save(self, state: GameState, random_source: XorShift64StarRandom) -> None:
        del state, random_source
        raise PersistenceError("simulated save failure")

    def load(self) -> LoadedSave:
        raise PersistenceError("no save")


def _runtime(
    repository: JsonFileSaveRepository | FailingSaveRepository,
    *,
    seed: int = 100,
) -> SingleGameRuntime[XorShift64StarRandom]:
    return SingleGameRuntime[XorShift64StarRandom](
        repository=repository,
        trait_catalog=PROTOTYPE_TRAIT_CATALOG,
        random_source_factory=FixedRandomFactory(seed),
        draft_identifier_source=SequentialDraftIds(),
    )


def _selection(draft: DraftCreated) -> tuple[str, tuple[str, str]]:
    return (
        draft.candidates.aptitude_options[0].option_id,
        (
            draft.candidates.trait_options[0].trait_id,
            draft.candidates.trait_options[1].trait_id,
        ),
    )


def _old_state() -> GameState:
    return GameState(
        revision=4,
        elapsed_days=9,
        player=PlayerCharacter(
            name="旧角色",
            aptitudes=InnateAptitudes(5, 5, 5, 5, 5),
            trait_ids=("prototype.calm", "prototype.steady"),
        ),
    )


def test_status_distinguishes_no_save_available_save_and_active_session(tmp_path: Path) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    runtime = _runtime(repository)

    empty = runtime.inspect_status()
    assert not empty.save_exists
    assert not empty.save_available
    assert not empty.session_active
    assert empty.state is None

    repository.save(_old_state(), XorShift64StarRandom.from_seed(77))
    available = runtime.inspect_status()
    assert available.save_exists
    assert available.save_available
    assert not available.session_active
    assert available.state is None

    loaded = runtime.load_game()
    assert isinstance(loaded, GameLoaded)
    active = runtime.inspect_status()
    assert active.save_exists
    assert active.save_available
    assert active.session_active
    assert active.state == _old_state()


def test_new_draft_has_required_candidates_and_invalidates_previous_draft(
    tmp_path: Path,
) -> None:
    runtime = _runtime(JsonFileSaveRepository(tmp_path / "save.json"))

    first = runtime.create_draft()
    second = runtime.create_draft()

    assert isinstance(first, DraftCreated)
    assert isinstance(second, DraftCreated)
    assert first.draft_id != second.draft_id
    assert len(second.candidates.aptitude_options) == 3
    assert len(second.candidates.trait_options) == 6
    option_id, trait_ids = _selection(first)
    stale = runtime.confirm_new_game(
        first.draft_id,
        "测试者",
        option_id,
        trait_ids,
        overwrite_existing_save=False,
    )
    assert isinstance(stale, DraftNotFound)


def test_forged_aptitude_selection_is_revalidated_by_server_draft(tmp_path: Path) -> None:
    runtime = _runtime(JsonFileSaveRepository(tmp_path / "save.json"))
    draft = runtime.create_draft()
    assert isinstance(draft, DraftCreated)
    _, trait_ids = _selection(draft)

    result = runtime.confirm_new_game(
        draft.draft_id,
        "测试者",
        "forged-option",
        trait_ids,
        overwrite_existing_save=False,
    )

    assert result == NewGameRejected(CharacterCreationErrorCode.INVALID_APTITUDE_SELECTION)
    assert not runtime.inspect_status().session_active


def test_existing_save_requires_consent_and_remains_unchanged_without_it(tmp_path: Path) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    old_random = XorShift64StarRandom.from_seed(81)
    repository.save(_old_state(), old_random)
    runtime = _runtime(repository)
    draft = runtime.create_draft()
    assert isinstance(draft, DraftCreated)
    option_id, trait_ids = _selection(draft)

    result = runtime.confirm_new_game(
        draft.draft_id,
        "新角色",
        option_id,
        trait_ids,
        overwrite_existing_save=False,
    )

    assert isinstance(result, SaveOverwriteRequired)
    loaded = repository.load()
    assert loaded.state == _old_state()
    assert loaded.random_source.snapshot() == old_random.snapshot()
    assert not runtime.inspect_status().session_active


def test_explicit_overwrite_persists_new_game_and_activates_session(tmp_path: Path) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    repository.save(_old_state(), XorShift64StarRandom.from_seed(83))
    runtime = _runtime(repository)
    draft = runtime.create_draft()
    assert isinstance(draft, DraftCreated)
    option_id, trait_ids = _selection(draft)

    result = runtime.confirm_new_game(
        draft.draft_id,
        "新角色",
        option_id,
        trait_ids,
        overwrite_existing_save=True,
    )

    assert isinstance(result, NewGameCreated)
    assert result.session.state.player.name == "新角色"
    assert repository.load().state == result.session.state
    assert runtime.active_session is result.session


def test_save_failure_creates_no_session_and_retains_draft_for_retry() -> None:
    runtime = _runtime(FailingSaveRepository())
    draft = runtime.create_draft()
    assert isinstance(draft, DraftCreated)
    option_id, trait_ids = _selection(draft)

    first = runtime.confirm_new_game(
        draft.draft_id,
        "测试者",
        option_id,
        trait_ids,
        overwrite_existing_save=False,
    )
    second = runtime.confirm_new_game(
        draft.draft_id,
        "测试者",
        option_id,
        trait_ids,
        overwrite_existing_save=False,
    )

    assert isinstance(first, InitialSaveFailed)
    assert isinstance(second, InitialSaveFailed)
    assert runtime.active_session is None


def test_process_restart_loads_equal_state_and_exact_rng_position(tmp_path: Path) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    first_runtime = _runtime(repository, seed=211)
    draft = first_runtime.create_draft()
    assert isinstance(draft, DraftCreated)
    option_id, trait_ids = _selection(draft)
    created = first_runtime.confirm_new_game(
        draft.draft_id,
        "测试者",
        option_id,
        trait_ids,
        overwrite_existing_save=False,
    )
    assert isinstance(created, NewGameCreated)
    expected_state = created.session.state
    expected_random = created.session.fork_random_source().snapshot()

    restarted_runtime = _runtime(JsonFileSaveRepository(repository.path), seed=999)
    loaded = restarted_runtime.load_game()

    assert loaded == GameLoaded(expected_state)
    assert restarted_runtime.active_session is not None
    assert restarted_runtime.active_session.fork_random_source().snapshot() == expected_random


def test_wait_requires_session_then_commits_authoritative_time(tmp_path: Path) -> None:
    runtime = _runtime(JsonFileSaveRepository(tmp_path / "save.json"))
    assert isinstance(runtime.wait(days=2, expected_revision=0), NoActiveSession)

    draft = runtime.create_draft()
    assert isinstance(draft, DraftCreated)
    option_id, trait_ids = _selection(draft)
    created = runtime.confirm_new_game(
        draft.draft_id,
        "测试者",
        option_id,
        trait_ids,
        overwrite_existing_save=False,
    )
    assert isinstance(created, NewGameCreated)

    waited = runtime.wait(days=3, expected_revision=0)

    assert isinstance(waited, CommitSucceeded)
    assert waited.state.elapsed_days == 3
    assert waited.state.revision == 1


def test_seek_wheel_requires_session_then_commits_state_time_and_rng(
    tmp_path: Path,
) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    runtime = _runtime(repository, seed=307)
    assert isinstance(
        runtime.seek_wheel(max_days=1, expected_revision=0),
        NoActiveSession,
    )

    draft = runtime.create_draft()
    assert isinstance(draft, DraftCreated)
    option_id, trait_ids = _selection(draft)
    created = runtime.confirm_new_game(
        draft.draft_id,
        "测试者",
        option_id,
        trait_ids,
        overwrite_existing_save=False,
    )
    assert isinstance(created, NewGameCreated)
    before_random = created.session.fork_random_source().snapshot()

    cultivated = runtime.seek_wheel(max_days=7, expected_revision=0)

    assert isinstance(cultivated, CommitSucceeded)
    assert cultivated.state.elapsed_days == 7
    assert cultivated.state.revision == 1
    assert cultivated.state.cultivation.wheel_insight > 0
    assert created.session.fork_random_source().snapshot() != before_random
    loaded = repository.load()
    assert loaded.state == cultivated.state
    assert loaded.random_source.snapshot() == created.session.fork_random_source().snapshot()
