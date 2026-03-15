"""FastAPI application factory for the HTTP adapter."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.adapters.interface.http_api.data_version import DataVersionStore
from src.adapters.interface.http_api.dependencies import get_data_version_store
from src.adapters.interface.http_api.router import router
from src.infrastructure.logging.logger import get_app_logger


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
    )


def create_app(
    *,
    cors_origins: list[str] | None = None,
) -> FastAPI:
    """Create and configure FastAPI app."""
    app = FastAPI(title="GnuCash Dashboard API", version="0.1.0")
    app.state.logger = get_app_logger()
    app.state.data_version_store = DataVersionStore(initial=1)

    allowed_origins = cors_origins or [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_data_version_header(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers["X-Data-Version"] = str(
            app.state.data_version_store.get()
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(  # type: ignore[no-untyped-def]
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details = {
            ".".join(str(part) for part in err["loc"]): err["msg"]
            for err in exc.errors()
        }
        return _error_response(
            status_code=400,
            code="invalid_request",
            message="Request validation failed.",
            details=details,
        )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(  # type: ignore[no-untyped-def]
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        if isinstance(exc.detail, str):
            details: dict[str, Any] = {}
            message = exc.detail
        elif isinstance(exc.detail, dict):
            details = exc.detail
            message = "Request failed."
        else:
            details = {}
            message = "Request failed."
        return _error_response(
            status_code=exc.status_code,
            code="invalid_request" if exc.status_code < 500 else "server_error",
            message=message,
            details=details,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(  # type: ignore[no-untyped-def]
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        app.state.logger.exception("Unhandled API exception: %s", exc)
        return _error_response(
            status_code=500,
            code="server_error",
            message="Unexpected server error.",
        )

    app.dependency_overrides[get_data_version_store] = (
        lambda: app.state.data_version_store
    )
    app.include_router(router)
    return app

