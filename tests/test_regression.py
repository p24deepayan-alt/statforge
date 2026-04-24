import pandas as pd
import pytest
from app.analysis.modeling import train_model
from app.util.errors import AnalysisError

def test_train_ols():
    df = pd.DataFrame({
        "X": [1, 2, 3, 4, 5],
        "Y": [2, 4, 5, 4, 5]
    })
    
    model, metrics = train_model(df, "ols", "Y", ["X"], {})
    assert model is not None
    assert "r2" in metrics
    assert "aic" in metrics

def test_train_missing_target():
    df = pd.DataFrame({"X": [1, 2]})
    with pytest.raises(AnalysisError):
        train_model(df, "ols", "Y", ["X"], {})
