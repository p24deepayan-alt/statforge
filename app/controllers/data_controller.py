"""Data controller — import, parse, and manage datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from PySide6.QtCore import QObject, Signal

from app.analysis.descriptive import compute_all_stats, compute_column_stats
from app.persistence.blob_store import BlobStore
from app.persistence.store import SessionStore
from app.util.errors import DataImportError


class DataController(QObject):
    """Handles file import, dataset loading, and descriptive statistics."""

    data_loaded = Signal(str)  # session_id
    stats_computed = Signal(list)  # list of stat dicts

    def __init__(self, store: SessionStore, blobs: BlobStore, parent: QObject | None = None):
        super().__init__(parent)
        self._store = store
        self._blobs = blobs
        self._stats_cache: dict[str, list[dict[str, Any]]] = {}

    # ── import ───────────────────────────────────────────────

    def preview_file(
        self,
        path: Path,
        delimiter: str | None = None,
        has_header: bool = True,
        encoding: str = "utf-8",
        nrows: int = 50,
    ) -> pd.DataFrame:
        """Load a preview of the first ``nrows`` rows for the import dialog."""
        try:
            if path.suffix.lower() in (".xlsx", ".xls"):
                return pd.read_excel(path, nrows=nrows)
            sep = delimiter or self._detect_delimiter(path, encoding)
            header = 0 if has_header else None
            return pd.read_csv(
                path, sep=sep, header=header, encoding=encoding,
                nrows=nrows, on_bad_lines="skip",
            )
        except Exception as exc:
            raise DataImportError(f"Failed to preview {path.name}: {exc}") from exc

    def import_file(
        self,
        session_id: str,
        path: Path,
        delimiter: str | None = None,
        has_header: bool = True,
        encoding: str = "utf-8",
        dtype_overrides: dict[str, str] | None = None,
    ) -> pd.DataFrame:
        """Full import: read file, save original + working copy, update session metadata."""
        try:
            if path.suffix.lower() in (".xlsx", ".xls"):
                df = pd.read_excel(path)
            else:
                sep = delimiter or self._detect_delimiter(path, encoding)
                header = 0 if has_header else None
                df = pd.read_csv(
                    path, sep=sep, header=header, encoding=encoding,
                    on_bad_lines="skip",
                )
        except Exception as exc:
            raise DataImportError(f"Failed to import {path.name}: {exc}") from exc

        # Apply dtype overrides from user.
        if dtype_overrides:
            for col, dtype in dtype_overrides.items():
                if col in df.columns:
                    try:
                        df[col] = df[col].astype(dtype)
                    except (ValueError, TypeError):
                        pass  # Keep original type if cast fails.

        # Persist both copies.
        self._blobs.save_dataset(session_id, df, original=True)
        self._blobs.save_dataset(session_id, df, original=False)

        # Update session metadata.
        self._store.update_session(
            session_id,
            source_filename=path.name,
            row_count=len(df),
            col_count=len(df.columns),
        )

        self._invalidate_cache(session_id)
        self.data_loaded.emit(session_id)
        return df

    def load_dataset(self, session_id: str, *, original: bool = False) -> pd.DataFrame:
        return self._blobs.load_dataset(session_id, original=original)

    def has_dataset(self, session_id: str) -> bool:
        return self._blobs.dataset_exists(session_id)

    # ── descriptive statistics ───────────────────────────────

    def get_all_stats(self, session_id: str) -> list[dict[str, Any]]:
        """Compute (or return cached) column statistics for the active dataset."""
        if session_id in self._stats_cache:
            return self._stats_cache[session_id]
        df = self.load_dataset(session_id)
        stats = compute_all_stats(df)
        self._stats_cache[session_id] = stats
        self.stats_computed.emit(stats)
        return stats

    def get_column_stats(self, session_id: str, column: str) -> dict[str, Any]:
        df = self.load_dataset(session_id)
        return compute_column_stats(df[column])

    def _invalidate_cache(self, session_id: str) -> None:
        self._stats_cache.pop(session_id, None)

    # ── helpers ──────────────────────────────────────────────

    @staticmethod
    def _detect_delimiter(path: Path, encoding: str = "utf-8") -> str:
        """Sniff the delimiter from the first few lines of the file."""
        try:
            with open(path, "r", encoding=encoding) as f:
                sample = f.read(8192)
        except UnicodeDecodeError:
            return ","
        # Simple heuristic: count common delimiters in the sample.
        counts = {sep: sample.count(sep) for sep in [",", "\t", ";", "|"]}
        best = max(counts, key=counts.get)  # type: ignore[arg-type]
        return best if counts[best] > 0 else ","
