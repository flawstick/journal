"""Service-level tests for period synchronization orchestration."""

from __future__ import annotations

import datetime

import pytest

from sync.application.period_sync_service import PeriodSyncService
from sync.contracts.media import MediaBundle
from sync.contracts.notes import NotePublication
from sync.contracts.metrics import DailyAggregate
from sync.dates import daterange
from sync.metrics import compute_period_metrics
from sync.periods.windows import (
    build_month_window,
    build_week_window,
    build_year_window,
)


class _StubNoteStore:
    def __init__(self) -> None:
        self._notes: dict[str, list[str]] = {}

    def read(self, path: str) -> list[str] | None:
        lines = self._notes.get(path)
        return lines[:] if lines is not None else None

    def read_or_create(self, path: str, _template_path: str) -> list[str]:
        lines = self._notes.get(path)
        if lines is None:
            lines = ["## Metrics", "---", "", "## Reflections", ""]
            self._notes[path] = lines
        return lines[:]

    def publish(
        self,
        path: str,
        lines: list[str],
        *,
        expected: list[str] | None,
    ) -> NotePublication:
        current = self.read(path)
        if current != expected:
            return NotePublication(
                status="conflict",
                lines=tuple(current) if current is not None else None,
            )
        return self.update(path, lambda _current: lines)

    def update(self, path, updater, *, template_path=None) -> NotePublication:
        _ = template_path
        current = self.read(path)
        base = current or ["## Metrics", "---", "", "## Reflections", ""]
        updated = updater(base)
        if updated == current:
            return NotePublication(status="unchanged", lines=tuple(updated))
        self._notes[path] = updated[:]
        return NotePublication(status="updated", lines=tuple(updated))


class _StubAggregateSource:
    def load_for_dates(self, dates: list[datetime.date]):
        return {day: {} for day in dates}


class _StubMediaSource:
    def __init__(self) -> None:
        self.calls: list[tuple[datetime.date, datetime.date]] = []

    def scan(self, start: datetime.date, end: datetime.date) -> MediaBundle:
        self.calls.append((start, end))
        return MediaBundle(items=())


def test_sync_week_writes_metrics_and_runs_cleanup(monkeypatch, tmp_path):
    note_store = _StubNoteStore()
    media_source = _StubMediaSource()
    service = PeriodSyncService(
        note_store=note_store,
        aggregate_source=_StubAggregateSource(),
        media_source=media_source,
    )

    day = datetime.date(2026, 2, 6)
    window = build_week_window(day)
    note_path = str(tmp_path / window.filename)

    base_dir = tmp_path / "journal"
    base_dir.mkdir()

    monkeypatch.setattr(
        "sync.application.period_sync_service.journal_path",
        lambda filename: str(base_dir / filename),
    )

    def _stub_build_weekly_metrics(*_a, **_kwargs):
        return ["### **SUMMARY**", "", "week"]

    monkeypatch.setattr(
        "sync.application.period_sync_service.build_weekly_metrics",
        _stub_build_weekly_metrics,
    )
    cleanup_calls: list[tuple[bool, str, object | None]] = []

    def _record_cleanup(*, enabled, previous_note_path, rerun):
        cleanup_calls.append((enabled, previous_note_path, rerun))
        return False

    monkeypatch.setattr(
        "sync.application.period_sync_service.maybe_cleanup_previous",
        _record_cleanup,
    )

    def _cleanup_runner() -> None:
        return None

    service.sync_week(
        window,
        note_path,
        cleanup_previous=True,
        cleanup_previous_runner=_cleanup_runner,
    )

    written = note_store.read(note_path)
    assert written is not None
    assert "week" in written
    assert cleanup_calls
    enabled, _prev_path, rerun = cleanup_calls[0]
    assert enabled is True
    assert callable(rerun)
    assert media_source.calls == [(window.start, window.end)]


def test_sync_year_writes_metrics(monkeypatch, tmp_path):
    note_store = _StubNoteStore()
    media_source = _StubMediaSource()
    service = PeriodSyncService(
        note_store=note_store,
        aggregate_source=_StubAggregateSource(),
        media_source=media_source,
    )

    window = build_year_window(2026, target_date=datetime.date(2026, 6, 1))
    note_path = str(tmp_path / window.filename)

    monkeypatch.setattr(
        "sync.application.period_sync_service.build_yearly_metrics",
        lambda *_a, **_kw: ["### **SUMMARY**", "", "year"],
    )
    service.sync_year(window, note_path)

    written = note_store.read(note_path)
    assert written is not None
    assert "year" in written
    assert media_source.calls == [(window.start, window.end)]


@pytest.mark.parametrize(
    ("period", "window", "prior_count"),
    [
        ("week", build_week_window(datetime.date(2026, 1, 1)), 4),
        ("month", build_month_window(datetime.date(2026, 1, 1)), 3),
        ("year", build_year_window(2026, target_date=datetime.date(2026, 6, 1)), 3),
    ],
)
def test_period_loads_each_day_once_and_preserves_comparison_windows(
    monkeypatch, tmp_path, period, window, prior_count
):
    earliest, _ = window.prior_bounds(prior_count)
    expected_dates = list(daterange(earliest, window.end))
    data = {
        day: DailyAggregate(study_minutes=float(index + 1))
        for index, day in enumerate(expected_dates)
        if index % 3 == 0
    }
    loads = []

    class Source:
        def load_for_dates(self, dates):
            loads.append(dates)
            return {day: data[day] for day in dates if day in data}

    def render(actual_window, current, previous, media, **kwargs):
        assert actual_window == window
        assert current == {
            day: value
            for day, value in data.items()
            if window.start <= day <= window.end
        }
        assert previous == {
            day: value
            for day, value in data.items()
            if window.previous_start <= day <= window.previous_end
        }
        expected_prior = [
            compute_period_metrics(list(daterange(*window.prior_bounds(offset))), data)
            for offset in range(prior_count, 0, -1)
        ]
        assert kwargs[f"prior_{period}_metrics"] == expected_prior
        return ["metrics"]

    builder = {"week": "weekly", "month": "monthly", "year": "yearly"}[period]
    monkeypatch.setattr(
        f"sync.application.period_sync_service.build_{builder}_metrics", render
    )
    service = PeriodSyncService(_StubNoteStore(), Source(), _StubMediaSource())
    note_path = str(tmp_path / window.filename)
    if period == "year":
        service.sync_year(window, note_path)
    else:
        getattr(service, f"sync_{period}")(window, note_path, cleanup_previous=False)
    assert loads == [expected_dates]
