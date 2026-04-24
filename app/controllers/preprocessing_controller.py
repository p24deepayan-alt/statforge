"""Controller for the preprocessing pipeline."""

from __future__ import annotations

from typing import Any

import pandas as pd
from PySide6.QtCore import QObject, Signal

from app.analysis.preprocessing import apply_operation
from app.controllers.data_controller import DataController
from app.persistence.blob_store import BlobStore
from app.persistence.store import SessionStore
from app.util.errors import PreprocessingError


class PreprocessingController(QObject):
    """Manages the application and undoing of preprocessing steps."""

    pipeline_changed = Signal(str)  # Emits session_id when steps change
    error_occurred = Signal(str)    # Emits error messages for the UI

    def __init__(
        self,
        store: SessionStore,
        blobs: BlobStore,
        data_ctrl: DataController,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._store = store
        self._blobs = blobs
        self._data_ctrl = data_ctrl

    def get_steps(self, session_id: str) -> list[dict[str, Any]]:
        """Return the ordered list of preprocessing steps."""
        return self._store.list_preprocess_steps(session_id)

    def can_undo(self, session_id: str) -> bool:
        """Return True if there is at least one step to undo."""
        return len(self.get_steps(session_id)) > 0

    def apply_step(self, session_id: str, op: str, params: dict[str, Any], description: str) -> None:
        """Apply a new step to the working dataset and persist it."""
        try:
            # 1. Load the current working dataset
            df = self._data_ctrl.load_dataset(session_id, original=False)

            # 2. Apply the operation
            df_new = apply_operation(df, op, params)

            # 3. Determine the step index
            steps = self.get_steps(session_id)
            step_index = steps[-1]["step_index"] + 1 if steps else 0

            # 4. Save the new working dataset
            self._blobs.save_dataset(session_id, df_new, original=False)

            # 5. Persist the step metadata
            self._store.add_preprocess_step(session_id, step_index, op, params, description)

            # 6. Invalidate data controller cache so UI gets fresh stats
            self._data_ctrl._invalidate_cache(session_id)
            self.pipeline_changed.emit(session_id)

        except Exception as exc:
            self.error_occurred.emit(str(exc))
            raise PreprocessingError(f"Failed to apply {op}: {exc}") from exc

    def undo_last_step(self, session_id: str) -> None:
        """Revert the most recent step.
        
        Because transformations can be destructive (like dropping rows),
        we undo by dropping the last step metadata, loading the original
        pristine dataset, and replaying all remaining steps sequentially.
        """
        steps = self.get_steps(session_id)
        if not steps:
            return

        last_step = steps[-1]
        remaining_steps = steps[:-1]

        try:
            # 1. Delete the last step from the registry
            self._store.delete_preprocess_steps_after(session_id, last_step["step_index"] - 1)

            # 2. Rebuild the dataset from the original source
            df = self._data_ctrl.load_dataset(session_id, original=True)

            for step in remaining_steps:
                import json
                params = json.loads(step["params_json"])
                df = apply_operation(df, step["op"], params)

            # 3. Save the rebuilt dataset as the new working copy
            self._blobs.save_dataset(session_id, df, original=False)

            # 4. Invalidate cache and notify
            self._data_ctrl._invalidate_cache(session_id)
            self.pipeline_changed.emit(session_id)

        except Exception as exc:
            self.error_occurred.emit(f"Failed during undo: {exc}")
            # If rebuild fails, we are in an inconsistent state.
            # In a production app we'd want more robust recovery here.
            raise PreprocessingError(f"Undo failed: {exc}") from exc
