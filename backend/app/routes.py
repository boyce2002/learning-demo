from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, Response

from .schemas import AttemptRequest, CompleteRequest
from .security import InMemoryRateLimiter, is_trusted_write
from .services import BusinessError, SparkLabService
from .visitor import VisitorSessionManager


def create_router(
    service: SparkLabService,
    sessions: VisitorSessionManager,
    rate_limiter: InMemoryRateLimiter,
) -> APIRouter:
    router = APIRouter(prefix="/api")

    def current_visitor(request: Request, response: Response) -> str:
        return sessions.resolve(request, response)

    def check_write(request: Request, visitor_id: str, action: str = "write") -> None:
        if not is_trusted_write(request, service.settings):
            raise BusinessError(403, "CROSS_SITE_WRITE_FORBIDDEN", "无法验证此次写入来源。")
        limit = (
            service.settings.reset_rate_limit_per_hour
            if action == "reset"
            else service.settings.write_rate_limit_per_minute
        )
        window = 3600 if action == "reset" else 60
        if not rate_limiter.allow(visitor_id, action, limit, window):
            raise BusinessError(429, "RATE_LIMITED", "操作有些频繁，请稍后再试。")

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "app": "sparklab"}

    @router.get("/today")
    def today(
        demo_date: Optional[str] = Query(default=None),
        visitor_id: str = Depends(current_visitor),
    ) -> dict:
        reference_date = service.reference_date(demo_date)
        return service.get_today(visitor_id, reference_date)

    @router.get("/progress")
    def progress(
        demo_date: Optional[str] = Query(default=None),
        visitor_id: str = Depends(current_visitor),
    ) -> dict:
        reference_date = service.reference_date(demo_date)
        return service.get_progress(visitor_id, reference_date)

    @router.get("/history")
    def history(
        limit: int = Query(default=7, ge=1, le=30),
        demo_date: Optional[str] = Query(default=None),
        visitor_id: str = Depends(current_visitor),
    ) -> list[dict]:
        reference_date = service.reference_date(demo_date)
        return service.get_history(visitor_id, reference_date, limit)

    @router.post("/tasks/{task_key}/attempt")
    def attempt(
        task_key: str,
        payload: AttemptRequest,
        request: Request,
        demo_date: Optional[str] = Query(default=None),
        visitor_id: str = Depends(current_visitor),
    ) -> dict:
        check_write(request, visitor_id)
        reference_date = service.reference_date(demo_date)
        return service.record_attempt(
            visitor_id,
            reference_date,
            task_key,
            payload.selected_option,
        )

    @router.post("/tasks/{task_key}/complete")
    def complete(
        task_key: str,
        payload: CompleteRequest,
        request: Request,
        demo_date: Optional[str] = Query(default=None),
        visitor_id: str = Depends(current_visitor),
    ) -> dict:
        check_write(request, visitor_id)
        reference_date = service.reference_date(demo_date)
        return service.complete_day(visitor_id, reference_date, task_key, payload.reflection)

    if (
        service.settings.demo_mode
        and service.settings.demo_reset_enabled
        and not service.settings.public_demo_enabled
    ):
        @router.post("/dev/reset")
        def reset_demo(
            request: Request,
            visitor_id: str = Depends(current_visitor),
        ) -> dict[str, int]:
            check_write(request, visitor_id, "reset")
            return service.reset_demo_user(visitor_id)

    if service.settings.public_demo_enabled and service.settings.visitor_reset_enabled:
        @router.post("/demo/reset")
        def reset_visitor_demo(
            request: Request,
            visitor_id: str = Depends(current_visitor),
        ) -> dict[str, int]:
            check_write(request, visitor_id, "reset")
            return service.reset_visitor(visitor_id)

    return router
