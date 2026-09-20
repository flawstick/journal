import json
from pathlib import Path
from typing import Any

import pytest

from learning import preferences, storage


def _scope(root: Path, name: str = "course") -> dict[str, Any]:
    directory = root / "state"
    directory.mkdir(exist_ok=True)
    (directory / f"{name}.json").write_text(
        json.dumps(
            {
                "revision": 1,
                "topics": {
                    "systems": {
                        "concepts": ["linear-systems"],
                        "domains": ["mathematics"],
                    },
                    "other": {},
                },
            }
        ),
        encoding="utf-8",
    )
    return storage.load(directory / f"{name}.json")


def _rule(
    when: dict[str, str], instruction: str, origin: str = "explicit"
) -> dict[str, Any]:
    return {
        "when": when,
        "values": {"pace": {"instruction": instruction, "origin": origin}},
    }


def test_context_keeps_overlapping_origins_and_matches_topic_labels(
    tmp_path: Path,
) -> None:
    state = _scope(tmp_path)
    another_state = _scope(tmp_path, "another")
    preferences.save(
        tmp_path,
        0,
        {
            "rules": [
                _rule({}, "Global"),
                _rule({"scope": "course"}, "Course"),
                _rule({"scope": "course", "topic": "systems"}, "Topic", "inferred"),
                _rule({"concept": "linear-systems"}, "Shared concept"),
                _rule({"domain": "mathematics", "activity": "proof"}, "Proof"),
                _rule({"scope": "another"}, "Other course"),
                _rule({"activity": "coding"}, "Code"),
            ]
        },
    )
    selected = preferences.context(
        tmp_path, "course", topics=["systems"], activity="proof", state=state
    )
    values = [rule["values"]["pace"] for rule in selected["rules"]]
    assert {value["instruction"] for value in values} == {
        "Global",
        "Course",
        "Topic",
        "Shared concept",
        "Proof",
    }
    assert next(value for value in values if value["instruction"] == "Topic") == {
        "instruction": "Topic",
        "origin": "inferred",
    }
    assert selected["revision"] == 1
    assert len(preferences.context(tmp_path)["rules"]) == 1
    assert len(preferences.context(tmp_path, "course")["rules"]) == 2
    other = preferences.context(
        tmp_path, "another", topics=["systems"], state=another_state
    )
    assert {rule["values"]["pace"]["instruction"] for rule in other["rules"]} == {
        "Global",
        "Other course",
        "Shared concept",
    }
    assert preferences.context(tmp_path, "course", dimension="missing")["rules"] == []
    assert len(preferences.inspect(tmp_path, "pace")["rules"]) == 7


def test_replacements_preserve_other_dimensions_and_deletions_are_idempotent(
    tmp_path: Path,
) -> None:
    _scope(tmp_path)
    preferences.save(
        tmp_path,
        0,
        {
            "rules": [
                {
                    "when": {"scope": "course", "topic": "systems"},
                    "values": {
                        "pace": {
                            "instruction": "Slow",
                            "origin": "inferred",
                            "basis": "Repeated requests",
                        },
                        "format": {"instruction": "Paragraphs", "origin": "explicit"},
                    },
                },
                _rule({}, "Default"),
            ]
        },
    )
    change = {"rules": [_rule({"topic": "systems", "scope": "course"}, "Faster")]}
    receipt = preferences.save(tmp_path, 1, change)
    assert receipt["revision"] == 2
    assert receipt["selectors"] == [{"scope": "course", "topic": "systems"}]
    assert "rules" not in receipt
    current = preferences.read(tmp_path)
    values = current["rules"][1]["values"]
    assert values == {
        "pace": {"instruction": "Faster", "origin": "explicit"},
        "format": {"instruction": "Paragraphs", "origin": "explicit"},
    }
    assert preferences.save(tmp_path, 2, change)["selectors"] == []
    assert preferences.read(tmp_path) == current
    deletion = {
        "rules": [
            {
                "when": {"scope": "course", "topic": "systems"},
                "values": {"pace": None, "format": None},
            }
        ]
    }
    assert preferences.save(tmp_path, 2, deletion)["revision"] == 3
    assert preferences.read(tmp_path)["rules"] == [_rule({}, "Default")]
    assert preferences.save(tmp_path, 3, deletion)["revision"] == 3


def test_stale_patch_cannot_overwrite_committed_policy(tmp_path: Path) -> None:
    assert preferences.save(tmp_path, 0, {"rules": []})["revision"] == 0
    assert not (tmp_path / "preferences.json").exists()
    preferences.save(tmp_path, 0, {"rules": [_rule({}, "Keep")]})
    current = preferences.read(tmp_path)
    with pytest.raises(ValueError, match="revision conflict"):
        preferences.save(tmp_path, 0, {"rules": [_rule({}, "Stale")]})
    assert preferences.read(tmp_path) == current


