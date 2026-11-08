from datetime import date

import pytest
from fastapi import Request, Response
from fastapi.testclient import TestClient

from app.config import Settings, load_settings
from app.main import create_app
from app.visitor import VisitorSessionManager
from conftest import complete_for_date


TEST_SECRET = "public-demo-test-secret-with-more-than-32-characters"


def public_settings(tmp_path, **overrides):
    values = {
        "database_path": tmp_path / "public-demo.sqlite3",
        "demo_mode": True,
        "demo_reset_enabled": False,
        "public_demo_enabled": True,
        "visitor_reset_enabled": True,
        "session_secret": TEST_SECRET,
        "cookie_secure": False,
        "allowed_origins": ("https://demo.example",),
        "seed_anchor_date": date(2026, 11, 5),
    }
    values.update(overrides)
    return Settings(**values)


def test_two_browser_sessions_are_fully_isolated(tmp_path):
    application = create_app(public_settings(tmp_path))
    with TestClient(application) as browser_a, TestClient(application) as browser_b:
        complete_for_date(browser_a, "2026-11-05", "A 浏览器留下的独立学习反思。")

        a_today = browser_a.get("/api/today?demo_date=2026-11-05").json()
        b_today = browser_b.get("/api/today?demo_date=2026-11-05").json()
        a_progress = browser_a.get("/api/progress?demo_date=2026-11-05").json()
        b_progress = browser_b.get("/api/progress?demo_date=2026-11-05").json()
        a_history = browser_a.get("/api/history?demo_date=2026-11-05").json()
        b_history = browser_b.get("/api/history?demo_date=2026-11-05").json()

        assert a_today["phase"] == "completed"
        assert b_today["phase"] == "not_started"
        assert a_progress["total_completed_days"] == 1
        assert b_progress["total_completed_days"] == 0
        assert len(a_history) == 1
        assert b_history == []
        assert browser_a.cookies.get("sparklab_session") != browser_b.cookies.get(
            "sparklab_session"
        )


def test_user_id_input_cannot_cross_or_clear_sessions(tmp_path):
    application = create_app(public_settings(tmp_path))
    with TestClient(application) as browser_a, TestClient(application) as browser_b:
        complete_for_date(browser_a, "2026-11-05", "A 访客自己的体验数据记录。")
        complete_for_date(browser_b, "2026-11-05", "B 访客自己的体验数据记录。")

        injected = browser_b.post(
            "/api/tasks/apple_browning/attempt?demo_date=2026-11-05",
            json={"selected_option": "b", "user_id": "another-user"},
        )
        reset_a = browser_a.post("/api/demo/reset?user_id=another-user")

        assert injected.status_code == 422
        assert reset_a.status_code == 200
        assert browser_a.get("/api/history?demo_date=2026-11-05").json() == []
        assert len(browser_b.get("/api/history?demo_date=2026-11-05").json()) == 1
        assert browser_a.post("/api/dev/reset").status_code == 404


def test_tampered_cookie_gets_new_empty_session(tmp_path):
    application = create_app(public_settings(tmp_path))
    with TestClient(application) as client:
        complete_for_date(client, "2026-11-05")
        original_cookie = client.cookies.get("sparklab_session")

        tampered = client.get(
            "/api/today?demo_date=2026-11-05",
            headers={"cookie": "sparklab_session=tampered"},
        )
        recovered = client.get(
            "/api/today?demo_date=2026-11-05",
            headers={"cookie": f"sparklab_session={original_cookie}"},
        )

        assert tampered.status_code == 200
        assert tampered.json()["phase"] == "not_started"
        assert "sparklab_session=" in tampered.headers["set-cookie"]
        assert recovered.json()["phase"] == "completed"


def test_expired_session_is_rejected_and_near_expiry_is_resigned(tmp_path):
    settings = public_settings(tmp_path, session_max_age_seconds=100)
    current_time = [1000.0]
    sessions = VisitorSessionManager(settings, time_provider=lambda: current_time[0])
    visitor_id = "a" * 32

    expired = sessions.encode(visitor_id, issued_at=899)
    assert sessions.decode(expired) is None

    near_expiry = sessions.encode(visitor_id, issued_at=940)
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "scheme": "https",
            "path": "/api/today",
            "query_string": b"",
            "headers": [(b"cookie", f"sparklab_session={near_expiry}".encode("ascii"))],
            "server": ("demo.example", 443),
            "client": ("127.0.0.1", 12345),
        }
    )
    response = Response()
    assert sessions.resolve(request, response) == visitor_id
    assert "sparklab_session=" in response.headers["set-cookie"]


def test_cross_site_write_and_oversized_body_are_rejected(tmp_path):
    settings = public_settings(tmp_path, max_request_body_bytes=120)
    application = create_app(settings)
    with TestClient(application) as client:
        client.get("/api/today?demo_date=2026-11-05")
        cross_site = client.post(
            "/api/tasks/apple_browning/attempt?demo_date=2026-11-05",
            headers={"origin": "https://evil.example", "sec-fetch-site": "cross-site"},
            json={"selected_option": "b"},
        )
        oversized = client.post(
            "/api/tasks/apple_browning/complete?demo_date=2026-11-05",
            content=b"x" * 121,
            headers={"content-type": "application/json"},
        )

        assert cross_site.status_code == 403
        assert cross_site.json()["detail"]["code"] == "CROSS_SITE_WRITE_FORBIDDEN"
        assert oversized.status_code == 413
        assert oversized.json()["detail"]["code"] == "REQUEST_TOO_LARGE"


def test_public_cookie_attributes_and_global_reset_absence(tmp_path):
    settings = public_settings(tmp_path, cookie_secure=True)
    application = create_app(settings)
    with TestClient(application, base_url="https://testserver") as client:
        response = client.get("/api/today?demo_date=2026-11-05")
        cookie = response.headers["set-cookie"].lower()

        assert "httponly" in cookie
        assert "secure" in cookie
        assert "samesite=lax" in cookie
        assert client.post("/api/dev/reset").status_code == 404


def test_public_mode_requires_persistent_session_secret(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "startup.sqlite3"))
    monkeypatch.setenv("PUBLIC_DEMO_ENABLED", "true")
    monkeypatch.delenv("SESSION_SECRET", raising=False)

    with pytest.raises(RuntimeError, match="SESSION_SECRET"):
        load_settings()


def test_write_rate_limit_is_per_visitor(tmp_path):
    settings = public_settings(tmp_path, write_rate_limit_per_minute=1)
    application = create_app(settings)
    with TestClient(application) as client:
        client.get("/api/today?demo_date=2026-11-05")
        first = client.post(
            "/api/tasks/apple_browning/attempt?demo_date=2026-11-05",
            json={"selected_option": "b"},
        )
        limited = client.post(
            "/api/tasks/apple_browning/attempt?demo_date=2026-11-05",
            json={"selected_option": "b"},
        )

        assert first.status_code == 200
        assert limited.status_code == 429
        assert limited.json()["detail"]["code"] == "RATE_LIMITED"
