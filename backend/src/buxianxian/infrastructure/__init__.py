"""Infrastructure adapters for local persistence and deterministic randomness."""

from buxianxian.infrastructure.prototype_traits import PROTOTYPE_TRAIT_CATALOG
from buxianxian.infrastructure.random_source import (
    RandomStateSnapshot,
    XorShift64StarRandom,
)
from buxianxian.infrastructure.runtime_sources import (
    SecureDraftIdentifierSource,
    SecureXorShift64StarFactory,
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
    "PROTOTYPE_TRAIT_CATALOG",
    "SAVE_FORMAT",
    "JsonFileSaveRepository",
    "LoadedSave",
    "RandomStateSnapshot",
    "SaveError",
    "SaveErrorCode",
    "SecureDraftIdentifierSource",
    "SecureXorShift64StarFactory",
    "XorShift64StarRandom",
]
