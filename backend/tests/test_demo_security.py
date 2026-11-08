from conftest import complete_for_date


def test_t14_normal_mode_forbids_demo_date(client_factory):
    with client_factory(demo_mode=False) as (client, _):
        response = client.get("/api/today?demo_date=2026-11-05")
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "DEMO_DATE_FORBIDDEN"


def test_t15_reset_route_is_absent_unless_both_flags_are_enabled(client_factory):
    with client_factory(demo_mode=False, reset_enabled=False) as (client, _):
        assert client.post("/api/dev/reset").status_code == 404

    with client_factory(demo_mode=True, reset_enabled=False) as (client, _):
        assert client.post("/api/dev/reset").status_code == 404


def test_t15_enabled_demo_reset_deletes_both_tables(client_factory):
    with client_factory(demo_mode=True, reset_enabled=True) as (client, _):
        complete_for_date(client, "2026-11-05")
        reset = client.post("/api/dev/reset")
        assert reset.status_code == 200
        assert reset.json() == {"deleted_attempts": 1, "deleted_completions": 1}
        assert client.get("/api/today?demo_date=2026-11-05").json()["phase"] == "not_started"


def test_demo_date_outside_safe_window_is_rejected(client_factory):
    with client_factory(demo_mode=True) as (client, _):
        response = client.get("/api/today?demo_date=2027-01-01")
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "DEMO_DATE_OUT_OF_RANGE"


def test_t19_history_is_limited_descending_and_hides_future(client_factory):
    with client_factory(demo_mode=True) as (client, _):
        for date_text in ["2026-11-05", "2026-11-06", "2026-11-07"]:
            complete_for_date(client, date_text, reflection=f"{date_text} 留下的真实反思。")

        latest_two = client.get("/api/history?limit=2&demo_date=2026-11-07")
        past_view = client.get("/api/history?limit=7&demo_date=2026-11-05")

        assert latest_two.status_code == 200
        assert [item["local_date"] for item in latest_two.json()] == ["2026-11-07", "2026-11-06"]
        assert latest_two.json()[0]["task_title"]
        assert isinstance(latest_two.json()[0]["was_correct"], bool)
        assert [item["local_date"] for item in past_view.json()] == ["2026-11-05"]
