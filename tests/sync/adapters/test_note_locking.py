from __future__ import annotations

import fcntl
import hashlib
import os
from pathlib import Path

import pytest

from sync.notes.locking import locked_path


def test_old_lock_file_still_excludes_another_writer(tmp_path: Path) -> None:
    target = str(tmp_path / "note.md")
    lock_root = tmp_path / "locks"
    digest = hashlib.sha1(os.path.abspath(target).encode()).hexdigest()
    lock_file = lock_root / digest[:2] / f"{digest}.lock"
    lock_file.parent.mkdir(parents=True)
    with lock_file.open("w") as holder:
        fcntl.flock(holder, fcntl.LOCK_EX)
        os.utime(lock_file, (0, 0))
        with pytest.raises(TimeoutError):
            with locked_path(target, lock_root=str(lock_root), timeout=0):
                pytest.fail("A second writer acquired the held lock")

    with locked_path(target, lock_root=str(lock_root), timeout=0):
        assert lock_file.exists()
