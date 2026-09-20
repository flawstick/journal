"""Unified markdown table API."""

from __future__ import annotations

from .renderers.simple_grid import render_simple_grid
from .renderers.summary_metrics import render_summary_metrics
from .specs import SimpleGridTableSpec, SummaryMetricsTableSpec, TableSpec


def render_table(spec: TableSpec) -> list[str]:
    """Render a Markdown table from its typed specification."""
    if isinstance(spec, SimpleGridTableSpec):
        return render_simple_grid(spec)
    if isinstance(spec, SummaryMetricsTableSpec):
        return render_summary_metrics(spec)
    raise ValueError(f"Unsupported table spec: {type(spec)!r}")
