"""Preprocessing pipeline operations.

Functions here take a DataFrame and parameters, returning a mutated DataFrame.
They are pure functions designed to be re-run sequentially from the original
dataset to reconstruct the working dataset upon undo.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from app.util.errors import PreprocessingError


def apply_drop_column(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    col = params["column"]
    if col not in df.columns:
        raise PreprocessingError(f"Column '{col}' not found.")
    return df.drop(columns=[col])


def apply_rename_column(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    old_name = params["old_name"]
    new_name = params["new_name"]
    if old_name not in df.columns:
        raise PreprocessingError(f"Column '{old_name}' not found.")
    return df.rename(columns={old_name: new_name})


def apply_drop_na(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    subset = params.get("subset")  # list of columns, or None for all
    return df.dropna(subset=subset)


def apply_impute(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    col = params["column"]
    strategy = params["strategy"]  # mean, median, mode, constant
    fill_value = params.get("fill_value")

    if col not in df.columns:
        raise PreprocessingError(f"Column '{col}' not found.")

    if strategy == "mean":
        val = df[col].mean()
    elif strategy == "median":
        val = df[col].median()
    elif strategy == "mode":
        mode_s = df[col].mode()
        val = mode_s.iloc[0] if len(mode_s) > 0 else None
    elif strategy == "constant":
        val = fill_value
    else:
        raise PreprocessingError(f"Unknown impute strategy: {strategy}")

    if val is None or pd.isna(val):
        raise PreprocessingError(f"Cannot impute {strategy} on column '{col}' (all NaNs?).")

    df[col] = df[col].fillna(val)
    return df


def apply_scale(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    col = params["column"]
    method = params["method"]  # standard, minmax

    if col not in df.columns:
        raise PreprocessingError(f"Column '{col}' not found.")

    # Need 2D array for sklearn
    data = df[[col]].values

    if method == "standard":
        scaler = StandardScaler()
    elif method == "minmax":
        scaler = MinMaxScaler()
    else:
        raise PreprocessingError(f"Unknown scaling method: {method}")

    df[col] = scaler.fit_transform(data)
    return df


def apply_encode(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    col = params["column"]
    method = params["method"]  # onehot, label

    if col not in df.columns:
        raise PreprocessingError(f"Column '{col}' not found.")

    if method == "label":
        df[col] = df[col].astype("category").cat.codes
    elif method == "onehot":
        df = pd.get_dummies(df, columns=[col], prefix=col, drop_first=False)
    else:
        raise PreprocessingError(f"Unknown encoding method: {method}")

    return df


# Registry mapping op names to functions
_OPS = {
    "drop_column": apply_drop_column,
    "rename_column": apply_rename_column,
    "drop_na": apply_drop_na,
    "impute": apply_impute,
    "scale": apply_scale,
    "encode": apply_encode,
}


def apply_operation(df: pd.DataFrame, op: str, params: dict[str, Any]) -> pd.DataFrame:
    """Apply a registered preprocessing operation to a DataFrame."""
    func = _OPS.get(op)
    if not func:
        raise PreprocessingError(f"Unknown preprocessing operation: {op}")
    # Always operate on a copy to avoid SettingWithCopyWarning issues
    df = df.copy()
    return func(df, params)
