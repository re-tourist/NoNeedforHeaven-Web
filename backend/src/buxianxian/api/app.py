"""FastAPI application construction and engineering health contract."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

from buxianxian import __version__

APP_ID = "buxianxian"
APP_NAME = "不羡仙"


class HealthResponse(BaseModel):
    """Validated response returned by the engineering health endpoint."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["ok"]
    app_id: Literal["buxianxian"]
    app_name: Literal["不羡仙"]
    version: str


def create_app() -> FastAPI:
    """Create a configured HTTP application without starting a process."""

    application = FastAPI(title=APP_NAME, version=__version__)
    application.add_api_route(
        "/api/health",
        get_health,
        methods=["GET"],
        response_model=HealthResponse,
    )
    return application


def get_health() -> HealthResponse:
    """Return the runtime identity used by connectivity checks."""

    return HealthResponse(
        status="ok",
        app_id=APP_ID,
        app_name=APP_NAME,
        version=__version__,
    )


app = create_app()
