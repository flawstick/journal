"""Owned live lesson notes with stable presentation titles."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any
from uuid import UUID

from learning import storage
from learning.markdown import obsidian_math

_META = "<!-- learning-lesson:"


def _title(value: str) -> str:
    if not value.strip() or "\n" in value or "\r" in value:
        raise ValueError("lesson title must be nonempty and on one line")
    return value.strip()


def _metadata(text: str) -> dict[str, Any]:
    for line in text.splitlines()[1:2]:
        if line.startswith(_META) and line.endswith(" -->"):
            data = json.loads(line[len(_META) : -4])
            if (
                not isinstance(data, dict)
                or not isinstance(data.get("title"), str)
                or (
                    "scope" in data
                    and (
                        not isinstance(data["scope"], str)
                        or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", data["scope"])
                    )
                )
            ):
                raise ValueError("invalid lesson metadata")
            data["title"] = _title(data["title"])
            return data
    return {}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _write(path: Path, text: str) -> None:
    if _read(path) != text:
        storage.publish_text(path, text)


def _change(
    root: Path, session_id: str, text: str | None, title: str | None, scope: str | None
) -> Path:
    if str(UUID(session_id)) != session_id:
        raise ValueError("session ID must be a canonical lowercase UUID")
    if scope is not None:
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", scope):
            raise ValueError("invalid lesson scope")
        if not (root / "state" / f"{scope}.json").is_file():
            raise ValueError(f"unknown lesson scope: {scope}")
    if title is not None:
        title = _title(title)
    path = root / "sessions" / f"{session_id}.md"
    marker = f"<!-- learning-session:{session_id} -->"
    # Serialise label changes and Pi publication of the same owned note.
    with storage.lock(root / ".lessons.lock"):
        existing = _read(path)
        if path.exists() and existing.partition("\n")[0] != marker:
            raise ValueError(f"refusing to overwrite an unowned lesson: {path}")
        if text is not None and not text.strip() and not existing:
            return path.resolve()
        if text is None and not existing:
            raise ValueError(f"lesson does not exist: {path}")
        old = _metadata(existing)
        data = dict(old)
        if title is not None:
            data.update(title=title, named=True)
        if scope is not None:
            data["scope"] = scope
        body = (
            text
            if text is not None
            else "\n".join(
                line
                for line in existing.splitlines()
                if line != marker and not line.startswith(_META)
            ).lstrip("\n")
        )
        heading = re.match(r"^#{1,6} +([^\n]+?)(?: +#+)?(?:\n|$)", body)
        if "title" not in data or (not data.get("named") and body.strip()):
            data["title"] = _title(heading[1]) if heading else "Study session"
        body = obsidian_math(body)
        encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        encoded = encoded.replace("<", "\\u003c").replace(">", "\\u003e")
        content = f"{marker}\n{_META}{encoded} -->\n\n{body.rstrip()}\n"
        _write(path, content)
    return path.resolve()


def publish(root: Path, session_id: str, text: str) -> Path:
    """Publish teaching; an empty branch clears only an existing owned lesson."""
    return _change(root, session_id, text, None, None)


def label(root: Path, session_id: str, *, title: str, scope: str | None = None) -> Path:
    """Name an existing lesson and optionally associate its established course."""
    return _change(root, session_id, None, title, scope)
