import numpy as np
import pandas as pd
from app.analysis.preprocessing import apply_pipeline

def test_preprocessing_pipeline():
    df = pd.DataFrame({
        "A": [1, 2, np.nan, 4],
        "B": ["cat", "dog", "cat", np.nan],
        "C": [10, 20, 30, 40]
    })
    
    pipeline = {
        "imputation": {
            "strategy_numeric": "mean",
            "strategy_categorical": "mode"
        },
        "encoding": {
            "strategy": "onehot",
            "columns": ["B"]
        },
        "scaling": {
            "strategy": "standard",
            "columns": ["C"]
        }
    }
    
    result = apply_pipeline(df, pipeline)
    
    # Check imputation
    assert not result["A"].isna().any()
    # Check encoding (onehot drops original, adds B_cat, B_dog)
    assert "B" not in result.columns
    assert "B_cat" in result.columns
    
    # Check scaling (C should have mean ~0, std ~1)
    assert abs(result["C"].mean()) < 1e-6
