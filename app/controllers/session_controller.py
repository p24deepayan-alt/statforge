"""Session controller — create, open, delete, rename sessions."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

from app.persistence.blob_store import BlobStore
from app.persistence.store import SessionStore


class SessionController(QObject):
    """Mediates session lifecycle between the UI and persistence layers."""

    sessions_changed = Signal()
    session_opened = Signal(str)  # session_id

    def __init__(self, store: SessionStore, blobs: BlobStore, parent: QObject | None = None):
        super().__init__(parent)
        self._store = store
        self._blobs = blobs
        self._active_session_id: str | None = None

    @property
    def active_session_id(self) -> str | None:
        return self._active_session_id

    def list_sessions(self) -> list[dict[str, Any]]:
        return self._store.list_sessions()

    def create_session(self, name: str) -> dict[str, Any]:
        session = self._store.create_session(name=name)
        # Ensure the blob directory exists.
        self._blobs.session_dir(session["id"])
        self.sessions_changed.emit()
        return session

    def open_session(self, session_id: str) -> dict[str, Any] | None:
        session = self._store.get_session(session_id)
        if session:
            self._active_session_id = session_id
            self.session_opened.emit(session_id)
        return session

    def rename_session(self, session_id: str, new_name: str) -> None:
        self._store.update_session(session_id, name=new_name)
        self.sessions_changed.emit()

    def delete_session(self, session_id: str) -> None:
        self._blobs.delete_session_blobs(session_id)
        self._store.delete_session(session_id)
        if self._active_session_id == session_id:
            self._active_session_id = None
        self.sessions_changed.emit()

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        return self._store.get_session(session_id)

    def session_count(self) -> int:
        return len(self._store.list_sessions())

    def storage_size_bytes(self) -> int:
        """Total disk usage of all session blob directories."""
        sessions_dir = self._blobs._data_dir / "sessions"
        if not sessions_dir.exists():
            return 0
        total = 0
        for f in sessions_dir.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
        return total
