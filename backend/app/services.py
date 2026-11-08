from __future__ import annotations

from datetime import date, timedelta, timezone
from typing import Any, Optional

from .clock import NowProvider, resolve_reference_date, utc_now
from .config import Settings
from .database import connect_db, transaction
from .tasks import attempt_detail, get_task_for_date, load_tasks, public_task


class BusinessError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class SparkLabService:
    def __init__(
        self,
        settings: Settings,
        now_provider: NowProvider = utc_now,
    ) -> None:
        self.settings = settings
        self.now_provider = now_provider
        self.tasks = load_tasks()

    def reference_date(self, demo_date: Optional[str]) -> date:
        return resolve_reference_date(self.settings, demo_date, self.now_provider)

    def task_for_date(self, reference_date: date) -> dict[str, Any]:
        return get_task_for_date(
            reference_date,
            self.tasks,
            self.settings.seed_anchor_date,
        )

    def _checked_task(self, reference_date: date, task_key: str) -> dict[str, Any]:
        task = self.task_for_date(reference_date)
        if task["key"] != task_key:
            raise BusinessError(
                409,
                "TASK_MISMATCH",
                "今天的任务已更新，请刷新星图。",
            )
        return task

    def get_today(self, visitor_id: str, reference_date: date) -> dict[str, Any]:
        task = self.task_for_date(reference_date)
        date_text = reference_date.isoformat()
        with connect_db(self.settings.database_path) as connection:
            attempt = connection.execute(
                """
                SELECT * FROM daily_attempts
                WHERE user_id = ? AND local_date = ?
                """,
                (visitor_id, date_text),
            ).fetchone()
            completion = connection.execute(
                """
                SELECT * FROM daily_completions
                WHERE user_id = ? AND local_date = ?
                """,
                (visitor_id, date_text),
            ).fetchone()

        if completion is not None:
            phase = "completed"
        elif attempt is not None:
            phase = "attempted"
        else:
            phase = "not_started"

        return {
            "reference_date": date_text,
            "timezone": self.settings.app_timezone,
            "is_demo_mode": self.settings.demo_mode,
            "is_ephemeral_storage": self.settings.ephemeral_storage,
            "demo_reset_enabled": (
                self.settings.visitor_reset_enabled
                if self.settings.public_demo_enabled
                else self.settings.demo_reset_enabled
            ),
            "user_id": "anonymous_visitor",
            "phase": phase,
            "task": public_task(task),
            "attempt": (
                attempt_detail(task, attempt["selected_option"])
                if attempt is not None
                else None
            ),
            "completion": (
                {
                    "reflection": completion["reflection"],
                    "completed_at_utc": completion["completed_at_utc"],
                }
                if completion is not None
                else None
            ),
        }

    def record_attempt(
        self,
        visitor_id: str,
        reference_date: date,
        task_key: str,
        selected_option: str,
    ) -> dict[str, Any]:
        task = self._checked_task(reference_date, task_key)
        valid_options = {option["key"] for option in task["options"]}
        if selected_option not in valid_options:
            raise BusinessError(422, "INVALID_OPTION", "请选择页面中的一个选项。")

        date_text = reference_date.isoformat()
        with connect_db(self.settings.database_path) as connection:
            with transaction(connection):
                existing = connection.execute(
                    """
                    SELECT * FROM daily_attempts
                    WHERE user_id = ? AND local_date = ?
                    """,
                    (visitor_id, date_text),
                ).fetchone()
                if existing is not None:
                    if existing["selected_option"] != selected_option:
                        raise BusinessError(
                            409,
                            "ATTEMPT_LOCKED",
                            "今天的猜想已经保存，请继续学习。",
                        )
                    return attempt_detail(task, existing["selected_option"])

                now = self.now_provider()
                if now.tzinfo is None:
                    now = now.replace(tzinfo=timezone.utc)
                was_correct = int(selected_option == task["correct_option"])
                connection.execute(
                    """
                    INSERT INTO daily_attempts (
                        user_id, local_date, task_key, selected_option,
                        was_correct, attempted_at_utc
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        visitor_id,
                        date_text,
                        task_key,
                        selected_option,
                        was_correct,
                        now.astimezone(timezone.utc).isoformat(),
                    ),
                )
        return attempt_detail(task, selected_option)

    def complete_day(
        self,
        visitor_id: str,
        reference_date: date,
        task_key: str,
        reflection: str,
    ) -> dict[str, Any]:
        self._checked_task(reference_date, task_key)
        date_text = reference_date.isoformat()
        newly_completed = False

        with connect_db(self.settings.database_path) as connection:
            with transaction(connection):
                existing = connection.execute(
                    """
                    SELECT * FROM daily_completions
                    WHERE user_id = ? AND local_date = ?
                    """,
                    (visitor_id, date_text),
                ).fetchone()
                if existing is not None:
                    completion = existing
                else:
                    attempt = connection.execute(
                        """
                        SELECT * FROM daily_attempts
                        WHERE user_id = ? AND local_date = ?
                        """,
                        (visitor_id, date_text),
                    ).fetchone()
                    if attempt is None:
                        raise BusinessError(
                            409,
                            "ATTEMPT_REQUIRED",
                            "请先做出猜想，再留下今天的发现。",
                        )
                    if attempt["task_key"] != task_key:
                        raise BusinessError(
                            409,
                            "TASK_MISMATCH",
                            "今天的任务已更新，请刷新星图。",
                        )

                    cleaned = reflection.strip()
                    length = len(cleaned)
                    if length < 6 or length > 120:
                        raise BusinessError(
                            422,
                            "INVALID_REFLECTION",
                            "今日收获去掉首尾空格后需为 6–120 个字符。",
                        )

                    now = self.now_provider()
                    if now.tzinfo is None:
                        now = now.replace(tzinfo=timezone.utc)
                    completed_at = now.astimezone(timezone.utc).isoformat()
                    cursor = connection.execute(
                        """
                        INSERT INTO daily_completions (
                            user_id, local_date, task_key, attempt_id,
                            reflection, completed_at_utc
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            visitor_id,
                            date_text,
                            task_key,
                            attempt["id"],
                            cleaned,
                            completed_at,
                        ),
                    )
                    completion = connection.execute(
                        "SELECT * FROM daily_completions WHERE id = ?",
                        (cursor.lastrowid,),
                    ).fetchone()
                    newly_completed = True

        return {
            "newly_completed": newly_completed,
            "completion": {
                "reflection": completion["reflection"],
                "completed_at_utc": completion["completed_at_utc"],
            },
            "progress": self.get_progress(visitor_id, reference_date),
        }

    @staticmethod
    def compute_streak(reference_date: date, completed_dates: set[date]) -> int:
        if reference_date in completed_dates:
            cursor = reference_date
        elif reference_date - timedelta(days=1) in completed_dates:
            cursor = reference_date - timedelta(days=1)
        else:
            return 0

        streak = 0
        while cursor in completed_dates:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def get_progress(self, visitor_id: str, reference_date: date) -> dict[str, Any]:
        with connect_db(self.settings.database_path) as connection:
            rows = connection.execute(
                """
                SELECT local_date FROM daily_completions
                WHERE user_id = ? AND local_date <= ?
                ORDER BY local_date
                """,
                (visitor_id, reference_date.isoformat()),
            ).fetchall()
        completed_dates = {date.fromisoformat(row["local_date"]) for row in rows}
        week_start = reference_date - timedelta(days=reference_date.weekday())
        week_days = []
        for offset in range(7):
            day = week_start + timedelta(days=offset)
            if day > reference_date:
                status = "future"
            elif day in completed_dates:
                status = "done"
            elif day == reference_date:
                status = "today_pending"
            else:
                status = "missed"
            week_days.append({"date": day.isoformat(), "status": status})

        return {
            "reference_date": reference_date.isoformat(),
            "streak_days": self.compute_streak(reference_date, completed_dates),
            "total_completed_days": len(completed_dates),
            "today_completed": reference_date in completed_dates,
            "week_days": week_days,
        }

    def get_history(
        self,
        visitor_id: str,
        reference_date: date,
        limit: int,
    ) -> list[dict[str, Any]]:
        with connect_db(self.settings.database_path) as connection:
            rows = connection.execute(
                """
                SELECT
                    c.local_date,
                    c.task_key,
                    c.reflection,
                    c.completed_at_utc,
                    a.was_correct
                FROM daily_completions AS c
                JOIN daily_attempts AS a ON a.id = c.attempt_id
                WHERE c.user_id = ? AND c.local_date <= ?
                ORDER BY c.local_date DESC
                LIMIT ?
                """,
                (visitor_id, reference_date.isoformat(), limit),
            ).fetchall()
        titles = {task["key"]: task["title"] for task in self.tasks}
        return [
            {
                "local_date": row["local_date"],
                "task_key": row["task_key"],
                "task_title": titles.get(row["task_key"], row["task_key"]),
                "reflection": row["reflection"],
                "was_correct": bool(row["was_correct"]),
                "completed_at_utc": row["completed_at_utc"],
            }
            for row in rows
        ]

    def reset_demo_user(self, visitor_id: str) -> dict[str, int]:
        if not (
            self.settings.demo_mode
            and self.settings.demo_reset_enabled
            and not self.settings.public_demo_enabled
        ):
            raise BusinessError(
                403,
                "DEMO_RESET_FORBIDDEN",
                "当前环境未启用演示重置。",
            )
        with connect_db(self.settings.database_path) as connection:
            with transaction(connection):
                deleted_completions = connection.execute(
                    "DELETE FROM daily_completions WHERE user_id = ?",
                    (visitor_id,),
                ).rowcount
                deleted_attempts = connection.execute(
                    "DELETE FROM daily_attempts WHERE user_id = ?",
                    (visitor_id,),
                ).rowcount
        return {
            "deleted_attempts": deleted_attempts,
            "deleted_completions": deleted_completions,
        }

    def reset_visitor(self, visitor_id: str) -> dict[str, int]:
        if not (
            self.settings.public_demo_enabled
            and self.settings.visitor_reset_enabled
        ):
            raise BusinessError(
                403,
                "VISITOR_RESET_FORBIDDEN",
                "当前环境未启用访客体验重置。",
            )
        with connect_db(self.settings.database_path) as connection:
            with transaction(connection):
                deleted_completions = connection.execute(
                    "DELETE FROM daily_completions WHERE user_id = ?",
                    (visitor_id,),
                ).rowcount
                deleted_attempts = connection.execute(
                    "DELETE FROM daily_attempts WHERE user_id = ?",
                    (visitor_id,),
                ).rowcount
        return {
            "deleted_attempts": deleted_attempts,
            "deleted_completions": deleted_completions,
        }
