import pandas as pd
from app.analysis.modeling import train_model

def test_train_logistic():
    df = pd.DataFrame({
        "X1": [1, 2, 3, 4, 5, 6],
        "X2": [6, 5, 4, 3, 2, 1],
        "Y": [0, 0, 0, 1, 1, 1]
    })
    
    model, metrics = train_model(df, "logistic", "Y", ["X1", "X2"], {})
    assert model is not None
    assert "accuracy" in metrics
    assert "f1_score" in metrics
