from pathlib import Path
from uuid import uuid4

import pytest

from learning import lessons, storage


def test_lesson_metadata_never_replaces_teaching_headings(tmp_path: Path) -> None:
    session = str(uuid4())
    storage.update(tmp_path / "state/smm.json", 0, lambda _: {"title": "SMM"})
    path = lessons.publish(tmp_path, session, "# Linear maps\n\nText.")
    lessons.label(tmp_path, session, title="Singular systems", scope="smm")
    lessons.publish(tmp_path, session, "# Linear maps\n\nNext explanation.")
    assert "# Linear maps\n\nNext explanation." in path.read_text()
    assert '"title":"Singular systems"' in path.read_text()
    assert not (tmp_path / "index.md").exists()
    assert not (tmp_path / "courses").exists()
    before = path.read_text()
    with pytest.raises(ValueError, match="unknown lesson scope"):
        lessons.label(tmp_path, session, title="Maps", scope="unknown")
    assert path.read_text() == before
    path.write_text("# Personal note\n")
    with pytest.raises(ValueError, match="unowned lesson"):
        lessons.label(tmp_path, session, title="Do not overwrite")
    assert path.read_text() == "# Personal note\n"


def test_empty_projection_preserves_identity_without_creating_a_note(
    tmp_path: Path,
) -> None:
    session = str(uuid4())
    path = lessons.publish(tmp_path, session, "")
    assert not path.exists()
    lessons.publish(tmp_path, session, "## Linear maps\n\nPrior teaching.")
    lessons.publish(tmp_path, session, "")
    assert '"title":"Linear maps"' in path.read_text()
    assert "Prior teaching" not in path.read_text()
    storage.update(tmp_path / "state/smm.json", 0, lambda _: {"title": "SMM"})
    lessons.label(tmp_path, session, title="Named lesson", scope="smm")
    lessons.publish(tmp_path, session, "New teaching.")
    lessons.publish(tmp_path, session, "")
    assert '"title":"Named lesson","named":true,"scope":"smm"' in path.read_text()
    assert "New teaching" not in path.read_text()
    before = path.read_text()
    lessons.publish(tmp_path, session, "")
    assert path.read_text() == before
    path.write_text("# Personal note\n")
    with pytest.raises(ValueError, match="unowned lesson"):
        lessons.publish(tmp_path, session, "")
    assert path.read_text() == "# Personal note\n"


def test_lesson_publisher_updates_only_its_owned_note(tmp_path: Path) -> None:
    session_id = str(uuid4())
    path = lessons.publish(tmp_path, session_id, "# Lesson\n\nFirst turn.")
    assert path.read_text(encoding="utf-8").endswith("# Lesson\n\nFirst turn.\n")
    modified = path.stat().st_mtime_ns
    assert lessons.publish(tmp_path, session_id, "# Lesson\n\nFirst turn.") == path
    assert path.stat().st_mtime_ns == modified
    assert lessons.publish(tmp_path, session_id, "# Lesson\n\nNext turn.") == path
    assert path.read_text(encoding="utf-8").endswith("# Lesson\n\nNext turn.\n")
    user_note = "# My note\n\nKeep this content.\n"
    path.write_text(user_note, encoding="utf-8")
    with pytest.raises(ValueError, match="unowned lesson"):
        lessons.publish(tmp_path, session_id, "Replacement")
    assert path.read_text(encoding="utf-8") == user_note
