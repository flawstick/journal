from __future__ import annotations

from sync.writers.tables import (
    SimpleGridTableSpec,
    SummaryMetricsTableSpec,
    render_table,
)


def test_simple_grid_table_renders_headers_and_rows():
    assert render_table(
        SimpleGridTableSpec(
            headers=("A", "B"),
            rows=(("one", "two"),),
        )
    ) == [
        "| A | B |",
        "| ---- | ---- |",
        "| one | two |",
    ]


def test_summary_table_omits_change_column():
    lines = render_table(
        SummaryMetricsTableSpec(
            current_metrics={
                "study_total_minutes": 420.0,
                "sleep_avg_minutes": 480.0,
                "workout_count": 1,
                "stretch_count": 3,
                "days_up_to_today": 7,
                "total_days": 7,
            },
            previous_metrics={
                "study_total_minutes": 210.0,
                "sleep_avg_minutes": 420.0,
                "workout_count": 1,
                "stretch_count": 2,
                "days_up_to_today": 7,
                "total_days": 7,
            },
            current_label="CURRENT",
            previous_label="PREVIOUS",
        )
    )

    assert lines[2] == "| METRIC | CURRENT | PREVIOUS |"
    assert any(line.startswith("| **STUDY** |") for line in lines)
    assert "| **SLEEP** | `8h00m` | `7h00m` |" in lines


def test_summary_table_ma_column_only_adds_moving_average():
    lines = render_table(
        SummaryMetricsTableSpec(
            current_metrics={
                "study_total_minutes": 420.0,
                "sleep_avg_minutes": 480.0,
                "workout_count": 1,
                "stretch_count": 3,
                "days_up_to_today": 7,
                "total_days": 7,
            },
            previous_metrics={
                "study_total_minutes": 210.0,
                "sleep_avg_minutes": 420.0,
                "workout_count": 1,
                "stretch_count": 2,
                "days_up_to_today": 7,
                "total_days": 7,
            },
            current_label="CURRENT",
            previous_label="PREVIOUS",
            ma_label="4-WEEK",
            ma_metrics={
                "study_avg_minutes": 60.0,
                "sleep_avg_minutes": 450.0,
                "workout_avg": 1.0,
                "stretch_avg": 2.0,
            },
        )
    )

    assert lines[2] == "| METRIC | CURRENT | PREVIOUS | 4-WEEK |"
    assert "| **SLEEP** | `8h00m` | `7h00m` | `7h30m` |" in lines


def test_summary_keeps_zero_values_and_full_period_denominators():
    lines = render_table(
        SummaryMetricsTableSpec(
            current_metrics={
                "study_total_minutes": 0.0,
                "sleep_avg_minutes": 0.0,
                "workout_count": 0,
                "stretch_count": 0,
                "days_up_to_today": 0,
                "total_days": 31,
            },
            previous_metrics={
                "study_total_minutes": 120.0,
                "sleep_avg_minutes": None,
                "workout_count": 1,
                "stretch_count": 0,
                "days_up_to_today": 2,
                "total_days": 30,
            },
            current_label="CURRENT",
            previous_label="PREVIOUS",
            ma_label="4-MONTH",
            ma_metrics={
                "study_avg_minutes": 0.0,
                "sleep_avg_minutes": None,
                "workout_avg": 0.0,
                "stretch_avg": None,
            },
            ma_training_unit="30",
        )
    )

    assert "| **STUDY** | `0h00m/day` | `1h00m/day` | `0h00m/day` |" in lines
    assert "| **SLEEP** | `0h00m` | `—` | `—` |" in lines
    assert "| **WORKOUT** | `00/31` | `01/30` | `0.0/30` |" in lines
    assert "| **STRETCH** | `00/31` | `00/30` | `—` |" in lines
