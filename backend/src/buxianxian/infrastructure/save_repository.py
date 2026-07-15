"""Versioned JSON save codec and atomic local-file adapter."""

import json
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from json import JSONDecodeError
from pathlib import Path

from buxianxian.application.ports import PersistenceError
from buxianxian.domain import GameState
from buxianxian.infrastructure.random_source import (
    RandomStateSnapshot,
    XorShift64StarRandom,
)

SAVE_FORMAT = "buxianxian-save"
CURRENT_SCHEMA_VERSION = 1

type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]


class SaveErrorCode(StrEnum):
    """Stable categories for expected persistence failures."""

    FILE_NOT_FOUND = "file_not_found"
    INVALID_JSON = "invalid_json"
    WRONG_PRODUCT = "wrong_product"
    UNSUPPORTED_SCHEMA_VERSION = "unsupported_schema_version"
    INVALID_DATA = "invalid_data"
    UNSUPPORTED_RANDOM_ALGORITHM = "unsupported_random_algorithm"
    UNSUPPORTED_RANDOM_VERSION = "unsupported_random_version"
    INVALID_RANDOM_STATE = "invalid_random_state"
    IO_ERROR = "io_error"


class SaveError(PersistenceError):
    """Structured persistence error that hides incidental lower-level exceptions."""

    code: SaveErrorCode
    detail: str

    def __init__(self, code: SaveErrorCode, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code.value}: {detail}")


@dataclass(frozen=True, slots=True)
class LoadedSave:
    """Authoritative state and resumed random source loaded from one snapshot."""

    state: GameState
    random_source: XorShift64StarRandom


@dataclass(frozen=True, slots=True)
class JsonFileSaveRepository:
    """Read and atomically replace one versioned local JSON save file."""

    path: Path

    def save(self, state: GameState, random_source: XorShift64StarRandom) -> None:
        """Serialize completely, then atomically replace the configured save."""

        payload = _encode_v1(state, random_source.snapshot())
        serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        _atomic_write_text(self.path, serialized)

    def load(self) -> LoadedSave:
        """Load and strictly validate a supported save version."""

        try:
            serialized = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise SaveError(SaveErrorCode.FILE_NOT_FOUND, "save file does not exist") from None
        except UnicodeDecodeError:
            raise SaveError(SaveErrorCode.INVALID_JSON, "save is not valid UTF-8 JSON") from None
        except OSError:
            raise SaveError(SaveErrorCode.IO_ERROR, "save file could not be read") from None

        payload = _decode_json_object(serialized)
        save_format = _required_string(payload, "format", SaveErrorCode.INVALID_DATA)
        if save_format != SAVE_FORMAT:
            raise SaveError(SaveErrorCode.WRONG_PRODUCT, "save belongs to another product")

        schema_version = _required_integer(
            payload,
            "schema_version",
            SaveErrorCode.INVALID_DATA,
        )
        loader = _VERSION_LOADERS.get(schema_version)
        if loader is None:
            raise SaveError(
                SaveErrorCode.UNSUPPORTED_SCHEMA_VERSION,
                f"schema version {schema_version} is not supported",
            )

        return loader(payload)


def _encode_v1(
    state: GameState,
    random_state: RandomStateSnapshot,
) -> dict[str, JsonValue]:
    return {
        "format": SAVE_FORMAT,
        "schema_version": CURRENT_SCHEMA_VERSION,
        "state": {
            "revision": state.revision,
            "counter": state.counter,
        },
        "random": {
            "algorithm": random_state.algorithm,
            "version": random_state.version,
            "state": random_state.state,
        },
    }


