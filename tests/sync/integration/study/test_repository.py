from __future__ import annotations

import datetime
import sqlite3
from pathlib import Path

import pytest

from sync.study.core_data_time import datetime_to_core_data
from sync.study.repository import FlowSessionRepository


def _create_flow_db(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE ZSESSION (
            Z_PK INTEGER PRIMARY KEY,
            ZPHASE TEXT,
            ZDURATION REAL,
            ZSTARTEDAT REAL,
            ZCOMPLETEDAT REAL,
            ZTITLE TEXT
        );
        CREATE TABLE ZINTERRUPTION (
            ZSESSION INTEGER, ZSTARTEDAT REAL, ZFINISHEDAT REAL
        );
        """
    )
    connection.commit()
    connection.close()


def _repository(path: Path) -> FlowSessionRepository:
    def connect(readonly: bool) -> sqlite3.Connection:
        if readonly:
            return sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        return sqlite3.connect(path)

    return FlowSessionRepository(connection_factory=connect)


def _insert_session(
    path: Path,
    *,
    pk: int,
    phase: str,
    start: datetime.datetime,
    completed: datetime.datetime | None,
    title: str = "Study",
) -> None:
    connection = sqlite3.connect(path)
    connection.execute(
        """
        INSERT INTO ZSESSION
            (Z_PK, ZPHASE, ZDURATION, ZSTARTEDAT, ZCOMPLETEDAT, ZTITLE)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            pk,
            phase,
            60.0,
            datetime_to_core_data(start),
            datetime_to_core_data(completed),
            title,
        ),
    )
    connection.commit()
    connection.close()


def test_rename_sessions_updates_every_source_row(tmp_path: Path) -> None:
    db_path = tmp_path / "flow.sqlite"
    _create_flow_db(db_path)
    start = datetime.datetime(2026, 8, 10, 9, 0)
    end = start + datetime.timedelta(hours=1)
    _insert_session(db_path, pk=10, phase="flow", start=start, completed=end)
    _insert_session(db_path, pk=11, phase="flow", start=start, completed=end)

    _repository(db_path).rename_sessions([10, 11], "Architecture")

    connection = sqlite3.connect(db_path)
    titles = connection.execute(
        "SELECT Z_PK, ZTITLE FROM ZSESSION ORDER BY Z_PK"
    ).fetchall()
    connection.close()
    assert titles == [(10, "Architecture"), (11, "Architecture")]


def test_rename_sessions_rejects_a_missing_source_row(tmp_path: Path) -> None:
    db_path = tmp_path / "flow.sqlite"
    _create_flow_db(db_path)
    start = datetime.datetime(2026, 8, 10, 9, 0)
    end = start + datetime.timedelta(hours=1)
    _insert_session(db_path, pk=10, phase="flow", start=start, completed=end)

    with pytest.raises(LookupError, match="11"):
        _repository(db_path).rename_sessions([10, 11], "Architecture")

    connection = sqlite3.connect(db_path)
    titles = connection.execute("SELECT ZTITLE FROM ZSESSION").fetchall()
    connection.close()
    assert titles == [("Study",)]


