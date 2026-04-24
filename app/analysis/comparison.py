"""Advanced model comparison logic."""

from __future__ import annotations

from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve, auc

from app.util.errors import AnalysisError

# Use non-interactive backend
matplotlib.use("Agg")

def compare_classifiers_roc(df: pd.DataFrame, models_data: list[tuple[str, Any, dict[str, Any]]]) -> matplotlib.figure.Figure:
    """
    Generates an overlaid ROC curve for binary classifiers.
    models_data is a list of (model_name, estimator, spec).
    """
    if not models_data:
        raise AnalysisError("No models provided for ROC comparison.")
        
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # We need a common target to plot ROC. Assume first model's target.
    target = models_data[0][2].get("target")
    if not target or target not in df.columns:
        raise AnalysisError(f"Target '{target}' missing from dataset.")
        
    y = df[target]
    
    # Convert string targets to binary for ROC if needed
    if y.dtype == object or str(y.dtype) == "category":
        classes = y.unique()
        if len(classes) != 2:
            raise AnalysisError("ROC curve requires a binary target variable.")
        # Map to 0 and 1
        pos_label = classes[1] # Arbitrarily pick second class as positive
        y_bin = (y == pos_label).astype(int)
    else:
        # Assume 0 and 1 already or continuous (which might fail)
        y_bin = y
        if len(np.unique(y_bin)) > 2:
             raise AnalysisError("ROC curve requires a binary target variable.")

    plotted = 0
    for name, estimator, spec in models_data:
        features = spec.get("features", [])
        if any(f not in df.columns for f in features):
            continue
            
        X = df[features]
        
        # Check if model has predict_proba
        if hasattr(estimator, "predict_proba"):
            try:
                y_probs = estimator.predict_proba(X)[:, 1]
                fpr, tpr, _ = roc_curve(y_bin, y_probs)
                roc_auc = auc(fpr, tpr)
                ax.plot(fpr, tpr, lw=2, label=f"{name} (AUC = {roc_auc:.3f})")
                plotted += 1
            except Exception:
                pass
                
    if plotted == 0:
        raise AnalysisError("None of the selected models support predict_proba for ROC curves.")
        
    ax.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--", label="Random Guess")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("Receiver Operating Characteristic (ROC)")
    ax.legend(loc="lower right")
    fig.tight_layout()
    
    return fig
