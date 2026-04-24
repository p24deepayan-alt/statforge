"""Machine learning modeling wrappers."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    silhouette_score,
)

from app.util.errors import AnalysisError


def train_ols(df: pd.DataFrame, target: str, features: list[str], params: dict[str, Any]) -> tuple[Any, dict[str, float]]:
    """Trains an Ordinary Least Squares (OLS) regression using statsmodels."""
    if target not in df.columns or any(f not in df.columns for f in features):
        raise AnalysisError("Target or features missing from dataset.")

    y = df[target]
    X = df[features]
    X = sm.add_constant(X)

    try:
        model = sm.OLS(y, X).fit()
        
        coef_table = []
        conf_int = model.conf_int()
        for i, var in enumerate(model.params.index):
            coef_table.append({
                "variable": str(var),
                "coef": round(float(model.params.iloc[i]), 4),
                "std_err": round(float(model.bse.iloc[i]), 4),
                "t": round(float(model.tvalues.iloc[i]), 4),
                "p": round(float(model.pvalues.iloc[i]), 4),
                "ci_low": round(float(conf_int.iloc[i, 0]), 4),
                "ci_high": round(float(conf_int.iloc[i, 1]), 4),
            })
            
        metrics = {
            "r2": float(model.rsquared),
            "adj_r2": float(model.rsquared_adj),
            "f_pvalue": float(model.f_pvalue),
            "aic": float(model.aic),
            "bic": float(model.bic),
            "coef_table": coef_table,
        }
        return model, metrics
    except Exception as e:
        raise AnalysisError(f"Failed to train OLS model: {e}") from e


def train_logistic(df: pd.DataFrame, target: str, features: list[str], params: dict[str, Any]) -> tuple[Any, dict[str, float]]:
    """Trains a Logistic Regression classifier using scikit-learn."""
    if target not in df.columns or any(f not in df.columns for f in features):
        raise AnalysisError("Target or features missing from dataset.")

    y = df[target]
    X = df[features]

    try:
        model = LogisticRegression(max_iter=1000)
        model.fit(X, y)
        y_pred = model.predict(X)
        
        metrics = {
            "accuracy": float(accuracy_score(y, y_pred)),
            "f1_score": float(f1_score(y, y_pred, average="weighted")),
        }
        return model, metrics
    except Exception as e:
        raise AnalysisError(f"Failed to train Logistic Regression: {e}") from e


def train_random_forest_regressor(df: pd.DataFrame, target: str, features: list[str], params: dict[str, Any]) -> tuple[Any, dict[str, float]]:
    """Trains a Random Forest Regressor using scikit-learn."""
    if target not in df.columns or any(f not in df.columns for f in features):
        raise AnalysisError("Target or features missing from dataset.")

    y = df[target]
    X = df[features]
    
    n_estimators = params.get("n_estimators", 100)
    max_depth = params.get("max_depth", None)

    try:
        model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
        model.fit(X, y)
        y_pred = model.predict(X)
        
        metrics = {
            "r2": float(r2_score(y, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y, y_pred))),
            "mae": float(mean_absolute_error(y, y_pred)),
        }
        return model, metrics
    except Exception as e:
        raise AnalysisError(f"Failed to train Random Forest Regressor: {e}") from e


def train_random_forest_classifier(df: pd.DataFrame, target: str, features: list[str], params: dict[str, Any]) -> tuple[Any, dict[str, float]]:
    """Trains a Random Forest Classifier using scikit-learn."""
    if target not in df.columns or any(f not in df.columns for f in features):
        raise AnalysisError("Target or features missing from dataset.")

    y = df[target]
    X = df[features]
    
    n_estimators = params.get("n_estimators", 100)
    max_depth = params.get("max_depth", None)

    try:
        model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
        model.fit(X, y)
        y_pred = model.predict(X)
        
        metrics = {
            "accuracy": float(accuracy_score(y, y_pred)),
            "f1_score": float(f1_score(y, y_pred, average="weighted")),
        }
        return model, metrics
    except Exception as e:
        raise AnalysisError(f"Failed to train Random Forest Classifier: {e}") from e


def train_kmeans(df: pd.DataFrame, target: str | None, features: list[str], params: dict[str, Any]) -> tuple[Any, dict[str, float]]:
    """Trains a K-Means clustering model. Target is ignored."""
    if any(f not in df.columns for f in features):
        raise AnalysisError("Features missing from dataset.")

    X = df[features]
    n_clusters = params.get("n_clusters", 3)

    try:
        model = KMeans(n_clusters=n_clusters, random_state=42)
        labels = model.fit_predict(X)
        
        metrics = {
            "inertia": float(model.inertia_),
        }
        
        # Silhouette score can be slow on very large datasets
        if len(X) < 10000:
            metrics["silhouette"] = float(silhouette_score(X, labels))
            
        return model, metrics
    except Exception as e:
        raise AnalysisError(f"Failed to train K-Means: {e}") from e


def stepwise_ols(
    df: pd.DataFrame, target: str, candidates: list[str], alpha: float = 0.05
) -> tuple[Any, dict[str, float], list[str]]:
    """Bidirectional stepwise OLS selection based on p-values.
    
    Returns (fitted_model, metrics_dict, selected_features).
    """
    if target not in df.columns:
        raise AnalysisError("Target column missing from dataset.")
    
    y = df[target]
    remaining = set(candidates)
    selected: list[str] = []
    
    changed = True
    while changed:
        changed = False
        
        # --- Forward step: find the best variable to add ---
        best_add = None
        best_p = 1.0
        for feat in remaining:
            trial = selected + [feat]
            X_trial = sm.add_constant(df[trial])
            try:
                model = sm.OLS(y, X_trial).fit()
                # p-value for the newly added feature
                p_val = model.pvalues[feat]
            except Exception:
                continue
                
            if p_val < best_p:
                best_p = p_val
                best_add = feat
                
        if best_add is not None and best_p < alpha:
            selected.append(best_add)
            remaining.remove(best_add)
            changed = True
            
        # --- Backward step: remove worst variable if it exceeds alpha ---
        if len(selected) > 0:
            X_current = sm.add_constant(df[selected])
            try:
                model = sm.OLS(y, X_current).fit()
                pvals = model.pvalues.drop("const", errors="ignore")
                worst_p = pvals.max()
                worst_feature = pvals.idxmax()
                
                if worst_p > alpha:
                    selected.remove(worst_feature)
                    remaining.add(worst_feature)
                    changed = True
            except Exception:
                pass

    if not selected:
        raise AnalysisError(f"Stepwise selection could not find any predictors significant at alpha={alpha}.")
    
    # Final fit
    model, metrics = train_ols(df, target, selected, {})
    return model, metrics, selected


_MODEL_REGISTRY = {
    "ols": train_ols,
    "logistic": train_logistic,
    "rf_regressor": train_random_forest_regressor,
    "rf_classifier": train_random_forest_classifier,
    "kmeans": train_kmeans,
}

def train_model(
    df: pd.DataFrame, model_type: str, target: str | None, features: list[str], params: dict[str, Any]
) -> tuple[Any, dict[str, float]]:
    """Dispatches model training based on type and returns (model_obj, metrics_dict)."""
    func = _MODEL_REGISTRY.get(model_type)
    if not func:
        raise AnalysisError(f"Unknown model type: {model_type}")
        
    return func(df, target, features, params)
