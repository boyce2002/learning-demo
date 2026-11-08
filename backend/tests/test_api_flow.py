import sqlite3

import pytest


def row_count(database_path, table):
    with sqlite3.connect(database_path) as connection:
        return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_t01_new_database_has_no_answer_leak(client_factory):
    with client_factory() as (client, _):
        today = client.get("/api/today?demo_date=2026-11-05")
        progress = client.get("/api/progress?demo_date=2026-11-05")

        assert today.status_code == 200
        payload = today.json()
        assert payload["phase"] == "not_started"
        assert payload["attempt"] is None
        assert payload["completion"] is None
        assert "correct_option" not in payload["task"]
        assert "explanation" not in payload["task"]
        assert progress.json()["streak_days"] == 0
        assert progress.json()["total_completed_days"] == 0
        assert today.headers["cache-control"] == "no-store"


def test_t02_same_date_is_stable_and_anchor_is_apple(client_factory):
    with client_factory() as (client, _):
        first = client.get("/api/today?demo_date=2026-11-05").json()
        second = client.get("/api/today?demo_date=2026-11-05").json()
        assert first["task"]["key"] == second["task"]["key"] == "apple_browning"


def test_t03_correct_attempt_is_persisted_once(client_factory):
    with client_factory() as (client, database_path):
        response = client.post(
            "/api/tasks/apple_browning/attempt?demo_date=2026-11-05",
            json={"selected_option": "b"},
        )
        assert response.status_code == 200
        assert response.json()["was_correct"] is True
        assert response.json()["correct_option"] == "b"
        assert response.json()["explanation"]
        assert row_count(database_path, "daily_attempts") == 1


def test_t04_wrong_attempt_can_still_complete(client_factory):
    with client_factory() as (client, database_path):
        attempt = client.post(
            "/api/tasks/apple_browning/attempt?demo_date=2026-11-05",
            json={"selected_option": "a"},
        )
        assert attempt.status_code == 200
        assert attempt.json()["was_correct"] is False
        assert attempt.json()["correct_option"] == "b"

        completed = client.post(
            "/api/tasks/apple_browning/complete?demo_date=2026-11-05",
            json={"reflection": "我知道了错误猜想也能帮助我找到答案。"},
        )
        assert completed.status_code == 200
        assert completed.json()["progress"]["streak_days"] == 1
        assert row_count(database_path, "daily_completions") == 1


def test_t05_attempt_is_idempotent_and_first_choice_is_locked(client_factory):
    with client_factory() as (client, database_path):
        url = "/api/tasks/apple_browning/attempt?demo_date=2026-11-05"
        first = client.post(url, json={"selected_option": "a"})
        repeated = client.post(url, json={"selected_option": "a"})
        changed = client.post(url, json={"selected_option": "b"})

        assert repeated.status_code == 200
        assert repeated.json() == first.json()
        assert changed.status_code == 409
        assert changed.json()["detail"]["code"] == "ATTEMPT_LOCKED"
        assert row_count(database_path, "daily_attempts") == 1


def test_t06_completion_requires_attempt(client_factory):
    with client_factory() as (client, database_path):
        response = client.post(
            "/api/tasks/apple_browning/complete?demo_date=2026-11-05",
            json={"reflection": "我留下了一句足够长的反思。"},
        )
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "ATTEMPT_REQUIRED"
        assert row_count(database_path, "daily_completions") == 0


@pytest.mark.parametrize(
    "reflection, expected_status",
    [
        ("", 422),
        ("     ", 422),
        ("一二三四五", 422),
        ("星" * 121, 422),
        ("一二三四五六", 200),
        ("星" * 120, 200),
    ],
)
def test_t07_reflection_boundaries(client_factory, reflection, expected_status):
    with client_factory() as (client, database_path):
        client.post(
            "/api/tasks/apple_browning/attempt?demo_date=2026-11-05",
            json={"selected_option": "b"},
        )
        response = client.post(
            "/api/tasks/apple_browning/complete?demo_date=2026-11-05",
            json={"reflection": reflection},
        )
        assert response.status_code == expected_status
        expected_rows = 1 if expected_status == 200 else 0
        assert row_count(database_path, "daily_completions") == expected_rows


def test_t08_completion_refresh_restores_state_and_trimmed_text(client_factory):
    with client_factory() as (client, _):
        client.post(
            "/api/tasks/apple_browning/attempt?demo_date=2026-11-05",
            json={"selected_option": "b"},
        )
        client.post(
            "/api/tasks/apple_browning/complete?demo_date=2026-11-05",
            json={"reflection": "  我会尝试减少苹果和空气的接触。  "},
        )
        refreshed = client.get("/api/today?demo_date=2026-11-05").json()
        assert refreshed["phase"] == "completed"
        assert refreshed["attempt"]["was_correct"] is True
        assert refreshed["completion"]["reflection"] == "我会尝试减少苹果和空气的接触。"


def test_t09_complete_is_idempotent_and_does_not_overwrite(client_factory):
    with client_factory() as (client, database_path):
        attempt_url = "/api/tasks/apple_browning/attempt?demo_date=2026-11-05"
        complete_url = "/api/tasks/apple_browning/complete?demo_date=2026-11-05"
        client.post(attempt_url, json={"selected_option": "b"})
        first = client.post(complete_url, json={"reflection": "第一次写下的真实发现。"})
        second = client.post(complete_url, json={"reflection": "第二次试图覆盖原来的发现。"})

        assert first.json()["newly_completed"] is True
        assert second.json()["newly_completed"] is False
        assert second.json()["completion"]["reflection"] == "第一次写下的真实发现。"
        assert second.json()["progress"]["total_completed_days"] == 1
        assert row_count(database_path, "daily_completions") == 1


def test_t16_rejects_wrong_task_and_invalid_option_without_writes(client_factory):
    with client_factory() as (client, database_path):
        wrong_task = client.post(
            "/api/tasks/active_recall/attempt?demo_date=2026-11-05",
            json={"selected_option": "b"},
        )
        invalid_option = client.post(
            "/api/tasks/apple_browning/attempt?demo_date=2026-11-05",
            json={"selected_option": "z"},
        )
        assert wrong_task.status_code == 409
        assert wrong_task.json()["detail"]["code"] == "TASK_MISMATCH"
        assert invalid_option.status_code == 422
        assert invalid_option.json()["detail"]["code"] == "INVALID_OPTION"
        assert row_count(database_path, "daily_attempts") == 0

