from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS daily_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  local_date TEXT NOT NULL,
  task_key TEXT NOT NULL,
  selected_option TEXT NOT NULL,
  was_correct INTEGER NOT NULL CHECK (was_correct IN (0, 1)),
  attempted_at_utc TEXT NOT NULL,
  UNIQUE (user_id, local_date)
);

CREATE TABLE IF NOT EXISTS daily_completions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  local_date TEXT NOT NULL,
  task_key TEXT NOT NULL,
  attempt_id INTEGER NOT NULL UNIQUE,
  reflection TEXT NOT NULL,
  completed_at_utc TEXT NOT NULL,
  UNIQUE (user_id, local_date),
  FOREIGN KEY (attempt_id) REFERENCES daily_attempts(id)
);

CREATE INDEX IF NOT EXISTS idx_attempts_user_date
ON daily_attempts(user_id, local_date);

CREATE INDEX IF NOT EXISTS idx_completions_user_date
ON daily_completions(user_id, local_date);
"""


def connect_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def init_db(path: Path) -> None:
    with connect_db(path) as connection:
        connection.executescript(SCHEMA)


@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()

