"""Seaborn wrappers for generating matplotlib Figures."""

from __future__ import annotations

from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Use the non-interactive Agg backend to avoid GUI thread issues
matplotlib.use("Agg")

# Apply the Biscay Blue theme globally to seaborn
sns.set_theme(
    style="whitegrid",
    palette=["#001857", "#1b2f6e", "#304382", "#dce1ff", "#757681"],
)

def create_histogram(df: pd.DataFrame, params: dict[str, Any]) -> matplotlib.figure.Figure:
    x = params["x"]
    hue = params.get("hue")
    bins = params.get("bins", "auto")
    
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.histplot(data=df, x=x, hue=hue, bins=bins, kde=True, ax=ax)
    ax.set_title(f"Histogram of {x}")
    fig.tight_layout()
    return fig

def create_boxplot(df: pd.DataFrame, params: dict[str, Any]) -> matplotlib.figure.Figure:
    y = params["y"]
    x = params.get("x")
    hue = params.get("hue")
    
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.boxplot(data=df, x=x, y=y, hue=hue, ax=ax)
    title = f"Boxplot of {y}" + (f" by {x}" if x else "")
    ax.set_title(title)
    fig.tight_layout()
    return fig

def create_scatterplot(df: pd.DataFrame, params: dict[str, Any]) -> matplotlib.figure.Figure:
    x = params["x"]
    y = params["y"]
    hue = params.get("hue")
    
    # Downsample large datasets to 50k points for scatter plots to prevent long rendering
    # and massive SVG files.
    if len(df) > 50000:
        df = df.sample(n=50000, random_state=42)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(data=df, x=x, y=y, hue=hue, ax=ax)
    ax.set_title(f"Scatter plot: {x} vs {y}")
    fig.tight_layout()
    return fig

def create_barplot(df: pd.DataFrame, params: dict[str, Any]) -> matplotlib.figure.Figure:
    x = params["x"]
    y = params["y"]
    hue = params.get("hue")
    
    fig, ax = plt.subplots(figsize=(8, 6))
    # For a standard bar plot in statforge, we default to mean estimator
    sns.barplot(data=df, x=x, y=y, hue=hue, ax=ax)
    ax.set_title(f"Bar plot of {y} by {x}")
    fig.tight_layout()
    return fig

def create_heatmap(df: pd.DataFrame, params: dict[str, Any]) -> matplotlib.figure.Figure:
    """Creates a correlation heatmap of all numeric columns."""
    fig, ax = plt.subplots(figsize=(10, 8))
    numeric_df = df.select_dtypes(include="number")
    corr = numeric_df.corr()
    
    sns.heatmap(
        corr, 
        annot=True, 
        cmap="coolwarm", 
        center=0, 
        vmin=-1, 
        vmax=1, 
        square=True, 
        fmt=".2f", 
        ax=ax
    )
    ax.set_title("Correlation Heatmap")
    fig.tight_layout()
    return fig

def create_pairplot(df: pd.DataFrame, params: dict[str, Any]) -> matplotlib.figure.Figure:
    """Creates a seaborn pairplot (returns a Figure)."""
    hue = params.get("hue")
    vars_list = params.get("vars") # subset of columns
    
    # Pairplots are even more expensive, limit to 20k points.
    if len(df) > 20000:
        df = df.sample(n=20000, random_state=42)
        
    g = sns.pairplot(df, hue=hue, vars=vars_list, corner=True)
    g.fig.suptitle("Pairwise Relationships", y=1.02)
    return g.fig


_PLOT_REGISTRY = {
    "histogram": create_histogram,
    "boxplot": create_boxplot,
    "scatter": create_scatterplot,
    "bar": create_barplot,
    "heatmap": create_heatmap,
    "pairplot": create_pairplot,
}

def generate_plot(df: pd.DataFrame, plot_type: str, params: dict[str, Any]) -> matplotlib.figure.Figure:
    func = _PLOT_REGISTRY.get(plot_type)
    if not func:
        raise ValueError(f"Unknown plot type: {plot_type}")
    
    # Generate the figure
    fig = func(df, params)
    return fig
