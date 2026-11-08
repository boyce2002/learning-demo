from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from typing import Callable, Optional

from fastapi import Request, Response

from .config import Settings


TimeProvider = Callable[[], float]


@dataclass(frozen=True)
class SessionPayload:
    visitor_id: str
    issued_at: int


class VisitorSessionManager:
    """Issues and verifies opaque anonymous visitor identities.

    The browser never supplies a user id to an API method. The only accepted
    identity is a server-signed cookie containing a random 128-bit identifier.
    """

    def __init__(
        self,
        settings: Settings,
        time_provider: TimeProvider = time.time,
    ) -> None:
        if not settings.session_secret:
            raise ValueError("session_secret must not be empty")
        self.settings = settings
        self.time_provider = time_provider
        self._secret = settings.session_secret.encode("utf-8")

    def encode(self, visitor_id: str, issued_at: Optional[int] = None) -> str:
        timestamp = int(self.time_provider()) if issued_at is None else issued_at
        payload = f"v1.{timestamp}.{visitor_id}"
        signature = hmac.new(
            self._secret,
            payload.encode("ascii"),
            hashlib.sha256,
        ).hexdigest()
        return f"{payload}.{signature}"

    def decode(self, raw_cookie: str) -> Optional[SessionPayload]:
        try:
            version, issued_text, visitor_id, signature = raw_cookie.split(".", 3)
            issued_at = int(issued_text)
        except (TypeError, ValueError):
            return None
        if version != "v1" or len(visitor_id) != 32:
            return None
        if any(character not in "0123456789abcdef" for character in visitor_id):
            return None
        payload = f"{version}.{issued_at}.{visitor_id}"
        expected = hmac.new(
            self._secret,
            payload.encode("ascii"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        now = int(self.time_provider())
        if issued_at > now + 60 or now - issued_at > self.settings.session_max_age_seconds:
            return None
        return SessionPayload(visitor_id=visitor_id, issued_at=issued_at)

    def resolve(self, request: Request, response: Response) -> str:
        raw_cookie = request.cookies.get(self.settings.session_cookie_name, "")
        payload = self.decode(raw_cookie) if raw_cookie else None
        now = int(self.time_provider())
        should_refresh = payload is None
        if payload is None:
            payload = SessionPayload(visitor_id=secrets.token_hex(16), issued_at=now)
        elif now - payload.issued_at > self.settings.session_max_age_seconds // 2:
            payload = SessionPayload(visitor_id=payload.visitor_id, issued_at=now)
            should_refresh = True

        if should_refresh:
            response.set_cookie(
                key=self.settings.session_cookie_name,
                value=self.encode(payload.visitor_id, payload.issued_at),
                max_age=self.settings.session_max_age_seconds,
                httponly=True,
                secure=self.settings.cookie_secure,
                samesite="lax",
                path="/",
            )
        return payload.visitor_id