@pytest.mark.parametrize(
    ("rule", "message"),
    [
        (_rule({"topic": "systems"}, "Text"), "requires its scope"),
        (_rule({"scope": "absent"}, "Text"), "unknown scope"),
        (_rule({"scope": "course", "topic": "absent"}, "Text"), "unknown topic"),
        (_rule({"scope": "../course"}, "Text"), "invalid scope"),
        (_rule({"unsupported": "x"}, "Text"), "when must contain"),
        (_rule({}, " "), "nonempty string"),
        (_rule({}, "Text", "guessed"), "origin must"),
    ],
)
def test_invalid_policy_does_not_publish(
    tmp_path: Path, rule: dict[str, Any], message: str
) -> None:
    _scope(tmp_path)
    with pytest.raises(ValueError, match=message):
        preferences.save(tmp_path, 0, {"rules": [rule]})
    assert preferences.read(tmp_path)["revision"] == 0


def test_unknown_topics_and_duplicate_dimensions_are_not_silently_accepted(
    tmp_path: Path,
) -> None:
    state = _scope(tmp_path)
    with pytest.raises(ValueError, match="unknown topic"):
        preferences.context(tmp_path, "course", topics=["absent"], state=state)
    with pytest.raises(ValueError, match="topic selection requires"):
        preferences.context(tmp_path, topics=["systems"])
    with pytest.raises(ValueError, match="requires the retrieved scope state"):
        preferences.context(tmp_path, "course", topics=["systems"])
    with pytest.raises(ValueError, match="duplicate preference"):
        preferences.save(
            tmp_path, 0, {"rules": [_rule({}, "First"), _rule({}, "Second")]}
        )


def test_unrecorded_scope_can_read_general_preferences(tmp_path: Path) -> None:
    preferences.save(
        tmp_path,
        0,
        {
            "rules": [
                _rule({}, "Global"),
                _rule({"domain": "mathematics", "activity": "proof"}, "Proof"),
            ]
        },
    )
    result = preferences.context(
        tmp_path, "new-course", domains=["mathematics"], activity="proof"
    )
    assert {rule["values"]["pace"]["instruction"] for rule in result["rules"]} == {
        "Global",
        "Proof",
    }
    assert not (tmp_path / "state").exists()
    with pytest.raises(ValueError, match="unknown topic"):
        preferences.context(
            tmp_path, "new-course", topics=["missing"], state={"revision": 0}
        )
    with pytest.raises(ValueError, match="invalid scope"):
        preferences.context(tmp_path, "../invalid")


@pytest.mark.parametrize("when", [{}, {"scope": "course", "topic": "systems"}])
def test_inference_cannot_replace_explicit_preference(
    tmp_path: Path, when: dict[str, str]
) -> None:
    _scope(tmp_path)
    preferences.save(tmp_path, 0, {"rules": [_rule(when, "One step at a time")]})
    path = tmp_path / "preferences.json"
    original = path.read_bytes()
    with pytest.raises(ValueError, match="cannot replace explicit pace"):
        preferences.save(
            tmp_path,
            1,
            {"rules": [_rule(when, "Long uninterrupted lectures", "inferred")]},
        )
    assert path.read_bytes() == original
    assert (
        preferences.save(tmp_path, 1, {"rules": [_rule(when, "Move faster")]})[
            "revision"
        ]
        == 2
    )


def test_preference_applicability_uses_retrieved_scope_snapshot(tmp_path: Path) -> None:
    state = _scope(tmp_path)
    preferences.save(
        tmp_path,
        0,
        {
            "rules": [
                _rule({"concept": "linear-systems"}, "Original concept"),
                _rule({"concept": "new-concept"}, "Changed concept"),
            ]
        },
    )
    storage.update(
        tmp_path / "state/course.json",
        1,
        lambda _: {"topics": {"systems": {"concepts": ["new-concept"]}}},
    )
    selected = preferences.context(tmp_path, "course", topics=["systems"], state=state)
    assert selected["scope_revision"] == 1
    assert [rule["values"]["pace"]["instruction"] for rule in selected["rules"]] == [
        "Original concept"
    ]


def test_topic_removal_requires_resolving_its_preferences(tmp_path: Path) -> None:
    _scope(tmp_path)
    when = {"scope": "course", "topic": "systems"}
    preferences.save(tmp_path, 0, {"rules": [_rule(when, "One step at a time")]})
    with storage.lock(tmp_path / ".records.lock"):
        with pytest.raises(ValueError, match="remove or reassign their preferences"):
            preferences.assert_topics_removable(tmp_path, "course", {"systems"})
        preferences.assert_topics_removable(tmp_path, "course", {"other"})
        preferences.assert_topics_removable(tmp_path, "another", {"systems"})
    preferences.save(tmp_path, 1, {"rules": [{"when": when, "values": {"pace": None}}]})
    with storage.lock(tmp_path / ".records.lock"):
        preferences.assert_topics_removable(tmp_path, "course", {"systems"})
