"""Strict HTTP request, response, read-model, and error contracts."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

STRICT_MODEL = ConfigDict(extra="forbid", frozen=True, strict=True)


class ApiErrorCode(StrEnum):
    """Stable machine-readable failures exposed by the game API."""

    INVALID_REQUEST = "invalid_request"
    NO_ACTIVE_SESSION = "no_active_session"
    SAVE_NOT_FOUND = "save_not_found"
    SAVE_CORRUPT = "save_corrupt"
    SAVE_UNSUPPORTED = "save_unsupported"
    SAVE_LOAD_FAILED = "save_load_failed"
    DRAFT_NOT_FOUND = "draft_not_found"
    DRAFT_CREATION_FAILED = "draft_creation_failed"
    INVALID_NAME = "invalid_name"
    INVALID_APTITUDE_SELECTION = "invalid_aptitude_selection"
    INVALID_TRAIT_SELECTION = "invalid_trait_selection"
    SAVE_OVERWRITE_REQUIRED = "save_overwrite_required"
    REVISION_CONFLICT = "revision_conflict"
    TIME_COMMAND_REJECTED = "time_command_rejected"
    CULTIVATION_COMMAND_REJECTED = "cultivation_command_rejected"
    PERSISTENCE_FAILED = "persistence_failed"


class ApiFieldError(BaseModel):
    """Optional field-level context without leaking validation internals."""

    model_config = STRICT_MODEL

    field: str
    message: str


class ApiErrorDetail(BaseModel):
    """Stable error detail shared by expected non-success responses."""

    model_config = STRICT_MODEL

    code: ApiErrorCode
    message: str
    fields: tuple[ApiFieldError, ...] = ()


class AptitudesResponse(BaseModel):
    """Presentation projection of the five authoritative innate aptitudes."""

    model_config = STRICT_MODEL

    constitution: int
    comprehension: int
    spiritual_sense: int
    temperament: int
    fortune: int


class TraitResponse(BaseModel):
    """Prototype display metadata keyed by an authoritative stable ID."""

    model_config = STRICT_MODEL

    trait_id: str
    name: str
    description: str


class PlayerResponse(BaseModel):
    """Browser-facing complete player summary."""

    model_config = STRICT_MODEL

    name: str
    aptitudes: AptitudesResponse
    traits: tuple[TraitResponse, ...]


class CultivationStateResponse(BaseModel):
    """Browser-facing cultivation state plus server-owned progress threshold."""

    model_config = STRICT_MODEL

    stage: Literal["seeking_wheel"]
    wheel_insight: int
    wheel_status: Literal["seeking", "suspected_sighting"]
    suspected_sighting_threshold: int


class GameStateResponse(BaseModel):
    """Browser-facing authoritative state without persistence or RNG details."""

    model_config = STRICT_MODEL

    revision: int
    elapsed_days: int
    player: PlayerResponse
    cultivation: CultivationStateResponse


class GameStatusResponse(BaseModel):
    """Current single-save and active-session status."""

    model_config = STRICT_MODEL

    save_exists: bool
    save_available: bool
    session_active: bool
    state: GameStateResponse | None
    error: ApiErrorDetail | None


class AptitudeOptionResponse(BaseModel):
    """One server-generated selectable aptitude option."""

    model_config = STRICT_MODEL

    option_id: str
    aptitudes: AptitudesResponse


class CharacterDraftResponse(BaseModel):
    """Public candidate projection without private candidate RNG state."""

    model_config = STRICT_MODEL

    draft_id: str
    aptitude_options: tuple[AptitudeOptionResponse, ...]
    trait_options: tuple[TraitResponse, ...]
    required_trait_count: int


class ConfirmNewGameRequest(BaseModel):
    """Untrusted identifiers and player input submitted for server confirmation."""

    model_config = STRICT_MODEL

    draft_id: str = Field(min_length=1)
    name: str
    aptitude_option_id: str = Field(min_length=1)
    trait_ids: list[str]
    overwrite_existing_save: bool = False


class WaitRequest(BaseModel):
    """Typed intent to wait against an expected authoritative revision."""

    model_config = STRICT_MODEL

    days: int
    expected_revision: int


class SeekWheelRequest(BaseModel):
    """Typed cultivation intent against an expected authoritative revision."""

    model_config = STRICT_MODEL

    max_days: int
    expected_revision: int


class CultivationResultResponse(BaseModel):
    """Summary of one committed wheel-seeking action."""

    model_config = STRICT_MODEL

    requested_max_days: int
    actual_days_elapsed: int
    previous_insight: int
    current_insight: int
    ordinary_insight_gained: int
    inspiration_insight_gained: int
    reached_suspected_sighting: bool
    previous_elapsed_days: int
    current_elapsed_days: int


class StateEnvelope(BaseModel):
    """Successful state-changing or load response."""

    model_config = STRICT_MODEL

    state: GameStateResponse


class CultivationEnvelope(BaseModel):
    """Successful cultivation response with authoritative state and action summary."""

    model_config = STRICT_MODEL

    state: GameStateResponse
    cultivation_result: CultivationResultResponse


class ApiErrorResponse(BaseModel):
    """Exact non-success envelope with optional authoritative refresh state."""

    model_config = STRICT_MODEL

    error: ApiErrorDetail
    state: GameStateResponse | None = None
