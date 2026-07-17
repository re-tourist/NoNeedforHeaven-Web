"""Versioned player-state save, recovery, validation, and atomicity tests."""

import json
from pathlib import Path

import pytest

import buxianxian.infrastructure.save_repository as save_repository_module
from buxianxian.domain import (
    Accepted,
    AdvanceTime,
    CultivationStage,
    CultivationState,
    DomainEngine,
    GameState,
    InnateAptitudes,
    PlayerCharacter,
    WheelSeekingStatus,
)
from buxianxian.infrastructure import (
    CURRENT_SCHEMA_VERSION,
    SAVE_FORMAT,
    JsonFileSaveRepository,
    SaveError,
    SaveErrorCode,
    XorShift64StarRandom,
)

TEST_PLAYER = PlayerCharacter(
    name="测试角色",
    aptitudes=InnateAptitudes(5, 5, 5, 5, 5),
    trait_ids=("trait.alpha", "trait.beta"),
)


def _state(revision: int, elapsed_days: int, insight: int = 0) -> GameState:
    return GameState(
        revision=revision,
        elapsed_days=elapsed_days,
        player=TEST_PLAYER,
        cultivation=CultivationState(
            stage=CultivationStage.SEEKING_WHEEL,
            wheel_insight=insight,
            wheel_status=(
                WheelSeekingStatus.SUSPECTED_SIGHTING
                if insight == 100
                else WheelSeekingStatus.SEEKING
            ),
        ),
    )


def _player_payload() -> dict[str, object]:
    return {
        "name": "测试角色",
        "aptitudes": {
            "constitution": 5,
            "comprehension": 5,
            "spiritual_sense": 5,
            "temperament": 5,
            "fortune": 5,
        },
        "trait_ids": ["trait.alpha", "trait.beta"],
    }


def _cultivation_payload() -> dict[str, object]:
    return {
        "stage": "seeking_wheel",
        "wheel_insight": 0,
        "wheel_status": "seeking",
    }


def _valid_payload() -> dict[str, object]:
    return {
        "format": SAVE_FORMAT,
        "schema_version": CURRENT_SCHEMA_VERSION,
        "state": {
            "revision": 2,
            "elapsed_days": 7,
            "player": _player_payload(),
            "cultivation": _cultivation_payload(),
        },
        "random": {
            "algorithm": "xorshift64star",
            "version": 1,
            "state": "0123456789abcdef",
        },
    }


