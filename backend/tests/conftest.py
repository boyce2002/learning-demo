from contextlib import contextmanager
from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client_factory(tmp_path):
    sequence = 0

    @contextmanager
    def make_client(
        *,
        demo_mode=True,
        reset_enabled=False,
        now=None,
    ):
        nonlocal sequence
        sequence += 1
        database_path = tmp_path / f"test-{sequence}.sqlite3"
        settings = Settings(
            database_path=database_path,
            demo_mode=demo_mode,
            demo_reset_enabled=reset_enabled,
            session_secret="test-session-secret-at-least-32-characters",
            seed_anchor_date=date(2026, 11, 5),
        )
        fixed_now = now or datetime(2026, 11, 5, 2, tzinfo=timezone.utc)
        application = create_app(settings, now_provider=lambda: fixed_now)
        with TestClient(application) as client:
            yield client, database_path

    return make_client


def complete_for_date(client, date_text, reflection="我记录下了今天发现的关键线索。"):
    query = f"?demo_date={date_text}"
    today = client.get(f"/api/today{query}").json()
    task_key = today["task"]["key"]
    attempt = client.post(
        f"/api/tasks/{task_key}/attempt{query}",
        json={"selected_option": "b"},
    )
    assert attempt.status_code == 200, attempt.text
    complete = client.post(
        f"/api/tasks/{task_key}/complete{query}",
        json={"reflection": reflection},
    )
    assert complete.status_code == 200, complete.text
    return complete.json()

