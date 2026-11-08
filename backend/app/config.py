from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_path: Path
    demo_mode: bool = False
    demo_reset_enabled: bool = False
    public_demo_enabled: bool = False
    visitor_reset_enabled: bool = False
    session_secret: str = ""
    session_cookie_name: str = "sparklab_session"
    session_max_age_seconds: int = 604800
    cookie_secure: bool = False
    allowed_origins: tuple[str, ...] = ()
    max_request_body_bytes: int = 4096
    write_rate_limit_per_minute: int = 60
    reset_rate_limit_per_hour: int = 3
    frontend_dist_path: Optional[Path] = None
    app_timezone: str = "Asia/Shanghai"
    seed_anchor_date: date = date(2026, 11, 5)
    demo_date_window_days: int = 30


def load_settings() -> Settings:
    raw_path = Path(os.getenv("DATABASE_PATH", "./data/sparklab.sqlite3"))
    if not raw_path.is_absolute():
        raw_path = BACKEND_ROOT / raw_path
    public_demo_enabled = _as_bool(os.getenv("PUBLIC_DEMO_ENABLED"))
    session_secret = os.getenv("SESSION_SECRET", "").strip()
    if public_demo_enabled and len(session_secret) < 32:
        raise RuntimeError("PUBLIC_DEMO_ENABLED=true 时 SESSION_SECRET 至少需要 32 个字符。")
    if not session_secret:
        session_secret = secrets.token_urlsafe(32)

    raw_frontend_path = os.getenv("FRONTEND_DIST_PATH", "").strip()
    frontend_dist_path = Path(raw_frontend_path).resolve() if raw_frontend_path else None
    allowed_origins = tuple(
        origin.strip().rstrip("/")
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    )

    return Settings(
        database_path=raw_path.resolve(),
        demo_mode=_as_bool(os.getenv("DEMO_MODE")),
        demo_reset_enabled=_as_bool(os.getenv("DEMO_RESET_ENABLED")),
        public_demo_enabled=public_demo_enabled,
        visitor_reset_enabled=_as_bool(os.getenv("VISITOR_RESET_ENABLED")),
        session_secret=session_secret,
        session_cookie_name=os.getenv("SESSION_COOKIE_NAME", "sparklab_session"),
        session_max_age_seconds=int(os.getenv("SESSION_MAX_AGE_SECONDS", "604800")),
        cookie_secure=_as_bool(os.getenv("COOKIE_SECURE"), default=public_demo_enabled),
        allowed_origins=allowed_origins,
        max_request_body_bytes=int(os.getenv("MAX_REQUEST_BODY_BYTES", "4096")),
        write_rate_limit_per_minute=int(os.getenv("WRITE_RATE_LIMIT_PER_MINUTE", "60")),
        reset_rate_limit_per_hour=int(os.getenv("RESET_RATE_LIMIT_PER_HOUR", "3")),
        frontend_dist_path=frontend_dist_path,
        app_timezone=os.getenv("APP_TIMEZONE", "Asia/Shanghai"),
        seed_anchor_date=date.fromisoformat(
            os.getenv("SEED_ANCHOR_DATE", "2026-11-05")
        ),
    )
