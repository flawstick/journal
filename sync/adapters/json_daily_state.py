"""JSON-backed per-day cache adapters."""

from __future__ import annotations

import datetime
import os
from typing import cast

from sync.constants import LOCK_DIR, TRAINING_STATE_DIR
from sync.contracts.state import DailyTrainingStateRow
from sync.ports.state import DailyTrainingStateStore
from sync.notes.locking import locked_path

from .json_cache_common import (
    atomic_write_json,
    load_json_or_none,
    schema_error,
)


def _validate_training_entry(
    raw: object,
    *,
    path: str,
    index: int,
) -> DailyTrainingStateRow:
    if not isinstance(raw, dict):
        raise schema_error(path, f"entries[{index}] must be an object")
    entry = cast(dict[str, object], raw)

    required_keys = {"start", "end", "time_raw", "activity", "duration", "interrupt"}
    if set(entry) != required_keys:
        raise schema_error(
            path, f"entries[{index}] must contain {sorted(required_keys)}"
        )

    start = entry.get("start")
    if start is not None and not isinstance(start, str):
        raise schema_error(path, f"entries[{index}].start must be a string or null")

    end = entry.get("end")
    if end is not None and not isinstance(end, str):
        raise schema_error(path, f"entries[{index}].end must be a string or null")

    time_raw = entry.get("time_raw")
    if not isinstance(time_raw, str):
        raise schema_error(path, f"entries[{index}].time_raw must be a string")

    activity = entry.get("activity")
    if not isinstance(activity, str):
        raise schema_error(path, f"entries[{index}].activity must be a string")

    duration = entry.get("duration")
    if not isinstance(duration, str):
        raise schema_error(path, f"entries[{index}].duration must be a string")

    interrupt_raw = entry.get("interrupt")
    interrupt: float | str
    if isinstance(interrupt_raw, (int, float)):
        interrupt = float(interrupt_raw)
    elif isinstance(interrupt_raw, str):
        interrupt = interrupt_raw
    else:
        raise schema_error(
            path,
            f"entries[{index}].interrupt must be numeric or a string",
        )

    return {
        "start": start,
        "end": end,
        "time_raw": time_raw,
        "activity": activity,
        "duration": duration,
        "interrupt": interrupt,
    }


def _validate_training_payload(
    raw: object,
    *,
    path: str,
    date_str: str,
) -> list[DailyTrainingStateRow]:
    if not isinstance(raw, dict):
        raise schema_error(path, "root payload must be an object")
    payload = cast(dict[str, object], raw)
    if set(payload) != {"date", "entries"}:
        raise schema_error(path, "root must contain exactly ['date', 'entries']")

    if payload.get("date") != date_str:
        raise schema_error(path, f"date must equal '{date_str}'")

    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise schema_error(path, "entries must be a list")

    typed_entries: list[DailyTrainingStateRow] = []
    for index, entry in enumerate(cast(list[object], entries)):
        typed_entries.append(_validate_training_entry(entry, path=path, index=index))

    return typed_entries


class JsonDailyTrainingStateStore(DailyTrainingStateStore):
    """Filesystem-backed per-day training state store."""

    def __init__(
        self,
        *,
        state_dir: str | None = None,
        lock_root: str | None = None,
    ) -> None:
        self.state_dir = state_dir or TRAINING_STATE_DIR
        self.lock_root = lock_root or LOCK_DIR

    def load_for_date(self, date_str: str) -> list[DailyTrainingStateRow]:
        path = os.path.join(self.state_dir, f"{date_str}.json")
        with locked_path(path, lock_root=self.lock_root):
            raw = load_json_or_none(path)
        if raw is None:
            return []
        return _validate_training_payload(raw, path=path, date_str=date_str)

    def save_for_date(
        self, date_str: str, entries: list[DailyTrainingStateRow]
    ) -> None:
        path = os.path.join(self.state_dir, f"{date_str}.json")
        with locked_path(path, lock_root=self.lock_root):
            atomic_write_json(path, {"date": date_str, "entries": entries})

    def prune(self, *, keep_days: int) -> None:
        if keep_days <= 0 or not os.path.isdir(self.state_dir):
            return
        cutoff = datetime.date.today() - datetime.timedelta(days=keep_days - 1)
        for name in os.listdir(self.state_dir):
            if not name.endswith(".json"):
                continue
            try:
                file_date = datetime.datetime.strptime(name[:-5], "%Y-%m-%d").date()
            except ValueError:
                continue
            if file_date < cutoff:
                try:
                    os.remove(os.path.join(self.state_dir, name))
                except OSError:
                    pass
