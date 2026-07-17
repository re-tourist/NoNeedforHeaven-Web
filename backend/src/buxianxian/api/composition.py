"""Concrete local runtime composition and environment-based save configuration."""

import os
from pathlib import Path

from buxianxian.application import SingleGameRuntime
from buxianxian.infrastructure import (
    PROTOTYPE_TRAIT_CATALOG,
    JsonFileSaveRepository,
    SecureDraftIdentifierSource,
    SecureXorShift64StarFactory,
    XorShift64StarRandom,
)

SAVE_PATH_ENVIRONMENT_VARIABLE = "BUXIANXIAN_SAVE_PATH"
DEFAULT_SAVE_PATH = Path(__file__).resolve().parents[4] / "runtime-data" / "buxianxian.save.json"

type ConcreteGameRuntime = SingleGameRuntime[XorShift64StarRandom]


def configured_save_path() -> Path:
    """Resolve the optional environment override or local ignored default."""

    configured = os.environ.get(SAVE_PATH_ENVIRONMENT_VARIABLE)
    if configured is None or not configured.strip():
        return DEFAULT_SAVE_PATH
    return Path(configured).expanduser().resolve()


def create_default_runtime(save_path: Path | None = None) -> ConcreteGameRuntime:
    """Compose one local runtime without reading or writing the save eagerly."""

    repository = JsonFileSaveRepository(save_path or configured_save_path())
    return SingleGameRuntime[XorShift64StarRandom](
        repository=repository,
        trait_catalog=PROTOTYPE_TRAIT_CATALOG,
        random_source_factory=SecureXorShift64StarFactory(),
        draft_identifier_source=SecureDraftIdentifierSource(),
    )
