"""SQLite session and artifact registry.

All metadata lives here.  Large blobs (datasets, models, plots) are on disk
and referenced by relative path in the ``blob_path`` column.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.util.errors import PersistenceError
from app.util.ids import new_id

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionStore:
    """Thin wrapper around the StatForge SQLite database."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    # ── bootstrap ────────────────────────────────────────────────

    def _init_schema(self) -> None:
        schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
        self._conn.executescript(schema_sql)

    # ── sessions ─────────────────────────────────────────────────

    def create_session(
        self,
        name: str,
        source_filename: str | None = None,
        row_count: int | None = None,
        col_count: int | None = None,
    ) -> dict[str, Any]:
        sid = new_id()
        now = _now()
        self._conn.execute(
            """INSERT INTO sessions
               (id, name, created_at, modified_at, source_filename, row_count, col_count, app_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (sid, name, now, now, source_filename, row_count, col_count, "0.1.0"),
        )
        self._conn.commit()
        return self.get_session(sid)  # type: ignore[return-value]

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_sessions(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM sessions ORDER BY modified_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def update_session(self, session_id: str, **fields: Any) -> None:
        allowed = {"name", "source_filename", "row_count", "col_count", "modified_at"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return
        updates["modified_at"] = _now()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        vals = list(updates.values()) + [session_id]
        self._conn.execute(
            f"UPDATE sessions SET {set_clause} WHERE id = ?", vals  # noqa: S608
        )
        self._conn.commit()

    def delete_session(self, session_id: str) -> None:
        self._conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self._conn.commit()

    # ── artifacts ────────────────────────────────────────────────

    def create_artifact(
        self,
        session_id: str,
        kind: str,
        name: str,
        spec: dict[str, Any],
        metrics: dict[str, Any] | None = None,
        blob_path: str | None = None,
    ) -> dict[str, Any]:
        aid = new_id()
        now = _now()
        self._conn.execute(
            """INSERT INTO artifacts
               (id, session_id, kind, name, created_at, spec_json, metrics_json, blob_path)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                aid, session_id, kind, name, now,
                json.dumps(spec), json.dumps(metrics) if metrics else None,
                blob_path,
            ),
        )
        self._conn.commit()
        self._touch_session(session_id)
        return self.get_artifact(aid)  # type: ignore[return-value]

    def get_artifact(self, artifact_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_artifacts(self, session_id: str, kind: str | None = None) -> list[dict[str, Any]]:
        if kind:
            rows = self._conn.execute(
                "SELECT * FROM artifacts WHERE session_id = ? AND kind = ? ORDER BY created_at",
                (session_id, kind),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM artifacts WHERE session_id = ? ORDER BY created_at",
                (session_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def set_artifact_in_report(self, artifact_id: str, included: bool) -> None:
        self._conn.execute(
            "UPDATE artifacts SET in_report = ? WHERE id = ?",
            (1 if included else 0, artifact_id),
        )
        self._conn.commit()

    def delete_artifact(self, artifact_id: str) -> None:
        self._conn.execute("DELETE FROM artifacts WHERE id = ?", (artifact_id,))
        self._conn.commit()

    # ── preprocess steps ─────────────────────────────────────────

    def add_preprocess_step(
        self,
        session_id: str,
        step_index: int,
        op: str,
        params: dict[str, Any],
        description: str,
    ) -> int:
        now = _now()
        cur = self._conn.execute(
            """INSERT INTO preprocess_steps
               (session_id, step_index, op, params_json, description, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, step_index, op, json.dumps(params), description, now),
        )
        self._conn.commit()
        self._touch_session(session_id)
        return cur.lastrowid  # type: ignore[return-value]

    def list_preprocess_steps(self, session_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM preprocess_steps WHERE session_id = ? ORDER BY step_index",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_preprocess_steps_after(self, session_id: str, step_index: int) -> None:
        """Delete all steps with index > step_index (for undo)."""
        self._conn.execute(
            "DELETE FROM preprocess_steps WHERE session_id = ? AND step_index > ?",
            (session_id, step_index),
        )
        self._conn.commit()

    # ── reports ──────────────────────────────────────────────────

    def create_report(self, session_id: str, name: str, layout: list[Any]) -> dict[str, Any]:
        rid = new_id()
        self._conn.execute(
            """INSERT INTO reports (id, session_id, name, layout_json)
               VALUES (?, ?, ?, ?)""",
            (rid, session_id, name, json.dumps(layout)),
        )
        self._conn.commit()
        row = self._conn.execute("SELECT * FROM reports WHERE id = ?", (rid,)).fetchone()
        return dict(row)  # type: ignore[arg-type]

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM reports WHERE id = ?", (report_id,)
        ).fetchone()
        return dict(row) if row else None

    def update_report_layout(self, report_id: str, layout: list[Any]) -> None:
        self._conn.execute(
            "UPDATE reports SET layout_json = ? WHERE id = ?",
            (json.dumps(layout), report_id),
        )
        self._conn.commit()

    # ── helpers ──────────────────────────────────────────────────

    def _touch_session(self, session_id: str) -> None:
        self._conn.execute(
            "UPDATE sessions SET modified_at = ? WHERE id = ?", (_now(), session_id)
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
