"""FastAPI adapter for the single-game application runtime."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from buxianxian.api.composition import ConcreteGameRuntime
from buxianxian.api.contracts import (
    ApiErrorCode,
    ApiErrorDetail,
    ApiErrorResponse,
    AptitudeOptionResponse,
    AptitudesResponse,
    CharacterDraftResponse,
    ConfirmNewGameRequest,
    GameStateResponse,
    GameStatusResponse,
    PlayerResponse,
    StateEnvelope,
    TraitResponse,
    WaitRequest,
)
from buxianxian.application import (
    CommandRejected,
    DraftCreated,
    DraftCreationFailed,
    DraftNotFound,
    GameLoadFailed,
    InitialSaveFailed,
    NewGameRejected,
    NoActiveSession,
    PersistenceError,
    PersistenceFailed,
    RevisionConflict,
    SaveInspectionFailed,
    SaveOverwriteRequired,
)
from buxianxian.domain import (
    CharacterCreationErrorCode,
    GameState,
    InnateAptitudes,
    RejectionReason,
    TraitDefinition,
)
from buxianxian.infrastructure import SaveError, SaveErrorCode


def create_game_router(runtime: ConcreteGameRuntime) -> APIRouter:
    """Create routes closed over one explicitly composed runtime."""

    router = APIRouter(prefix="/api/game", tags=["game"])

    def get_game_status() -> GameStatusResponse:
        current = runtime.inspect_status()
        return GameStatusResponse(
            save_exists=current.save_exists,
            save_available=current.save_available,
            session_active=current.session_active,
            state=(
                _state_response(current.state, runtime.trait_catalog)
                if current.state is not None
                else None
            ),
            error=(
                _load_error_detail(current.load_error) if current.load_error is not None else None
            ),
        )

    def create_character_draft() -> CharacterDraftResponse | JSONResponse:
        result = runtime.create_draft()
        if isinstance(result, DraftCreationFailed):
            return _error_response(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                ApiErrorCode.DRAFT_CREATION_FAILED,
                "暂时无法生成角色创建候选。请重试。",
            )
        return _draft_response(result)

    def confirm_new_game(request: ConfirmNewGameRequest) -> StateEnvelope | JSONResponse:
        result = runtime.confirm_new_game(
            draft_id=request.draft_id,
            name=request.name,
            aptitude_option_id=request.aptitude_option_id,
            selected_trait_ids=request.trait_ids,
            overwrite_existing_save=request.overwrite_existing_save,
        )
        if isinstance(result, DraftNotFound):
            return _error_response(
                status.HTTP_404_NOT_FOUND,
                ApiErrorCode.DRAFT_NOT_FOUND,
                "角色创建草稿不存在或已经失效。请重新生成。",
            )
        if isinstance(result, SaveOverwriteRequired):
            return _error_response(
                status.HTTP_409_CONFLICT,
                ApiErrorCode.SAVE_OVERWRITE_REQUIRED,
                "已有本地存档。开始新游戏前必须明确确认覆盖。",
            )
        if isinstance(result, SaveInspectionFailed | InitialSaveFailed):
            return _error_response(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                ApiErrorCode.PERSISTENCE_FAILED,
                "新游戏无法安全保存。请稍后重试。",
            )
        if isinstance(result, NewGameRejected):
            code, message = _character_error(result.error)
            return _error_response(status.HTTP_422_UNPROCESSABLE_CONTENT, code, message)
        return StateEnvelope(state=_state_response(result.session.state, runtime.trait_catalog))

    def load_game() -> StateEnvelope | JSONResponse:
        result = runtime.load_game()
        if isinstance(result, GameLoadFailed):
            detail = _load_error_detail(result.error)
            return _error_response(_load_error_status(detail.code), detail.code, detail.message)
        return StateEnvelope(state=_state_response(result.state, runtime.trait_catalog))

    def wait(request: WaitRequest) -> StateEnvelope | JSONResponse:
        result = runtime.wait(request.days, request.expected_revision)
        if isinstance(result, NoActiveSession):
            return _error_response(
                status.HTTP_409_CONFLICT,
                ApiErrorCode.NO_ACTIVE_SESSION,
                "当前没有活动游戏。请先开始或继续游戏。",
            )
        if isinstance(result, RevisionConflict):
            return _error_response(
                status.HTTP_409_CONFLICT,
                ApiErrorCode.REVISION_CONFLICT,
                "游戏状态已经更新。界面已刷新。请重新确认操作。",
                state=_active_state(runtime),
            )
        if isinstance(result, CommandRejected):
            return _error_response(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                ApiErrorCode.TIME_COMMAND_REJECTED,
                _time_rejection_message(result.reason),
                state=_state_response(result.state, runtime.trait_catalog),
            )
        if isinstance(result, PersistenceFailed):
            return _error_response(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                ApiErrorCode.PERSISTENCE_FAILED,
                "游戏状态无法安全保存。本次等待没有生效。",
                state=_state_response(result.state, runtime.trait_catalog),
            )
        return StateEnvelope(state=_state_response(result.state, runtime.trait_catalog))

    router.add_api_route(
        "",
        get_game_status,
        methods=["GET"],
        response_model=GameStatusResponse,
    )
    router.add_api_route(
        "/drafts",
        create_character_draft,
        methods=["POST"],
        response_model=CharacterDraftResponse,
        responses={503: {"model": ApiErrorResponse}},
        status_code=status.HTTP_201_CREATED,
    )
    router.add_api_route(
        "/new",
        confirm_new_game,
        methods=["POST"],
        response_model=StateEnvelope,
        responses={
            404: {"model": ApiErrorResponse},
            409: {"model": ApiErrorResponse},
            422: {"model": ApiErrorResponse},
            503: {"model": ApiErrorResponse},
        },
        status_code=status.HTTP_201_CREATED,
    )
    router.add_api_route(
        "/load",
        load_game,
        methods=["POST"],
        response_model=StateEnvelope,
        responses={
            404: {"model": ApiErrorResponse},
            422: {"model": ApiErrorResponse},
            503: {"model": ApiErrorResponse},
        },
    )
    router.add_api_route(
        "/wait",
        wait,
        methods=["POST"],
        response_model=StateEnvelope,
        responses={
            409: {"model": ApiErrorResponse},
            422: {"model": ApiErrorResponse},
            503: {"model": ApiErrorResponse},
        },
    )

    return router


def _draft_response(result: DraftCreated) -> CharacterDraftResponse:
    return CharacterDraftResponse(
        draft_id=result.draft_id,
        aptitude_options=tuple(
            AptitudeOptionResponse(
                option_id=option.option_id,
                aptitudes=_aptitudes_response(option.aptitudes),
            )
            for option in result.candidates.aptitude_options
        ),
        trait_options=tuple(_trait_response(trait) for trait in result.candidates.trait_options),
        required_trait_count=2,
    )


def _state_response(
    state: GameState,
    trait_catalog: tuple[TraitDefinition, ...],
) -> GameStateResponse:
    trait_by_id = {trait.trait_id: trait for trait in trait_catalog}
    traits = tuple(
        _trait_response(trait_by_id[trait_id])
        if trait_id in trait_by_id
        else TraitResponse(
            trait_id=trait_id,
            name="未知原型词条",
            description="当前原型目录中没有此词条的显示信息。",
        )
        for trait_id in state.player.trait_ids
    )
    return GameStateResponse(
        revision=state.revision,
        elapsed_days=state.elapsed_days,
        player=PlayerResponse(
            name=state.player.name,
            aptitudes=_aptitudes_response(state.player.aptitudes),
            traits=traits,
        ),
    )


def _aptitudes_response(aptitudes: InnateAptitudes) -> AptitudesResponse:
    return AptitudesResponse(
        constitution=aptitudes.constitution,
        comprehension=aptitudes.comprehension,
        spiritual_sense=aptitudes.spiritual_sense,
        temperament=aptitudes.temperament,
        fortune=aptitudes.fortune,
    )


def _trait_response(trait: TraitDefinition) -> TraitResponse:
    return TraitResponse(
        trait_id=trait.trait_id,
        name=trait.name,
        description=trait.description,
    )


def _character_error(error: CharacterCreationErrorCode) -> tuple[ApiErrorCode, str]:
    if error is CharacterCreationErrorCode.INVALID_NAME:
        return ApiErrorCode.INVALID_NAME, "角色姓名不符合要求。请检查空白、长度和控制字符。"
    if error is CharacterCreationErrorCode.INVALID_APTITUDE_SELECTION:
        return ApiErrorCode.INVALID_APTITUDE_SELECTION, "所选先天禀赋不属于当前草稿。"
    if error in {
        CharacterCreationErrorCode.INVALID_TRAIT_SELECTION_COUNT,
        CharacterCreationErrorCode.DUPLICATE_TRAIT,
        CharacterCreationErrorCode.TRAIT_NOT_OFFERED,
    }:
        return ApiErrorCode.INVALID_TRAIT_SELECTION, "必须选择当前草稿中的两个不同词条。"
    return ApiErrorCode.DRAFT_CREATION_FAILED, "角色创建草稿合同无效。请重新生成。"


def _load_error_detail(error: PersistenceError) -> ApiErrorDetail:
    if isinstance(error, SaveError):
        if error.code is SaveErrorCode.FILE_NOT_FOUND:
            return ApiErrorDetail(
                code=ApiErrorCode.SAVE_NOT_FOUND, message="没有可继续的本地存档。"
            )
        if error.code in {
            SaveErrorCode.UNSUPPORTED_SCHEMA_VERSION,
            SaveErrorCode.UNSUPPORTED_RANDOM_ALGORITHM,
            SaveErrorCode.UNSUPPORTED_RANDOM_VERSION,
        }:
            return ApiErrorDetail(
                code=ApiErrorCode.SAVE_UNSUPPORTED,
                message="本地存档版本或随机状态版本不受当前程序支持。",
            )
        if error.code in {
            SaveErrorCode.INVALID_JSON,
            SaveErrorCode.WRONG_PRODUCT,
            SaveErrorCode.INVALID_DATA,
            SaveErrorCode.INVALID_RANDOM_STATE,
        }:
            return ApiErrorDetail(
                code=ApiErrorCode.SAVE_CORRUPT,
                message="本地存档已损坏或不属于不羡仙。",
            )
    return ApiErrorDetail(
        code=ApiErrorCode.SAVE_LOAD_FAILED,
        message="无法安全读取本地存档。",
    )


def _load_error_status(code: ApiErrorCode) -> int:
    if code is ApiErrorCode.SAVE_NOT_FOUND:
        return status.HTTP_404_NOT_FOUND
    if code in {ApiErrorCode.SAVE_CORRUPT, ApiErrorCode.SAVE_UNSUPPORTED}:
        return status.HTTP_422_UNPROCESSABLE_CONTENT
    return status.HTTP_503_SERVICE_UNAVAILABLE


def _time_rejection_message(reason: RejectionReason) -> str:
    if reason is RejectionReason.INVALID_DAY_COUNT:
        return "等待天数必须是正整数。"
    return "等待天数超出当前支持的范围。"


def _active_state(runtime: ConcreteGameRuntime) -> GameStateResponse | None:
    session = runtime.active_session
    if session is None:
        return None
    return _state_response(session.state, runtime.trait_catalog)


def _error_response(
    status_code: int,
    code: ApiErrorCode,
    message: str,
    *,
    state: GameStateResponse | None = None,
) -> JSONResponse:
    response = ApiErrorResponse(
        error=ApiErrorDetail(code=code, message=message),
        state=state,
    )
    return JSONResponse(status_code=status_code, content=response.model_dump(mode="json"))
