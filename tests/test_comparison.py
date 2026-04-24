import pandas as pd
from app.analysis.comparison import compare_classifiers_roc
from app.analysis.modeling import train_model

def test_compare_classifiers_roc():
    df = pd.DataFrame({
        "X1": [1, 2, 3, 4, 5, 6, 7, 8],
        "X2": [8, 7, 6, 5, 4, 3, 2, 1],
        "Y": [0, 0, 0, 0, 1, 1, 1, 1]
    })
    
    m1, _ = train_model(df, "logistic", "Y", ["X1"], {})
    m2, _ = train_model(df, "rf_classifier", "Y", ["X2"], {})
    
    models = {
        "m1": m1,
        "m2": m2
    }
    
    spec, fig = compare_classifiers_roc(models, df, "Y")
    
    assert fig is not None
    assert "metrics" in spec
    assert "table" in spec["metrics"]
    assert len(spec["metrics"]["table"]) == 2
