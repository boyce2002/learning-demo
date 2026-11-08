from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone

from app.config import Settings
from app.database import init_db
from app.services import SparkLabService
from conftest import complete_for_date


def test_t10_t11_three_day_streak_then_gap(client_factory):
    with client_factory() as (client, _):
        for date_text in ["2026-11-05", "2026-11-06", "2026-11-07"]:
            complete_for_date(client, date_text)

        day_three = client.get("/api/progress?demo_date=2026-11-07").json()
        pending_next_day = client.get("/api/progress?demo_date=2026-11-08").json()
        after_gap = client.get("/api/progress?demo_date=2026-11-09").json()

        assert (day_three["streak_days"], day_three["total_completed_days"]) == (3, 3)
        assert (pending_next_day["streak_days"], pending_next_day["total_completed_days"]) == (3, 3)
        assert (after_gap["streak_days"], after_gap["total_completed_days"]) == (0, 3)


def test_t12_monday_week_starts_on_monday_without_losing_total(client_factory):
    with client_factory() as (client, _):
        for date_text in ["2026-11-05", "2026-11-06", "2026-11-07"]:
            complete_for_date(client, date_text)
        progress = client.get("/api/progress?demo_date=2026-11-09").json()
        assert progress["week_days"][0]["date"] == "2026-11-09"
        assert progress["week_days"][0]["status"] == "today_pending"
        assert progress["total_completed_days"] == 3


def test_t13_future_records_do_not_leak_into_past_view(client_factory):
    with client_factory() as (client, _):
        for date_text in ["2026-11-05", "2026-11-06", "2026-11-07"]:
            complete_for_date(client, date_text)
        past = client.get("/api/progress?demo_date=2026-11-05").json()
        assert past["total_completed_days"] == 1
        assert past["streak_days"] == 1
        assert all(
            item["status"] == "future"
            for item in past["week_days"]
            if item["date"] > "2026-11-05"
        )


def test_t17_concurrent_completion_creates_one_row(tmp_path):
    settings = Settings(
        database_path=tmp_path / "concurrent.sqlite3",
        demo_mode=True,
        seed_anchor_date=date(2026, 11, 5),
    )
    now = datetime(2026, 11, 5, 2, tzinfo=timezone.utc)
    service = SparkLabService(settings, now_provider=lambda: now)
    init_db(settings.database_path)
    reference_date = date(2026, 11, 5)
    visitor_id = "concurrent-test-visitor"
    service.record_attempt(visitor_id, reference_date, "apple_browning", "b")

    def finish(reflection):
        return service.complete_day(
            visitor_id,
            reference_date,
            "apple_browning",
            reflection,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(finish, ["并发提交留下的第一种反思。", "并发提交留下的第二种反思。"]))

    assert sorted(item["newly_completed"] for item in results) == [False, True]
    assert results[0]["completion"] == results[1]["completion"]
    assert results[0]["progress"]["total_completed_days"] == 1


def test_t18_shanghai_midnight_maps_to_correct_local_date(client_factory):
    just_after_midnight = datetime(2026, 11, 4, 16, 1, tzinfo=timezone.utc)
    with client_factory(demo_mode=False, now=just_after_midnight) as (client, _):
        today = client.get("/api/today").json()
        assert today["reference_date"] == "2026-11-05"
        assert today["task"]["key"] == "apple_browning"

    just_before_midnight = datetime(2026, 11, 4, 15, 59, tzinfo=timezone.utc)
    with client_factory(demo_mode=False, now=just_before_midnight) as (client, _):
        today = client.get("/api/today").json()
        assert today["reference_date"] == "2026-11-04"
        assert today["task"]["key"] == "water_reflection"

