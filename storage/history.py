import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from models.commit_request import CommitGenerationRequest
from models.commit_result import CommitResult


DEFAULT_DATABASE_PATH = Path("storage/commit_history.sqlite3")


class HistoryStorage:
    """Simple local SQLite storage for generated commits."""

    def __init__(self, database_path: Path | str = DEFAULT_DATABASE_PATH) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.enabled = os.getenv("HISTORY_ENABLED", "true").strip().lower() == "true"
        if self.enabled:
            self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS commit_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    original_description TEXT NOT NULL,
                    commit_style TEXT NOT NULL,
                    output_language TEXT NOT NULL,
                    selected_type TEXT NOT NULL,
                    scope TEXT,
                    recommended_commit TEXT NOT NULL,
                    alternatives TEXT NOT NULL,
                    semver_suggestion TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def save(self, request: CommitGenerationRequest, result: CommitResult) -> int | None:
        if not self.enabled:
            return None

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO commit_history (
                    created_at,
                    original_description,
                    commit_style,
                    output_language,
                    selected_type,
                    scope,
                    recommended_commit,
                    alternatives,
                    semver_suggestion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    request.change_description,
                    request.commit_style,
                    request.output_language,
                    request.change_type,
                    request.scope,
                    result.recommended_commit,
                    json.dumps(result.alternatives, ensure_ascii=False),
                    result.semver_suggestion,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def list_recent(self, limit: int = 10) -> list[dict]:
        if not self.enabled:
            return []

        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT * FROM commit_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        results: list[dict] = []
        for row in rows:
            item = dict(row)
            try:
                item["alternatives"] = json.loads(item.get("alternatives", "[]"))
            except json.JSONDecodeError:
                item["alternatives"] = []
            results.append(item)
        return results

    def clear(self) -> None:
        if not self.enabled:
            return

        with self._connect() as connection:
            connection.execute("DELETE FROM commit_history")
            connection.commit()
