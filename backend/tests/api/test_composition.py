"""Local save configuration and production source contract tests."""

from pathlib import Path

import pytest

import buxianxian.infrastructure.runtime_sources as runtime_sources_module
from buxianxian.api.composition import (
    DEFAULT_SAVE_PATH,
    SAVE_PATH_ENVIRONMENT_VARIABLE,
    configured_save_path,
)
from buxianxian.infrastructure import (
    SecureDraftIdentifierSource,
    SecureXorShift64StarFactory,
)


def test_default_save_path_is_in_ignored_runtime_data() -> None:
    assert DEFAULT_SAVE_PATH.parent.name == "runtime-data"
    assert DEFAULT_SAVE_PATH.name == "buxianxian.save.json"
    assert DEFAULT_SAVE_PATH.is_absolute()


def test_save_path_environment_override_is_expanded_and_resolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configured = tmp_path / "custom" / "single.json"
    monkeypatch.setenv(SAVE_PATH_ENVIRONMENT_VARIABLE, str(configured))

    assert configured_save_path() == configured.resolve()


def test_secure_sources_produce_nonzero_rng_and_opaque_identifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def return_zero(bit_count: int) -> int:
        assert bit_count == 64
        return 0

    monkeypatch.setattr(runtime_sources_module.secrets, "randbits", return_zero)
    random_source = SecureXorShift64StarFactory().create()

    assert random_source.snapshot().state == "0000000000000001"
    assert SecureDraftIdentifierSource().create()
