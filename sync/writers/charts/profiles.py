"""Chart profile registry for the unified chart API."""

from __future__ import annotations

from .specs import (
    AnchorRef,
    ColumnTrack,
    HAnchor,
    VerticalBarProfile,
)


WEEKLY_7DAY_CHART = VerticalBarProfile(
    height=10,
    y_max=10,
    track=ColumnTrack(
        column_width=8,
        bar_width=5,
        bar_left_gutter=1,
        x_label_prefix="   ",
        delta_label_prefix="   ",
        axis_trim=2,
    ),
    value_anchor_ref=AnchorRef.COLUMN,
    value_anchor_h=HAnchor.CENTER,
    delta_anchor_ref=AnchorRef.LABEL,
    delta_anchor_h=HAnchor.CENTER,
)

MONTHLY_WEEK_STUDY = VerticalBarProfile(
    height=10,
    y_max=40,
    track=ColumnTrack(
        column_width=12,
        bar_width=6,
        bar_left_gutter=2,
        x_label_prefix=" ",
        delta_label_prefix=" ",
        axis_trim=2,
    ),
    value_anchor_ref=AnchorRef.BAR,
    value_anchor_h=HAnchor.START,
    delta_anchor_ref=AnchorRef.BAR,
    delta_anchor_h=HAnchor.CENTER,
)

MONTHLY_WEEK_METRIC = VerticalBarProfile(
    height=10,
    y_max=10,
    track=ColumnTrack(
        column_width=12,
        bar_width=5,
        bar_left_gutter=2,
        x_label_prefix=" ",
        delta_label_prefix=" ",
        axis_trim=2,
    ),
    value_anchor_ref=AnchorRef.BAR,
    value_anchor_h=HAnchor.START,
    delta_anchor_ref=AnchorRef.LABEL,
    delta_anchor_h=HAnchor.CENTER,
)

YEARLY_4QTR_STUDY = VerticalBarProfile(
    height=12,
    y_max=720,
    track=ColumnTrack(
        column_width=11,
        bar_width=7,
        bar_left_gutter=2,
        x_label_prefix="    ",
        delta_label_prefix="   ",
        axis_trim=2,
    ),
    value_anchor_ref=AnchorRef.BAR,
    value_anchor_h=HAnchor.START,
    delta_anchor_ref=AnchorRef.COLUMN,
    delta_anchor_h=HAnchor.START,
)

YEARLY_4QTR_METRIC = VerticalBarProfile(
    height=10,
    y_max=10,
    track=ColumnTrack(
        column_width=11,
        bar_width=5,
        bar_left_gutter=2,
        x_label_prefix="    ",
        delta_label_prefix="    ",
        axis_trim=4,
    ),
    value_anchor_ref=AnchorRef.BAR,
    value_anchor_h=HAnchor.START,
    delta_anchor_ref=AnchorRef.COLUMN,
    delta_anchor_h=HAnchor.START,
)
