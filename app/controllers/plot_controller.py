"""Controller for generating and managing plots."""

from __future__ import annotations

import uuid
from typing import Any

import matplotlib.pyplot as plt
from PySide6.QtCore import QObject, Signal

from app.analysis.plotting import generate_plot
from app.controllers.data_controller import DataController
from app.persistence.blob_store import BlobStore
from app.persistence.store import SessionStore
from app.util.errors import AnalysisError


class PlotController(QObject):
    """Generates plots and saves them to the session registry."""

    plot_created = Signal(str)  # Emits artifact_id
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

    def get_plots(self, session_id: str) -> list[dict[str, Any]]:
        """List all plot artifacts for a session."""
        return self._store.list_artifacts(session_id, kind="plot")

    def create_plot(
        self, session_id: str, name: str, plot_type: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate a plot and persist it to the blob store and registry."""
        try:
            df = self._data_ctrl.load_dataset(session_id)
            
            # 1. Generate the Figure
            fig = generate_plot(df, plot_type, params)
            
            # 2. Save image files (PNG/SVG) to blobs
            # We use a distinct ID for the image files to decouple from artifact IDs
            img_id = f"plot_{uuid.uuid4().hex[:8]}"
            paths = self._blobs.save_plot(session_id, img_id, fig)
            
            # 3. Clean up matplotlib memory
            plt.close(fig)
            
            # 4. Save metadata to registry
            # We store the relative path to the PNG for the report HTML to use
            rel_blob_path = f"plots/{img_id}.png"
            
            # Construct spec to allow regeneration or report styling
            spec = {
                "plot_type": plot_type,
                "params": params,
                "title": name,
            }
            
            artifact = self._store.create_artifact(
                session_id=session_id,
                kind="plot",
                name=name,
                spec=spec,
                blob_path=rel_blob_path,
            )
            
            self.plot_created.emit(artifact["id"])
            return artifact

        except Exception as exc:
            self.error_occurred.emit(str(exc))
            raise AnalysisError(f"Failed to generate plot: {exc}") from exc

    def get_plot_image_path(self, session_id: str, artifact_id: str) -> str | None:
        """Returns the absolute path to the PNG file for a plot artifact."""
        artifact = self._store.get_artifact(artifact_id)
        if not artifact or artifact["kind"] != "plot" or not artifact["blob_path"]:
            return None
        
        # Resolve absolute path from blob store
        session_dir = self._blobs.session_dir(session_id)
        # blob_path is relative to the session dir, e.g., 'plots/xxx.png'
        # The artifact['blob_path'] actually contains 'plots/xxx.png'.
        return str(session_dir / artifact["blob_path"])
    
    def delete_plot(self, artifact_id: str) -> None:
        self._store.delete_artifact(artifact_id)
        # Note: We aren't deleting the PNGs from the blob store right away.
        # They will be cleaned up when the session is deleted to avoid sync issues.
