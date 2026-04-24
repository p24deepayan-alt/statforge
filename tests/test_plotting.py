import pandas as pd
import matplotlib.figure
from app.analysis.plotting import generate_plot

def test_generate_histogram():
    df = pd.DataFrame({"X": [1, 2, 2, 3, 3, 3, 4, 4, 5]})
    fig = generate_plot(df, "histogram", {"x": "X"})
    assert isinstance(fig, matplotlib.figure.Figure)
    assert len(fig.axes) > 0

def test_generate_scatterplot():
    df = pd.DataFrame({"X": range(100), "Y": range(100)})
    fig = generate_plot(df, "scatter", {"x": "X", "y": "Y"})
    assert isinstance(fig, matplotlib.figure.Figure)
    assert len(fig.axes) > 0
