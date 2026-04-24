import numpy as np
import pandas as pd
from app.analysis.descriptive import compute_all_stats, compute_column_stats

def test_compute_column_stats_numeric():
    series = pd.Series([1, 2, 3, 4, 5, np.nan])
    stats = compute_column_stats(series)
    
    assert stats["name"] == series.name
    assert stats["is_numeric"] is True
    assert stats["count"] == 5
    assert stats["missing"] == 1
    assert stats["mean"] == 3.0
    assert stats["min"] == 1.0
    assert stats["max"] == 5.0

def test_compute_column_stats_categorical():
    series = pd.Series(["apple", "banana", "apple", "orange", np.nan])
    stats = compute_column_stats(series)
    
    assert stats["is_numeric"] is False
    assert stats["count"] == 4
    assert stats["missing"] == 1
    assert stats["unique"] == 3
    assert stats["mode"] == "apple"

def test_compute_all_stats():
    df = pd.DataFrame({
        "A": [1, 2, 3],
        "B": ["x", "y", "x"]
    })
    
    stats = compute_all_stats(df)
    assert len(stats) == 2
    assert stats[0]["name"] == "A"
    assert stats[0]["is_numeric"] is True
    
    assert stats[1]["name"] == "B"
    assert stats[1]["is_numeric"] is False
    assert stats[1]["unique"] == 2