def _write_payload(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _assert_load_error(repository: JsonFileSaveRepository, code: SaveErrorCode) -> None:
    with pytest.raises(SaveError) as captured:
        repository.load()
    assert captured.value.code is code


def test_save_round_trip_preserves_complete_player_time_rng_and_markers(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    repository = JsonFileSaveRepository(path)
    state = _state(revision=4, elapsed_days=11, insight=42)
    random_source = XorShift64StarRandom.from_seed(0xCAFE_BABE)
    random_source.integer_inclusive(1, 10)
    expected_random_state = random_source.snapshot()

    repository.save(state, random_source)
    loaded = JsonFileSaveRepository(path).load()

    assert loaded.state == state
    assert loaded.random_source.snapshot() == expected_random_state
    decoded: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    assert decoded["format"] == "buxianxian-save"
    assert decoded["schema_version"] == 4
    assert decoded["state"] == {
        "elapsed_days": 11,
        "player": _player_payload(),
        "cultivation": {
            "stage": "seeking_wheel",
            "wheel_insight": 42,
            "wheel_status": "seeking",
        },
        "revision": 4,
    }


def test_save_and_resume_matches_continuous_time_and_random_sequence(tmp_path: Path) -> None:
    repository = JsonFileSaveRepository(tmp_path / "save.json")
    engine = DomainEngine()
    uninterrupted_state = _state(revision=0, elapsed_days=0)
    interrupted_state = _state(revision=0, elapsed_days=0)
    uninterrupted_random = XorShift64StarRandom.from_seed(0x1234_5678)
    interrupted_random = XorShift64StarRandom.from_seed(0x1234_5678)

    for days in (1, 3, 2):
        command = AdvanceTime(days=days)
        uninterrupted_result = engine.transition(
            uninterrupted_state,
            command,
            uninterrupted_random,
        )
        interrupted_result = engine.transition(interrupted_state, command, interrupted_random)
        assert isinstance(uninterrupted_result, Accepted)
        assert uninterrupted_result == interrupted_result
        uninterrupted_state = uninterrupted_result.state
        interrupted_state = interrupted_result.state
        assert uninterrupted_random.integer_inclusive(1, 100) == (
            interrupted_random.integer_inclusive(1, 100)
        )

    repository.save(interrupted_state, interrupted_random)
    loaded = repository.load()
    resumed_state = loaded.state
    resumed_random = loaded.random_source

    uninterrupted_values: list[int] = []
    resumed_values: list[int] = []
    for days in (5, 1, 10, 4):
        command = AdvanceTime(days=days)
        uninterrupted_result = engine.transition(
            uninterrupted_state,
            command,
            uninterrupted_random,
        )
        resumed_result = engine.transition(resumed_state, command, resumed_random)
        assert isinstance(uninterrupted_result, Accepted)
        assert isinstance(resumed_result, Accepted)
        assert uninterrupted_result == resumed_result
        uninterrupted_state = uninterrupted_result.state
        resumed_state = resumed_result.state
        uninterrupted_values.append(uninterrupted_random.integer_inclusive(1, 100))
        resumed_values.append(resumed_random.integer_inclusive(1, 100))

    assert resumed_values == uninterrupted_values
    assert resumed_state == uninterrupted_state
    assert resumed_random.snapshot() == uninterrupted_random.snapshot()


def test_missing_file_has_a_distinct_error(tmp_path: Path) -> None:
    _assert_load_error(
        JsonFileSaveRepository(tmp_path / "missing.json"),
        SaveErrorCode.FILE_NOT_FOUND,
    )


def test_corrupt_json_has_a_distinct_error(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    path.write_text('{"format":', encoding="utf-8")

    _assert_load_error(JsonFileSaveRepository(path), SaveErrorCode.INVALID_JSON)


def test_non_utf8_save_has_the_same_clear_corruption_error(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    path.write_bytes(b"\xff\xfe\x00")

    _assert_load_error(JsonFileSaveRepository(path), SaveErrorCode.INVALID_JSON)


def test_wrong_product_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    payload = _valid_payload()
    payload["format"] = "another-product"
    _write_payload(path, payload)

    _assert_load_error(JsonFileSaveRepository(path), SaveErrorCode.WRONG_PRODUCT)


@pytest.mark.parametrize(
    ("schema_version", "state"),
    [
        (1, {"revision": 2, "counter": 7}),
        (2, {"revision": 2, "elapsed_days": 7}),
        (
            3,
            {
                "revision": 2,
                "elapsed_days": 7,
                "player": _player_payload(),
            },
        ),
    ],
)
def test_pre_alpha_schema_without_player_is_explicitly_unsupported(
    tmp_path: Path,
    schema_version: int,
    state: dict[str, object],
) -> None:
    path = tmp_path / "save.json"
    payload = _valid_payload()
    payload["schema_version"] = schema_version
    payload["state"] = state
    _write_payload(path, payload)

    _assert_load_error(
        JsonFileSaveRepository(path),
        SaveErrorCode.UNSUPPORTED_SCHEMA_VERSION,
    )


def test_unknown_schema_version_is_rejected_before_guessing(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    payload = _valid_payload()
    payload["schema_version"] = 99
    _write_payload(path, payload)

    _assert_load_error(
        JsonFileSaveRepository(path),
        SaveErrorCode.UNSUPPORTED_SCHEMA_VERSION,
    )


@pytest.mark.parametrize(
    "invalid_state",
    [
        {
            "revision": -1,
            "elapsed_days": 7,
            "player": _player_payload(),
            "cultivation": _cultivation_payload(),
        },
        {
            "revision": 1,
            "elapsed_days": -1,
            "player": _player_payload(),
            "cultivation": _cultivation_payload(),
        },
        {
            "revision": 1,
            "elapsed_days": True,
            "player": _player_payload(),
            "cultivation": _cultivation_payload(),
        },
        {"revision": 1, "elapsed_days": 7},
    ],
)
def test_invalid_formal_domain_state_is_rejected(
    tmp_path: Path,
    invalid_state: dict[str, object],
) -> None:
    path = tmp_path / "save.json"
    payload = _valid_payload()
    payload["state"] = invalid_state
    _write_payload(path, payload)

    _assert_load_error(JsonFileSaveRepository(path), SaveErrorCode.INVALID_DATA)


@pytest.mark.parametrize(
    "invalid_player",
    [
        {**_player_payload(), "name": "   "},
        {
            **_player_payload(),
            "aptitudes": {
                "constitution": 4,
                "comprehension": 5,
                "spiritual_sense": 5,
                "temperament": 5,
                "fortune": 5,
            },
        },
        {**_player_payload(), "trait_ids": ["trait.alpha"]},
        {**_player_payload(), "trait_ids": ["trait.alpha", "trait.alpha"]},
        {**_player_payload(), "trait_ids": ["trait.beta", "trait.alpha"]},
        {**_player_payload(), "trait_ids": ["trait.alpha", 7]},
    ],
)
def test_invalid_player_profile_is_rejected(
    tmp_path: Path,
    invalid_player: dict[str, object],
) -> None:
    path = tmp_path / "save.json"
    payload = _valid_payload()
    payload["state"] = {
        "revision": 0,
        "elapsed_days": 0,
        "player": invalid_player,
        "cultivation": _cultivation_payload(),
    }
    _write_payload(path, payload)

    _assert_load_error(JsonFileSaveRepository(path), SaveErrorCode.INVALID_DATA)


@pytest.mark.parametrize(
    "invalid_cultivation",
    [
        {
            "stage": "unsupported",
            "wheel_insight": 0,
            "wheel_status": "seeking",
        },
        {
            "stage": "seeking_wheel",
            "wheel_insight": -1,
            "wheel_status": "seeking",
        },
        {
            "stage": "seeking_wheel",
            "wheel_insight": 99,
            "wheel_status": "suspected_sighting",
        },
        {
            "stage": "seeking_wheel",
            "wheel_insight": 100,
            "wheel_status": "seeking",
        },
    ],
)
def test_invalid_cultivation_state_is_rejected(
    tmp_path: Path,
    invalid_cultivation: dict[str, object],
) -> None:
    path = tmp_path / "save.json"
    payload = _valid_payload()
    payload["state"] = {
        "revision": 0,
        "elapsed_days": 0,
        "player": _player_payload(),
        "cultivation": invalid_cultivation,
    }
    _write_payload(path, payload)

    _assert_load_error(JsonFileSaveRepository(path), SaveErrorCode.INVALID_DATA)


def test_unsupported_random_algorithm_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    payload = _valid_payload()
    payload["random"] = {
        "algorithm": "unknown",
        "version": 1,
        "state": "0123456789abcdef",
    }
    _write_payload(path, payload)

    _assert_load_error(
        JsonFileSaveRepository(path),
        SaveErrorCode.UNSUPPORTED_RANDOM_ALGORITHM,
    )


def test_unsupported_random_state_version_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    payload = _valid_payload()
    payload["random"] = {
        "algorithm": "xorshift64star",
        "version": 2,
        "state": "0123456789abcdef",
    }
    _write_payload(path, payload)

    _assert_load_error(
        JsonFileSaveRepository(path),
        SaveErrorCode.UNSUPPORTED_RANDOM_VERSION,
    )


@pytest.mark.parametrize("invalid_state", ["not-hex", "0000000000000000"])
def test_invalid_random_state_is_rejected(tmp_path: Path, invalid_state: str) -> None:
    path = tmp_path / "save.json"
    payload = _valid_payload()
    payload["random"] = {
        "algorithm": "xorshift64star",
        "version": 1,
        "state": invalid_state,
    }
    _write_payload(path, payload)

    _assert_load_error(JsonFileSaveRepository(path), SaveErrorCode.INVALID_RANDOM_STATE)


def test_replace_failure_preserves_old_complete_save_and_cleans_temporary_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "save.json"
    repository = JsonFileSaveRepository(path)
    old_state = _state(revision=1, elapsed_days=9)
    old_random = XorShift64StarRandom.from_seed(7)
    old_random_snapshot = old_random.snapshot()
    repository.save(old_state, old_random)

    def fail_replace(source: Path, target: Path) -> None:
        del source, target
        raise OSError("simulated replacement failure")

    monkeypatch.setattr(save_repository_module, "_replace_file", fail_replace)

    with pytest.raises(SaveError) as captured:
        repository.save(
            _state(revision=2, elapsed_days=12),
            XorShift64StarRandom.from_seed(99),
        )

    assert captured.value.code is SaveErrorCode.IO_ERROR
    loaded = repository.load()
    assert loaded.state == old_state
    assert loaded.random_source.snapshot() == old_random_snapshot
    assert list(tmp_path.glob("*.tmp")) == []
