"""Controller for training and managing machine learning models."""

from __future__ import annotations

import uuid
from typing import Any

from PySide6.QtCore import QObject, Signal

from app.analysis.modeling import train_model
from app.controllers.data_controller import DataController
from app.persistence.blob_store import BlobStore
from app.persistence.store import SessionStore
from app.util.errors import AnalysisError


class ModelController(QObject):
    """Manages ML model training and persistence."""

    model_trained = Signal(str)  # Emits artifact_id
    error_occurred = Signal(str)

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

    def get_models(self, session_id: str) -> list[dict[str, Any]]:
        """List all model artifacts for a session."""
        return self._store.list_artifacts(session_id, kind="model")

    def train_and_save_model(
        self,
        session_id: str,
        name: str,
        model_type: str,
        target: str | None,
        features: list[str],
        params: dict[str, Any]
    ) -> dict[str, Any]:
        """Trains a model, saves it to disk via joblib, and records metadata."""
        try:
            df = self._data_ctrl.load_dataset(session_id)
            
            # 1. Train model and extract metrics
            model_obj, metrics = train_model(df, model_type, target, features, params)
            
            # 2. Save model object to blob store
            model_uuid = f"model_{uuid.uuid4().hex[:8]}"
            blob_path = self._blobs.save_model(session_id, model_uuid, model_obj)
            
            # 3. Save metadata to registry
            # We store metrics and configuration in the spec for easy retrieval in UI
            spec = {
                "model_type": model_type,
                "target": target,
                "features": features,
                "params": params,
                "metrics": metrics,
            }
            
            # Relies on the artifact's blob_path to find the joblib file later
            rel_blob_path = f"models/{model_uuid}.joblib"
            
            artifact = self._store.create_artifact(
                session_id=session_id,
                kind="model",
                name=name,
                spec=spec,
                blob_path=rel_blob_path,
            )
            
            self.model_trained.emit(artifact["id"])
            return artifact

        except Exception as exc:
            self.error_occurred.emit(str(exc))
            raise AnalysisError(f"Failed to train model: {exc}") from exc

    def train_stepwise_ols(
        self,
        session_id: str,
        name: str,
        target: str,
        candidates: list[str],
        alpha: float = 0.05
    ) -> dict[str, Any]:
        """Runs stepwise OLS selection, saves the best model, and records metadata."""
        try:
            df = self._data_ctrl.load_dataset(session_id)
            
            # 1. Run stepwise selection
            from app.analysis.modeling import stepwise_ols
            model_obj, metrics, selected_features = stepwise_ols(df, target, candidates, alpha)
            
            # 2. Save model object to blob store
            model_uuid = f"model_{uuid.uuid4().hex[:8]}"
            blob_path = self._blobs.save_model(session_id, model_uuid, model_obj)
            
            # 3. Save metadata to registry
            spec = {
                "model_type": "ols",
                "target": target,
                "features": selected_features,
                "params": {},
                "metrics": metrics,
            }
            
            rel_blob_path = f"models/{model_uuid}.joblib"
            
            artifact = self._store.create_artifact(
                session_id=session_id,
                kind="model",
                name=name,
                spec=spec,
                blob_path=rel_blob_path,
            )
            
            self.model_trained.emit(artifact["id"])
            return artifact

        except Exception as exc:
            self.error_occurred.emit(str(exc))
            raise AnalysisError(f"Failed to run stepwise selection: {exc}") from exc

    def delete_model(self, artifact_id: str) -> None:
        self._store.delete_artifact(artifact_id)
