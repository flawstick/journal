"""
File-lock utilities for note read/write synchronization.
"""

from __future__ import annotations

import fcntl
import hashlib
import os
import time
from collections.abc import Iterator
from contextlib import contextmanager


def _lockfile_for(path: str, lock_root: str) -> str:
    """Return path to advisory lockfile for a given lock root and target path."""
    digest = hashlib.sha1(os.path.abspath(path).encode()).hexdigest()
    shard = digest[:2]
    lock_dir = os.path.join(lock_root, shard)
    os.makedirs(lock_dir, exist_ok=True)
    return os.path.join(lock_dir, f"{digest}.lock")


@contextmanager
def locked_path(
    path: str,
    *,
    lock_root: str,
    timeout: float = 2.0,
    poll: float = 0.1,
) -> Iterator[None]:
    """Serialize access using a stable lock file; time out after `timeout` seconds."""
    lock_path = _lockfile_for(path, lock_root)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Could not lock {path} within {timeout}s.")
                time.sleep(poll)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
