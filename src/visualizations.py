"""
Visualization functions for clinical trial analytics.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from src.config import COLOR_PALETTE, PLOTLY_TEMPLATE


def plot_trials_by_therapeutic_area(df: pd.DataFrame) -> go.Figure:
    """Bar chart of trials grouped by therapeutic area."""
    area_counts = df["therapeutic_area"].value_counts().head(10)
    
    fig = go.Figure(data=[
        go.Bar(
            x=area_counts.index,
            y=area_counts.values,
            marker_color=COLOR_PALETTE["primary"],
            text=area_counts.values,
            textposition="auto"
        )
    ])
    
    fig.update_layout(
        title="Clinical Trials by Therapeutic Area",
        xaxis_title="Therapeutic Area",
        yaxis_title="Number of Trials",
        template=PLOTLY_TEMPLATE,
        height=400,
        showlegend=False
    )
    
    return fig


def plot_trial_growth_by_year(df: pd.DataFrame) -> go.Figure:
    """Line chart showing trial growth over years."""
    df_copy = df.copy()
    df_copy["start_year"] = pd.to_datetime(df_copy["start_date"]).dt.year
    yearly_growth = df_copy.groupby("start_year").size().reset_index(name="count")
    
    fig = go.Figure(data=[
        go.Scatter(
            x=yearly_growth["start_year"],
            y=yearly_growth["count"],
            mode="lines+markers",
            line=dict(color=COLOR_PALETTE["secondary"], width=3),
            marker=dict(size=8),
            fill="tozeroy"
        )
    ])
    
    fig.update_layout(
        title="Clinical Trial Initiation Trend",
        xaxis_title="Year",
        yaxis_title="Number of Trials Started",
        template=PLOTLY_TEMPLATE,
        height=400,
        showlegend=False
    )
    
    return fig


def plot_top_sponsors(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Horizontal bar chart of top sponsors by trial count."""
    sponsor_counts = df["sponsor"].value_counts().head(top_n)
    
    fig = go.Figure(data=[
        go.Bar(
            x=sponsor_counts.values,
            y=sponsor_counts.index,
            orientation="h",
            marker_color=COLOR_PALETTE["success"],
            text=sponsor_counts.values,
            textposition="auto"
        )
    ])
    
    fig.update_layout(
        title=f"Top {top_n} Sponsors by Trial Count",
        xaxis_title="Number of Trials",
        yaxis_title="Sponsor",
        template=PLOTLY_TEMPLATE,
        height=400,
        showlegend=False
    )
    
    return fig


def plot_phase_distribution(df: pd.DataFrame) -> go.Figure:
    """Pie chart of trial distribution by phase."""
    phase_counts = df["phase"].value_counts()
    
    fig = go.Figure(data=[
        go.Pie(
            labels=phase_counts.index,
            values=phase_counts.values,
            hole=0.3
        )
    ])
    
    fig.update_layout(
        title="Trial Distribution by Phase",
        template=PLOTLY_TEMPLATE,
        height=400
    )
    
    return fig


def plot_recruitment_status(df: pd.DataFrame) -> go.Figure:
    """Donut chart of recruitment status distribution."""
    status_counts = df["recruitment_status"].value_counts()
    
    fig = go.Figure(data=[
        go.Pie(
            labels=status_counts.index,
            values=status_counts.values,
            hole=0.4,
            textinfo="label+percent"
        )
    ])
    
    fig.update_layout(
        title="Trials by Recruitment Status",
        template=PLOTLY_TEMPLATE,
        height=400
    )
    
    return fig


def plot_geographic_distribution(df: pd.DataFrame, top_n: int = 8) -> go.Figure:
    """Bar chart of trials by state."""
    state_counts = df["state"].value_counts().head(top_n)
    
    fig = go.Figure(data=[
        go.Bar(
            x=state_counts.index,
            y=state_counts.values,
            marker_color=COLOR_PALETTE["warning"],
            text=state_counts.values,
            textposition="auto"
        )
    ])
    
    fig.update_layout(
        title=f"Top {top_n} States by Trial Count",
        xaxis_title="State",
        yaxis_title="Number of Trials",
        template=PLOTLY_TEMPLATE,
        height=400,
        showlegend=False
    )
    
    return fig


def plot_sponsor_by_therapeutic_area(df: pd.DataFrame) -> go.Figure:
    """Stacked bar chart: therapeutic areas by top sponsors."""
    top_sponsors = df["sponsor"].value_counts().head(8).index
    df_filtered = df[df["sponsor"].isin(top_sponsors)]
    
    crosstab = pd.crosstab(df_filtered["sponsor"], df_filtered["therapeutic_area"])
    
    fig = go.Figure()
    
    for area in crosstab.columns:
        fig.add_trace(go.Bar(
            x=crosstab.index,
            y=crosstab[area],
            name=area
        ))
    
    fig.update_layout(
        title="Therapeutic Areas Covered by Top Sponsors",
        xaxis_title="Sponsor",
        yaxis_title="Number of Trials",
        barmode="stack",
        template=PLOTLY_TEMPLATE,
        height=400
    )
    
    return fig


def plot_enrollment_by_phase(df: pd.DataFrame) -> go.Figure:
    """Box plot of enrollment numbers by trial phase."""
    fig = px.box(
        df,
        x="phase",
        y="enrollment",
        color="phase",
        title="Trial Enrollment Distribution by Phase",
        labels={"phase": "Trial Phase", "enrollment": "Enrollment Size"},
        template=PLOTLY_TEMPLATE
    )
    
    fig.update_layout(height=400, showlegend=False)
    
    return fig
