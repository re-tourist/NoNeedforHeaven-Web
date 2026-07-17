"""FastAPI application construction, health, and game-route composition."""

from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from buxianxian import __version__
from buxianxian.api.composition import ConcreteGameRuntime, create_default_runtime
from buxianxian.api.contracts import ApiErrorCode, ApiErrorDetail, ApiErrorResponse
from buxianxian.api.routes import create_game_router

APP_ID = "buxianxian"
APP_NAME = "不羡仙"


class HealthResponse(BaseModel):
    """Validated response returned by the engineering health endpoint."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["ok"]
    app_id: Literal["buxianxian"]
    app_name: Literal["不羡仙"]
    version: str


def create_app(runtime: ConcreteGameRuntime | None = None) -> FastAPI:
    """Create a configured HTTP application without starting a process."""

    application = FastAPI(title=APP_NAME, version=__version__)
    application.add_exception_handler(RequestValidationError, request_validation_error_handler)
    application.add_api_route(
        "/api/health",
        get_health,
        methods=["GET"],
        response_model=HealthResponse,
    )
    application.include_router(create_game_router(runtime or create_default_runtime()))
    return application


def get_health() -> HealthResponse:
    """Return the runtime identity used by connectivity checks."""

    return HealthResponse(
        status="ok",
        app_id=APP_ID,
        app_name=APP_NAME,
        version=__version__,
    )


async def request_validation_error_handler(
    request: Request,
    error: Exception,
) -> JSONResponse:
    """Normalize malformed transport input to the stable game API envelope."""

    del request, error
    response = ApiErrorResponse(
        error=ApiErrorDetail(
            code=ApiErrorCode.INVALID_REQUEST,
            message="请求格式无效。请检查字段类型和必需字段。",
        )
    )
    return JSONResponse(status_code=422, content=response.model_dump(mode="json"))


app = create_app()
