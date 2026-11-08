from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Callable, Optional
from zoneinfo import ZoneInfo

from .config import Settings


class ClockError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


NowProvider = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def resolve_reference_date(
    settings: Settings,
    demo_date: Optional[str],
    now_provider: NowProvider = utc_now,
) -> date:
    now = now_provider()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    real_local_date = now.astimezone(ZoneInfo(settings.app_timezone)).date()

    if demo_date is None:
        return real_local_date
    if not settings.demo_mode:
        raise ClockError(
            403,
            "DEMO_DATE_FORBIDDEN",
            "当前不是演示模式，不能切换日期。",
        )
    try:
        requested = date.fromisoformat(demo_date)
    except ValueError as exc:
        raise ClockError(422, "INVALID_DEMO_DATE", "演示日期格式应为 YYYY-MM-DD。") from exc

    if abs((requested - real_local_date).days) > settings.demo_date_window_days:
        raise ClockError(
            422,
            "DEMO_DATE_OUT_OF_RANGE",
            f"演示日期需在当前日期前后 {settings.demo_date_window_days} 天内。",
        )
    return requested
