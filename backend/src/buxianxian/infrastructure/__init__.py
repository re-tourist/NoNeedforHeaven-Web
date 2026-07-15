"""Infrastructure adapters for local persistence and deterministic randomness."""

from buxianxian.infrastructure.random_source import (
    RandomStateSnapshot,
    XorShift64StarRandom,
)
from buxianxian.infrastructure.save_repository import (
    CURRENT_SCHEMA_VERSION,
    SAVE_FORMAT,
    JsonFileSaveRepository,
    LoadedSave,
    SaveError,
    SaveErrorCode,
)

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "SAVE_FORMAT",
    "JsonFileSaveRepository",
    "LoadedSave",
    "RandomStateSnapshot",
    "SaveError",
    "SaveErrorCode",
    "XorShift64StarRandom",
]
