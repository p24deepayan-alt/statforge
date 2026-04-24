"""Controller for managing model comparisons."""

from __future__ import annotations

import json
import uuid
from typing import Any

import matplotlib.pyplot as plt
from PySide6.QtCore import QObject, Signal

from app.analysis.comparison import compare_classifiers_roc
from app.controllers.data_controller import DataController
from app.controllers.model_controller import ModelController
from app.persistence.blob_store import BlobStore
from app.persistence.store import SessionStore
from app.util.errors import AnalysisError


class ComparisonController(QObject):
    """Generates comparison plots and saves them."""

    comparison_created = Signal(str)
    error_occurred = Signal(str)

    def __init__(
        self,
        store: SessionStore,
        blobs: BlobStore,
        data_ctrl: DataController,
        model_ctrl: ModelController,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._store = store
        self._blobs = blobs
        self._data_ctrl = data_ctrl
        self._model_ctrl = model_ctrl

    def generate_roc_comparison(self, session_id: str, model_ids: list[str]) -> dict[str, Any] | None:
        """Generates ROC curves for selected models and saves as a comparison artifact."""
        try:
            df = self._data_ctrl.load_dataset(session_id)
            
            models_data = []
            for mid in model_ids:
                meta = self._store.get_artifact(mid)
                if not meta:
                    continue
                spec = json.loads(meta["spec_json"])
                estimator = self._blobs.load_model(session_id, mid)
                if estimator:
                    models_data.append((meta["name"], estimator, spec))
            
            if not models_data:
                raise AnalysisError("Could not load selected models.")
                
            fig = compare_classifiers_roc(df, models_data)
            
            img_id = f"comp_{uuid.uuid4().hex[:8]}"
            self._blobs.save_plot(session_id, img_id, fig)
            plt.close(fig)
            
            rel_blob_path = f"plots/{img_id}.png"
            
            spec = {
                "comparison_type": "roc_curve",
                "model_ids": model_ids,
            }
            
            artifact = self._store.create_artifact(
                session_id=session_id,
                kind="plot",  # We save it as a plot so it appears in the gallery and report builder easily
                name="Model Comparison ROC",
                spec=spec,
                blob_path=rel_blob_path,
            )
            
            self.comparison_created.emit(artifact["id"])
            return artifact
            
        except Exception as exc:
            self.error_occurred.emit(str(exc))
            raise AnalysisError(f"Failed to generate comparison: {exc}") from exc
