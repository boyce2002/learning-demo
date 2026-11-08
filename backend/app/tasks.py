from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any


TASKS_PATH = Path(__file__).resolve().parents[1] / "data" / "tasks.json"
PUBLIC_TASK_FIELDS = {
    "key",
    "category",
    "title",
    "question",
    "estimated_minutes",
    "options",
}


def load_tasks(path: Path = TASKS_PATH) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        tasks = json.load(file)
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("任务种子不能为空。")
    keys = [task.get("key") for task in tasks]
    if len(keys) != len(set(keys)):
        raise ValueError("任务 key 必须唯一。")
    return tasks


def get_task_for_date(
    reference_date: date,
    tasks: list[dict[str, Any]],
    anchor_date: date,
) -> dict[str, Any]:
    index = (reference_date - anchor_date).days % len(tasks)
    return tasks[index]


def public_task(task: dict[str, Any]) -> dict[str, Any]:
    return {key: task[key] for key in PUBLIC_TASK_FIELDS}


def attempt_detail(task: dict[str, Any], selected_option: str) -> dict[str, Any]:
    was_correct = selected_option == task["correct_option"]
    return {
        "selected_option": selected_option,
        "was_correct": was_correct,
        "correct_option": task["correct_option"],
        "feedback": task["feedback_correct"] if was_correct else task["feedback_try_again"],
        "explanation": task["explanation"],
        "takeaway": task["takeaway"],
        "reflection_prompt": task["reflection_prompt"],
    }