def test_undo_session_deletes_all_source_rows_and_linked_breaks(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "flow.sqlite"
    _create_flow_db(db_path)
    start = datetime.datetime(2026, 8, 10, 13, 0)
    end = start + datetime.timedelta(hours=1)
    _insert_session(db_path, pk=10, phase="flow", start=start, completed=end)
    _insert_session(db_path, pk=11, phase="flow", start=start, completed=end)
    _insert_session(
        db_path,
        pk=20,
        phase="shortBreak",
        start=end + datetime.timedelta(minutes=1),
        completed=end + datetime.timedelta(minutes=16),
    )
    _insert_session(
        db_path,
        pk=21,
        phase="longBreak",
        start=end + datetime.timedelta(minutes=4),
        completed=end + datetime.timedelta(minutes=34),
    )
    _insert_session(
        db_path,
        pk=22,
        phase="shortBreak",
        start=end + datetime.timedelta(minutes=6),
        completed=end + datetime.timedelta(minutes=21),
    )
    connection = sqlite3.connect(db_path)
    connection.executemany(
        "INSERT INTO ZINTERRUPTION (ZSESSION) VALUES (?)",
        [(10,), (11,), (20,), (22,)],
    )
    connection.commit()
    connection.close()

    result = _repository(db_path).undo_session([10, 11], end, [20, 21])

    assert [item["pk"] for item in result.breaks] == [20, 21]
    assert result.deleted_interruptions == 3
    connection = sqlite3.connect(db_path)
    remaining_sessions = connection.execute(
        "SELECT Z_PK FROM ZSESSION ORDER BY Z_PK"
    ).fetchall()
    remaining_interruptions = connection.execute(
        "SELECT ZSESSION FROM ZINTERRUPTION ORDER BY ZSESSION"
    ).fetchall()
    connection.close()
    assert remaining_sessions == [(22,)]
    assert remaining_interruptions == [(22,)]


def test_undo_session_rolls_back_every_delete_on_failure(tmp_path: Path) -> None:
    db_path = tmp_path / "flow.sqlite"
    _create_flow_db(db_path)
    start = datetime.datetime(2026, 8, 10, 9, 0)
    end = start + datetime.timedelta(hours=1)
    _insert_session(db_path, pk=10, phase="flow", start=start, completed=end)
    _insert_session(db_path, pk=11, phase="flow", start=start, completed=end)
    connection = sqlite3.connect(db_path)
    connection.execute("INSERT INTO ZINTERRUPTION (ZSESSION) VALUES (10)")
    connection.execute(
        """
        CREATE TRIGGER reject_second_focus_delete
        BEFORE DELETE ON ZSESSION
        WHEN OLD.Z_PK = 11
        BEGIN
            SELECT RAISE(ABORT, 'blocked');
        END
        """
    )
    connection.commit()
    connection.close()

    with pytest.raises(sqlite3.IntegrityError, match="blocked"):
        _repository(db_path).undo_session([10, 11], end, [])

    connection = sqlite3.connect(db_path)
    session_pks = connection.execute(
        "SELECT Z_PK FROM ZSESSION ORDER BY Z_PK"
    ).fetchall()
    interruption_pks = connection.execute(
        "SELECT ZSESSION FROM ZINTERRUPTION"
    ).fetchall()
    connection.close()
    assert session_pks == [(10,), (11,)]
    assert interruption_pks == [(10,)]


def test_undo_session_rejects_a_missing_source_row_before_deleting(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "flow.sqlite"
    _create_flow_db(db_path)
    start = datetime.datetime(2026, 8, 10, 9, 0)
    end = start + datetime.timedelta(hours=1)
    _insert_session(db_path, pk=10, phase="flow", start=start, completed=end)
    connection = sqlite3.connect(db_path)
    connection.execute("INSERT INTO ZINTERRUPTION (ZSESSION) VALUES (10)")
    connection.commit()
    connection.close()

    with pytest.raises(LookupError, match="11"):
        _repository(db_path).undo_session([10, 11], end, [])

    connection = sqlite3.connect(db_path)
    session_pks = connection.execute("SELECT Z_PK FROM ZSESSION").fetchall()
    interruption_pks = connection.execute(
        "SELECT ZSESSION FROM ZINTERRUPTION"
    ).fetchall()
    connection.close()
    assert session_pks == [(10,)]
    assert interruption_pks == [(10,)]


@pytest.mark.parametrize("session_count", [3, 1001])
def test_load_day_aggregates_interruptions_in_batches(
    tmp_path: Path, session_count: int
) -> None:
    db_path = tmp_path / "flow.sqlite"
    _create_flow_db(db_path)
    start = datetime.datetime(2026, 8, 10, 9)
    statements: list[str] = []
    connection = sqlite3.connect(db_path)
    connection.executemany(
        """
        INSERT INTO ZSESSION
            (Z_PK, ZPHASE, ZDURATION, ZSTARTEDAT, ZCOMPLETEDAT, ZTITLE)
        VALUES (?, 'flow', 60, ?, ?, 'Study')
        """,
        [
            (pk, datetime_to_core_data(start), datetime_to_core_data(start) + 3600)
            for pk in range(1, session_count + 1)
        ],
    )
    connection.executemany(
        "INSERT INTO ZINTERRUPTION VALUES (?, ?, ?)",
        [(1, 100, 130), (1, 200, None), (1, 300, 340), (2, 400, None)],
    )
    connection.commit()
    connection.close()

    def connect(readonly: bool) -> sqlite3.Connection:
        connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        connection.set_trace_callback(statements.append)
        return connection

    result = FlowSessionRepository(connection_factory=connect).load_day_sessions(
        start.date(), now=start + datetime.timedelta(hours=1)
    )
    assert result.interruption_totals == {
        **dict.fromkeys(range(1, session_count + 1), (0, 0.0)),
        1: (3, 70.0),
        2: (1, 0.0),
    }
    interruption_queries = [query for query in statements if "ZINTERRUPTION" in query]
    assert len(interruption_queries) <= 2