def _load_v1(payload: dict[str, JsonValue]) -> LoadedSave:
    _require_exact_fields(
        payload,
        frozenset({"format", "schema_version", "state", "random"}),
        SaveErrorCode.INVALID_DATA,
        "save envelope",
    )

    state_payload = _required_object(payload, "state", SaveErrorCode.INVALID_DATA)
    _require_exact_fields(
        state_payload,
        frozenset({"revision", "counter"}),
        SaveErrorCode.INVALID_DATA,
        "domain state",
    )
    revision = _required_integer(state_payload, "revision", SaveErrorCode.INVALID_DATA)
    counter = _required_integer(state_payload, "counter", SaveErrorCode.INVALID_DATA)
    try:
        state = GameState(revision=revision, counter=counter)
    except ValueError:
        raise SaveError(SaveErrorCode.INVALID_DATA, "domain state is invalid") from None

    random_payload = _required_object(payload, "random", SaveErrorCode.INVALID_RANDOM_STATE)
    _require_exact_fields(
        random_payload,
        frozenset({"algorithm", "version", "state"}),
        SaveErrorCode.INVALID_RANDOM_STATE,
        "random state",
    )
    algorithm = _required_string(
        random_payload,
        "algorithm",
        SaveErrorCode.INVALID_RANDOM_STATE,
    )
    if algorithm != XorShift64StarRandom.ALGORITHM:
        raise SaveError(
            SaveErrorCode.UNSUPPORTED_RANDOM_ALGORITHM,
            f"random algorithm {algorithm!r} is not supported",
        )

    random_version = _required_integer(
        random_payload,
        "version",
        SaveErrorCode.INVALID_RANDOM_STATE,
    )
    if random_version != XorShift64StarRandom.STATE_VERSION:
        raise SaveError(
            SaveErrorCode.UNSUPPORTED_RANDOM_VERSION,
            f"random state version {random_version} is not supported",
        )

    serialized_random_state = _required_string(
        random_payload,
        "state",
        SaveErrorCode.INVALID_RANDOM_STATE,
    )
    snapshot = RandomStateSnapshot(
        algorithm=algorithm,
        version=random_version,
        state=serialized_random_state,
    )
    try:
        random_source = XorShift64StarRandom.from_snapshot(snapshot)
    except ValueError:
        raise SaveError(
            SaveErrorCode.INVALID_RANDOM_STATE,
            "random state is invalid",
        ) from None

    return LoadedSave(state=state, random_source=random_source)


type _VersionLoader = Callable[[dict[str, JsonValue]], LoadedSave]

_VERSION_LOADERS: dict[int, _VersionLoader] = {
    CURRENT_SCHEMA_VERSION: _load_v1,
}


def _decode_json_object(serialized: str) -> dict[str, JsonValue]:
    try:
        decoded: JsonValue = json.loads(serialized)
    except JSONDecodeError:
        raise SaveError(SaveErrorCode.INVALID_JSON, "save is not valid JSON") from None

    return _require_object_value(decoded, SaveErrorCode.INVALID_DATA, "save root")


def _required_object(
    payload: dict[str, JsonValue],
    field: str,
    error_code: SaveErrorCode,
) -> dict[str, JsonValue]:
    value = _required_value(payload, field, error_code)
    return _require_object_value(value, error_code, field)


def _require_object_value(
    value: JsonValue,
    error_code: SaveErrorCode,
    context: str,
) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise SaveError(error_code, f"{context} must be an object")
    return value


def _required_string(
    payload: dict[str, JsonValue],
    field: str,
    error_code: SaveErrorCode,
) -> str:
    value = _required_value(payload, field, error_code)
    if not isinstance(value, str):
        raise SaveError(error_code, f"{field} must be a string")
    return value


def _required_integer(
    payload: dict[str, JsonValue],
    field: str,
    error_code: SaveErrorCode,
) -> int:
    value = _required_value(payload, field, error_code)
    if type(value) is not int:
        raise SaveError(error_code, f"{field} must be an integer")
    return value


def _required_value(
    payload: dict[str, JsonValue],
    field: str,
    error_code: SaveErrorCode,
) -> JsonValue:
    try:
        return payload[field]
    except KeyError:
        raise SaveError(error_code, f"required field {field!r} is missing") from None


def _require_exact_fields(
    payload: dict[str, JsonValue],
    expected: frozenset[str],
    error_code: SaveErrorCode,
    context: str,
) -> None:
    if payload.keys() != expected:
        raise SaveError(error_code, f"{context} fields do not match schema")


def _atomic_write_text(path: Path, serialized: str) -> None:
    temporary_path: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(serialized)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        _replace_file(temporary_path, path)
        temporary_path = None
    except OSError:
        raise SaveError(SaveErrorCode.IO_ERROR, "save could not be written atomically") from None
    finally:
        if temporary_path is not None:
            _remove_temporary_file(temporary_path)


def _replace_file(source: Path, target: Path) -> None:
    os.replace(source, target)


def _remove_temporary_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        return
