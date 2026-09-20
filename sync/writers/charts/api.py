"""Unified chart API."""

from __future__ import annotations

from .renderers.calendar_columns import render_training_calendar_columns
from .renderers.grouped_grid import (
    render_monthly_training_grid,
    render_weekly_training_grid,
)
from .renderers.vertical import render_vertical_bar
from .specs import (
    ChartSpec,
    MonthlyTrainingGridSpec,
    TrainingCalendarColumnsSpec,
    VerticalBarSpec,
    WeeklyTrainingGridSpec,
)


def render_chart(spec: ChartSpec) -> list[str]:
    """Render a chart and enclose its body in a Markdown fence."""
    if isinstance(spec, VerticalBarSpec):
        lines = render_vertical_bar(spec)
    elif isinstance(spec, MonthlyTrainingGridSpec):
        lines = render_monthly_training_grid(spec)
    elif isinstance(spec, WeeklyTrainingGridSpec):
        lines = render_weekly_training_grid(spec)
    elif isinstance(spec, TrainingCalendarColumnsSpec):
        lines = render_training_calendar_columns(spec)
    else:
        raise ValueError(f"Unsupported chart spec: {type(spec)!r}")
    return ["```", *lines, "```"] if lines else []
