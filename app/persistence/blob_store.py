"""File-backed storage for large binary payloads.

Datasets → parquet, fitted models → joblib, plots → PNG/SVG.
All writes use stage-then-rename for atomicity.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import joblib
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

if TYPE_CHECKING:
    from matplotlib.figure import Figure


class BlobStore:
    """Manages the ``sessions/<uuid>/`` directory tree on disk."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._cleanup_orphaned_tmp_files()

    def _cleanup_orphaned_tmp_files(self) -> None:
        """Removes any .tmp files left over from interrupted atomic writes."""
        sessions_dir = self._data_dir / "sessions"
        if not sessions_dir.exists():
            return
        for p in sessions_dir.rglob("*.tmp"):
            try:
                p.unlink()
            except Exception:
                pass

    # ── paths ────────────────────────────────────────────────────

    def session_dir(self, session_id: str) -> Path:
        d = self._data_dir / "sessions" / session_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _plots_dir(self, session_id: str) -> Path:
        d = self.session_dir(session_id) / "plots"
        d.mkdir(exist_ok=True)
        return d

    def _models_dir(self, session_id: str) -> Path:
        d = self.session_dir(session_id) / "models"
        d.mkdir(exist_ok=True)
        return d

    def _reports_dir(self, session_id: str) -> Path:
        d = self.session_dir(session_id) / "reports"
        d.mkdir(exist_ok=True)
        return d

    # ── datasets ─────────────────────────────────────────────────

    def save_dataset(self, session_id: str, df: pd.DataFrame, *, original: bool = False) -> Path:
        """Save a DataFrame as parquet.  ``original=True`` saves the immutable import copy."""
        name = "dataset_original.parquet" if original else "dataset.parquet"
        dest = self.session_dir(session_id) / name
        self._atomic_write_parquet(dest, df)
        return dest

    def load_dataset(self, session_id: str, *, original: bool = False) -> pd.DataFrame:
        name = "dataset_original.parquet" if original else "dataset.parquet"
        path = self.session_dir(session_id) / name
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")
        return pd.read_parquet(path)

    def dataset_exists(self, session_id: str, *, original: bool = False) -> bool:
        name = "dataset_original.parquet" if original else "dataset.parquet"
        return (self.session_dir(session_id) / name).exists()

    # ── plots ────────────────────────────────────────────────────

    def save_plot(self, session_id: str, plot_id: str, fig: Figure) -> dict[str, Path]:
        """Render a matplotlib Figure to PNG and SVG.  Returns ``{'png': ..., 'svg': ...}``."""
        plots = self._plots_dir(session_id)
        png_path = plots / f"{plot_id}.png"
        svg_path = plots / f"{plot_id}.svg"
        fig.savefig(str(png_path), dpi=150, bbox_inches="tight", format="png")
        fig.savefig(str(svg_path), bbox_inches="tight", format="svg")
        return {"png": png_path, "svg": svg_path}

    def load_plot_path(self, session_id: str, plot_id: str, fmt: str = "png") -> Path:
        return self._plots_dir(session_id) / f"{plot_id}.{fmt}"

    # ── models ───────────────────────────────────────────────────

    def save_model(self, session_id: str, model_id: str, estimator: object) -> Path:
        dest = self._models_dir(session_id) / f"{model_id}.joblib"
        self._atomic_write_joblib(dest, estimator)
        return dest

    def load_model(self, session_id: str, model_id: str) -> object:
        path = self._models_dir(session_id) / f"{model_id}.joblib"
        if not path.exists():
            raise FileNotFoundError(f"Model not found: {path}")
        return joblib.load(path)

    # ── session lifecycle ────────────────────────────────────────

    def delete_session_blobs(self, session_id: str) -> None:
        d = self._data_dir / "sessions" / session_id
        if d.exists():
            shutil.rmtree(d)

    # ── atomic write helpers ─────────────────────────────────────

    @staticmethod
    def _atomic_write_parquet(dest: Path, df: pd.DataFrame) -> None:
        table = pa.Table.from_pandas(df)
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(dest.parent), suffix=".tmp"
        )
        try:
            os.close(tmp_fd)
            pq.write_table(table, tmp_path)
            os.replace(tmp_path, str(dest))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    @staticmethod
    def _atomic_write_joblib(dest: Path, obj: object) -> None:
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(dest.parent), suffix=".tmp"
        )
        try:
            os.close(tmp_fd)
            joblib.dump(obj, tmp_path)
            os.replace(tmp_path, str(dest))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
