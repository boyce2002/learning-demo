from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .clock import ClockError, NowProvider, utc_now
from .config import Settings, load_settings
from .database import init_db
from .routes import create_router
from .security import InMemoryRateLimiter
from .services import BusinessError, SparkLabService
from .visitor import VisitorSessionManager


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"detail": {"code": code, "message": message}},
    )


def create_app(
    settings: Optional[Settings] = None,
    now_provider: NowProvider = utc_now,
) -> FastAPI:
    resolved_settings = settings or load_settings()
    service = SparkLabService(resolved_settings, now_provider)
    sessions = VisitorSessionManager(resolved_settings)
    rate_limiter = InMemoryRateLimiter()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        init_db(resolved_settings.database_path)
        yield

    application = FastAPI(
        title="SparkLab API",
        version="0.2.0",
        lifespan=lifespan,
        docs_url=None if resolved_settings.public_demo_enabled else "/docs",
        redoc_url=None if resolved_settings.public_demo_enabled else "/redoc",
        openapi_url=None if resolved_settings.public_demo_enabled else "/openapi.json",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def no_store_api(request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH"}:
            content_length = request.headers.get("content-length", "")
            try:
                declared_size = int(content_length) if content_length else 0
            except ValueError:
                declared_size = resolved_settings.max_request_body_bytes + 1
            if declared_size > resolved_settings.max_request_body_bytes:
                return _error_response(413, "REQUEST_TOO_LARGE", "提交内容超出允许大小。")
            body = await request.body()
            if len(body) > resolved_settings.max_request_body_bytes:
                return _error_response(413, "REQUEST_TOO_LARGE", "提交内容超出允许大小。")
        response = await call_next(request)
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Referrer-Policy"] = "same-origin"
        return response

    @application.exception_handler(BusinessError)
    async def handle_business_error(_: Request, exc: BusinessError):
        return _error_response(exc.status_code, exc.code, exc.message)

    @application.exception_handler(ClockError)
    async def handle_clock_error(_: Request, exc: ClockError):
        return _error_response(exc.status_code, exc.code, exc.message)

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError):
        errors = exc.errors()
        message = errors[0].get("msg", "请求内容不符合要求。") if errors else "请求内容不符合要求。"
        return _error_response(422, "INVALID_REQUEST", message)

    @application.exception_handler(sqlite3.Error)
    async def handle_database_error(_: Request, __: sqlite3.Error):
        return _error_response(
            503,
            "SERVICE_UNAVAILABLE",
            "星图暂时无法保存，请稍后再试。",
        )

    application.include_router(create_router(service, sessions, rate_limiter))

    @application.api_route(
        "/api/{unknown_path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        include_in_schema=False,
    )
    async def unknown_api_route(unknown_path: str):
        del unknown_path
        return _error_response(404, "NOT_FOUND", "没有找到这个接口。")

    if (
        resolved_settings.frontend_dist_path is not None
        and resolved_settings.frontend_dist_path.is_dir()
    ):
        application.mount(
            "/",
            StaticFiles(directory=resolved_settings.frontend_dist_path, html=True),
            name="frontend",
        )
    return application


app = create_app()
