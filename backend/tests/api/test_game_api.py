"""FastAPI integration tests for the first complete single-save game loop."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import buxianxian.infrastructure.save_repository as save_repository_module
from buxianxian.api.app import create_app
from buxianxian.api.contracts import (
    ApiErrorCode,
    ApiErrorResponse,
    CharacterDraftResponse,
    CultivationEnvelope,
    GameStatusResponse,
    StateEnvelope,
)
from buxianxian.application import PersistenceError, SingleGameRuntime
from buxianxian.domain import GameState, InnateAptitudes, PlayerCharacter
from buxianxian.infrastructure import (
    PROTOTYPE_TRAIT_CATALOG,
    JsonFileSaveRepository,
    LoadedSave,
    XorShift64StarRandom,
)


class FixedRandomFactory:
    """Create deterministic fresh game RNGs for HTTP integration tests."""

    def __init__(self, seed: int = 500) -> None:
        self._seed = seed

    def create(self) -> XorShift64StarRandom:
        return XorShift64StarRandom.from_seed(self._seed)


class FixedDraftIds:
    """Return incrementing opaque identifiers for predictable API assertions."""

    calls: int

    def __init__(self) -> None:
        self.calls = 0

    def create(self) -> str:
        self.calls += 1
        return f"http-draft-{self.calls}"


class FailingSaveRepository:
    """Repository double for API persistence-failure projection."""

    def exists(self) -> bool:
        return False

    def save(self, state: GameState, random_source: XorShift64StarRandom) -> None:
        del state, random_source
        raise PersistenceError("D:/private/path/must-not-leak")

    def load(self) -> LoadedSave:
        raise PersistenceError("D:/private/path/must-not-leak")


def _runtime(
    repository: JsonFileSaveRepository | FailingSaveRepository,
    *,
    seed: int = 500,
) -> SingleGameRuntime[XorShift64StarRandom]:
    return SingleGameRuntime[XorShift64StarRandom](
        repository=repository,
        trait_catalog=PROTOTYPE_TRAIT_CATALOG,
        random_source_factory=FixedRandomFactory(seed),
        draft_identifier_source=FixedDraftIds(),
    )


def _client(
    repository: JsonFileSaveRepository | FailingSaveRepository,
    *,
    seed: int = 500,
) -> tuple[TestClient, SingleGameRuntime[XorShift64StarRandom]]:
    runtime = _runtime(repository, seed=seed)
    return TestClient(create_app(runtime)), runtime


def _saved_state() -> GameState:
    return GameState(
        revision=3,
        elapsed_days=12,
        player=PlayerCharacter(
            name="已有角色",
            aptitudes=InnateAptitudes(5, 5, 5, 5, 5),
            trait_ids=("prototype.calm", "prototype.steady"),
        ),
    )


def _create_draft(client: TestClient) -> CharacterDraftResponse:
    response = client.post("/api/game/drafts")
    assert response.status_code == 201
    return CharacterDraftResponse.model_validate_json(response.text)


def _confirmation_payload(
    draft: CharacterDraftResponse,
    *,
    overwrite: bool = False,
) -> dict[str, object]:
    return {
        "draft_id": draft.draft_id,
        "name": "网页角色",
        "aptitude_option_id": draft.aptitude_options[0].option_id,
        "trait_ids": [
            draft.trait_options[0].trait_id,
            draft.trait_options[1].trait_id,
        ],
        "overwrite_existing_save": overwrite,
    }


def test_status_distinguishes_no_save_available_save_and_active_session(tmp_path: Path) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    client, _ = _client(repository)

    no_save = GameStatusResponse.model_validate_json(client.get("/api/game").text)
    assert not no_save.save_exists
    assert not no_save.save_available
    assert not no_save.session_active
    assert no_save.state is None

    repository.save(_saved_state(), XorShift64StarRandom.from_seed(41))
    available = GameStatusResponse.model_validate_json(client.get("/api/game").text)
    assert available.save_exists
    assert available.save_available
    assert not available.session_active

    loaded_response = client.post("/api/game/load")
    assert loaded_response.status_code == 200
    active = GameStatusResponse.model_validate_json(client.get("/api/game").text)
    assert active.session_active
    assert active.state is not None
    assert active.state.player.name == "已有角色"


def test_draft_returns_three_aptitudes_six_traits_without_private_runtime_data(
    tmp_path: Path,
) -> None:
    client, _ = _client(JsonFileSaveRepository(tmp_path / "private" / "save.json"))

    response = client.post("/api/game/drafts")
    draft = CharacterDraftResponse.model_validate_json(response.text)

    assert response.status_code == 201
    assert len(draft.aptitude_options) == 3
    assert len(draft.trait_options) == 6
    assert draft.required_trait_count == 2
    assert "random" not in response.text.lower()
    assert "private" not in response.text.lower()
    assert str(tmp_path) not in response.text


def test_new_draft_invalidates_old_identifier(tmp_path: Path) -> None:
    client, _ = _client(JsonFileSaveRepository(tmp_path / "save.json"))
    first = _create_draft(client)
    second = _create_draft(client)

    response = client.post("/api/game/new", json=_confirmation_payload(first))
    error = ApiErrorResponse.model_validate_json(response.text)

    assert first.draft_id != second.draft_id
    assert response.status_code == 404
    assert error.error.code is ApiErrorCode.DRAFT_NOT_FOUND


def test_client_cannot_forge_aptitudes_or_traits(tmp_path: Path) -> None:
    client, _ = _client(JsonFileSaveRepository(tmp_path / "save.json"))
    draft = _create_draft(client)
    forged_aptitude = _confirmation_payload(draft)
    forged_aptitude["aptitude_option_id"] = "forged-option"

    aptitude_response = client.post("/api/game/new", json=forged_aptitude)
    aptitude_error = ApiErrorResponse.model_validate_json(aptitude_response.text)

    forged_trait = _confirmation_payload(draft)
    forged_trait["trait_ids"] = [draft.trait_options[0].trait_id, "prototype.forged"]
    trait_response = client.post("/api/game/new", json=forged_trait)
    trait_error = ApiErrorResponse.model_validate_json(trait_response.text)

    assert aptitude_response.status_code == 422
    assert aptitude_error.error.code is ApiErrorCode.INVALID_APTITUDE_SELECTION
    assert trait_response.status_code == 422
    assert trait_error.error.code is ApiErrorCode.INVALID_TRAIT_SELECTION


def test_valid_draft_creates_persists_and_projects_complete_new_game(tmp_path: Path) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    client, runtime = _client(repository)
    draft = _create_draft(client)

    response = client.post("/api/game/new", json=_confirmation_payload(draft))
    created = StateEnvelope.model_validate_json(response.text)

    assert response.status_code == 201
    assert created.state.revision == 0
    assert created.state.elapsed_days == 0
    assert created.state.player.name == "网页角色"
    assert len(created.state.player.traits) == 2
    assert runtime.active_session is not None
    assert repository.load().state == runtime.active_session.state


def test_existing_save_requires_explicit_overwrite_then_replaces_atomically(tmp_path: Path) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    repository.save(_saved_state(), XorShift64StarRandom.from_seed(43))
    client, _ = _client(repository)
    draft = _create_draft(client)

    refused = client.post("/api/game/new", json=_confirmation_payload(draft))
    refused_error = ApiErrorResponse.model_validate_json(refused.text)
    assert refused.status_code == 409
    assert refused_error.error.code is ApiErrorCode.SAVE_OVERWRITE_REQUIRED
    assert repository.load().state == _saved_state()

    accepted = client.post(
        "/api/game/new",
        json=_confirmation_payload(draft, overwrite=True),
    )
    replacement = StateEnvelope.model_validate_json(accepted.text)
    assert accepted.status_code == 201
    assert replacement.state.player.name == "网页角色"
    assert repository.load().state.player.name == "网页角色"


def test_load_maps_missing_corrupt_and_unsupported_saves_to_stable_codes(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    client, _ = _client(JsonFileSaveRepository(path))

    missing = client.post("/api/game/load")
    assert (
        ApiErrorResponse.model_validate_json(missing.text).error.code is ApiErrorCode.SAVE_NOT_FOUND
    )

    path.write_text('{"format":', encoding="utf-8")
    corrupt = client.post("/api/game/load")
    assert (
        ApiErrorResponse.model_validate_json(corrupt.text).error.code is ApiErrorCode.SAVE_CORRUPT
    )

    path.write_text(
        '{"format":"buxianxian-save","schema_version":99}',
        encoding="utf-8",
    )
    unsupported = client.post("/api/game/load")
    assert (
        ApiErrorResponse.model_validate_json(unsupported.text).error.code
        is ApiErrorCode.SAVE_UNSUPPORTED
    )


def test_wait_advances_server_state_and_revision_conflict_returns_current_state(
    tmp_path: Path,
) -> None:
    client, _ = _client(JsonFileSaveRepository(tmp_path / "save.json"))
    draft = _create_draft(client)
    created_response = client.post("/api/game/new", json=_confirmation_payload(draft))
    assert created_response.status_code == 201

    waited_response = client.post(
        "/api/game/wait",
        json={"days": 4, "expected_revision": 0},
    )
    waited = StateEnvelope.model_validate_json(waited_response.text)
    assert waited.state.elapsed_days == 4
    assert waited.state.revision == 1

    conflict_response = client.post(
        "/api/game/wait",
        json={"days": 2, "expected_revision": 0},
    )
    conflict = ApiErrorResponse.model_validate_json(conflict_response.text)
    assert conflict_response.status_code == 409
    assert conflict.error.code is ApiErrorCode.REVISION_CONFLICT
    assert conflict.state == waited.state


def test_wait_rejection_no_session_and_persistence_failure_have_distinct_codes(
    tmp_path: Path,
) -> None:
    client, _ = _client(JsonFileSaveRepository(tmp_path / "save.json"))
    no_session = client.post("/api/game/wait", json={"days": 1, "expected_revision": 0})
    assert (
        ApiErrorResponse.model_validate_json(no_session.text).error.code
        is ApiErrorCode.NO_ACTIVE_SESSION
    )

    draft = _create_draft(client)
    client.post("/api/game/new", json=_confirmation_payload(draft))
    rejected = client.post("/api/game/wait", json={"days": 0, "expected_revision": 0})
    assert (
        ApiErrorResponse.model_validate_json(rejected.text).error.code
        is ApiErrorCode.TIME_COMMAND_REJECTED
    )

    failing_client, _ = _client(FailingSaveRepository())
    failing_draft = _create_draft(failing_client)
    failed = failing_client.post("/api/game/new", json=_confirmation_payload(failing_draft))
    failure = ApiErrorResponse.model_validate_json(failed.text)
    assert failed.status_code == 503
    assert failure.error.code is ApiErrorCode.PERSISTENCE_FAILED
    assert "private" not in failed.text.lower()
    assert "traceback" not in failed.text.lower()


def test_malformed_request_uses_stable_error_envelope(tmp_path: Path) -> None:
    client, _ = _client(JsonFileSaveRepository(tmp_path / "save.json"))

    response = client.post(
        "/api/game/wait",
        json={"days": "2", "expected_revision": 0},
    )
    error = ApiErrorResponse.model_validate_json(response.text)

    assert response.status_code == 422
    assert error.error.code is ApiErrorCode.INVALID_REQUEST
    assert "detail" not in response.text


def test_restart_load_restores_player_time_revision_and_rng(tmp_path: Path) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    first_client, first_runtime = _client(repository, seed=777)
    draft = _create_draft(first_client)
    first_client.post("/api/game/new", json=_confirmation_payload(draft))
    first_client.post("/api/game/wait", json={"days": 5, "expected_revision": 0})
    assert first_runtime.active_session is not None
    expected_random = first_runtime.active_session.fork_random_source().snapshot()

    restarted_client, restarted_runtime = _client(JsonFileSaveRepository(repository.path), seed=999)
    loaded_response = restarted_client.post("/api/game/load")
    loaded = StateEnvelope.model_validate_json(loaded_response.text)

    assert loaded_response.status_code == 200
    assert loaded.state.player.name == "网页角色"
    assert loaded.state.elapsed_days == 5
    assert loaded.state.revision == 1
    assert restarted_runtime.active_session is not None
    assert restarted_runtime.active_session.fork_random_source().snapshot() == expected_random


def test_seek_wheel_returns_complete_state_summary_and_persists_rng(tmp_path: Path) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    client, runtime = _client(repository, seed=701)
    draft = _create_draft(client)
    created = client.post("/api/game/new", json=_confirmation_payload(draft))
    assert created.status_code == 201
    assert runtime.active_session is not None
    before_random = runtime.active_session.fork_random_source().snapshot()

    response = client.post(
        "/api/game/cultivation/seek-wheel",
        json={"max_days": 7, "expected_revision": 0},
    )
    result = CultivationEnvelope.model_validate_json(response.text)

    assert response.status_code == 200
    assert result.state.elapsed_days == 7
    assert result.state.revision == 1
    assert result.state.cultivation.stage == "seeking_wheel"
    assert result.state.cultivation.wheel_status == "seeking"
    assert result.state.cultivation.wheel_insight > 0
    assert result.state.cultivation.suspected_sighting_threshold == 100
    assert result.cultivation_result.requested_max_days == 7
    assert result.cultivation_result.actual_days_elapsed == 7
    assert (
        result.cultivation_result.ordinary_insight_gained
        + result.cultivation_result.inspiration_insight_gained
        == result.state.cultivation.wheel_insight
    )
    assert runtime.active_session.fork_random_source().snapshot() != before_random
    loaded = repository.load()
    assert loaded.state.revision == result.state.revision
    assert loaded.state.elapsed_days == result.state.elapsed_days
    assert loaded.state.cultivation.wheel_insight == result.state.cultivation.wheel_insight
    assert loaded.random_source.snapshot() == runtime.active_session.fork_random_source().snapshot()


def test_seek_wheel_expected_failures_have_stable_codes_and_refresh_state(
    tmp_path: Path,
) -> None:
    client, _ = _client(JsonFileSaveRepository(tmp_path / "save.json"), seed=703)
    no_session = client.post(
        "/api/game/cultivation/seek-wheel",
        json={"max_days": 1, "expected_revision": 0},
    )
    assert (
        ApiErrorResponse.model_validate_json(no_session.text).error.code
        is ApiErrorCode.NO_ACTIVE_SESSION
    )

    draft = _create_draft(client)
    client.post("/api/game/new", json=_confirmation_payload(draft))
    invalid = client.post(
        "/api/game/cultivation/seek-wheel",
        json={"max_days": 0, "expected_revision": 0},
    )
    invalid_error = ApiErrorResponse.model_validate_json(invalid.text)
    assert invalid.status_code == 422
    assert invalid_error.error.code is ApiErrorCode.CULTIVATION_COMMAND_REJECTED
    assert invalid_error.state is not None
    assert invalid_error.state.revision == 0
    assert invalid_error.state.elapsed_days == 0
    assert invalid_error.state.cultivation.wheel_insight == 0

    succeeded = client.post(
        "/api/game/cultivation/seek-wheel",
        json={"max_days": 1, "expected_revision": 0},
    )
    authoritative = CultivationEnvelope.model_validate_json(succeeded.text).state
    conflict = client.post(
        "/api/game/cultivation/seek-wheel",
        json={"max_days": 1, "expected_revision": 0},
    )
    conflict_error = ApiErrorResponse.model_validate_json(conflict.text)
    assert conflict.status_code == 409
    assert conflict_error.error.code is ApiErrorCode.REVISION_CONFLICT
    assert conflict_error.state == authoritative


def test_seek_wheel_save_failure_reports_failure_and_preserves_state_rng_and_save(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    client, runtime = _client(repository, seed=709)
    draft = _create_draft(client)
    client.post("/api/game/new", json=_confirmation_payload(draft))
    assert runtime.active_session is not None
    before_state = runtime.active_session.state
    before_random = runtime.active_session.fork_random_source().snapshot()

    def fail_replace(source: Path, target: Path) -> None:
        del source, target
        raise OSError("simulated replacement failure")

    monkeypatch.setattr(save_repository_module, "_replace_file", fail_replace)
    failed = client.post(
        "/api/game/cultivation/seek-wheel",
        json={"max_days": 7, "expected_revision": 0},
    )
    error = ApiErrorResponse.model_validate_json(failed.text)

    assert failed.status_code == 503
    assert error.error.code is ApiErrorCode.PERSISTENCE_FAILED
    assert error.state is not None
    assert error.state.revision == before_state.revision
    assert error.state.elapsed_days == before_state.elapsed_days
    assert error.state.cultivation.wheel_insight == before_state.cultivation.wheel_insight
    assert runtime.active_session.state == before_state
    assert runtime.active_session.fork_random_source().snapshot() == before_random
    loaded = repository.load()
    assert loaded.state == before_state
    assert loaded.random_source.snapshot() == before_random


def test_restart_load_restores_cultivation_and_can_continue_rng_sequence(
    tmp_path: Path,
) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    first_client, first_runtime = _client(repository, seed=719)
    draft = _create_draft(first_client)
    first_client.post("/api/game/new", json=_confirmation_payload(draft))
    first_result = CultivationEnvelope.model_validate_json(
        first_client.post(
            "/api/game/cultivation/seek-wheel",
            json={"max_days": 7, "expected_revision": 0},
        ).text
    )
    assert first_runtime.active_session is not None
    persisted_random = first_runtime.active_session.fork_random_source().snapshot()

    restarted_client, restarted_runtime = _client(
        JsonFileSaveRepository(repository.path),
        seed=999,
    )
    loaded = StateEnvelope.model_validate_json(restarted_client.post("/api/game/load").text)
    assert loaded.state == first_result.state
    assert restarted_runtime.active_session is not None
    assert restarted_runtime.active_session.fork_random_source().snapshot() == persisted_random

    continued_response = restarted_client.post(
        "/api/game/cultivation/seek-wheel",
        json={"max_days": 1, "expected_revision": first_result.state.revision},
    )
    continued = CultivationEnvelope.model_validate_json(continued_response.text)
    assert continued_response.status_code == 200
    assert continued.state.revision == first_result.state.revision + 1
    assert continued.state.elapsed_days > first_result.state.elapsed_days
    assert continued.state.cultivation.wheel_insight > first_result.state.cultivation.wheel_insight
