"""Descriptive statistics computation.

Pure-Python module — no UI imports.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def compute_column_stats(series: pd.Series) -> dict[str, Any]:  # type: ignore[type-arg]
    """Compute summary statistics for a single column.

    Returns a dict suitable for display in the Descriptive Statistics panel
    and for serialisation as a ``column_summary`` artifact.
    """
    stats: dict[str, Any] = {
        "name": series.name,
        "dtype": str(series.dtype),
        "count": int(len(series)),
        "missing": int(series.isna().sum()),
        "missing_pct": round(float(series.isna().mean()) * 100, 2),
        "unique": int(series.nunique()),
    }

    if pd.api.types.is_numeric_dtype(series):
        clean = series.dropna()
        stats["is_numeric"] = True
        stats["mean"] = _safe_round(clean.mean())
        stats["median"] = _safe_round(clean.median())
        stats["std"] = _safe_round(clean.std())
        stats["min"] = _safe_round(clean.min())
        stats["max"] = _safe_round(clean.max())
        stats["q1"] = _safe_round(clean.quantile(0.25))
        stats["q3"] = _safe_round(clean.quantile(0.75))
    else:
        stats["is_numeric"] = False
        mode_result = series.mode()
        if len(mode_result) > 0:
            mode_val = mode_result.iloc[0]
            mode_count = int((series == mode_val).sum())
            mode_pct = round(mode_count / max(len(series), 1) * 100, 1)
            stats["mode"] = str(mode_val)
            stats["mode_pct"] = mode_pct
        else:
            stats["mode"] = None
            stats["mode_pct"] = 0.0

    return stats


def compute_all_stats(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Compute summary statistics for every column in a DataFrame."""
    return [compute_column_stats(df[col]) for col in df.columns]


def _safe_round(val: Any, decimals: int = 4) -> float | None:
    """Round a numeric value, returning None for non-finite values."""
    if val is None or (isinstance(val, float) and not np.isfinite(val)):
        return None
    return round(float(val), decimals)
