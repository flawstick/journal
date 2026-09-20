"""Stable task purpose and small, task-local teaching plans."""

from __future__ import annotations

from graphlib import CycleError, TopologicalSorter
import re
from typing import Any


def validate(task: dict[str, Any], field: str) -> None:
    """Validate plan structure; learning.records validates evidence/source links."""
    if "frame" in task:
        frame = task["frame"]
        if not isinstance(frame, dict):
            raise ValueError(f"{field}.frame must be an object")
        for name in ("within", "goal", "completion"):
            if name in frame and (
                not isinstance(frame[name], str) or not frame[name].strip()
            ):
                raise ValueError(f"{field}.frame.{name} must be a nonempty string")
    if "plan" not in task:
        return
    plan = task["plan"]
    if not isinstance(plan, dict) or plan.get("status") not in ("proposed", "agreed"):
        raise ValueError(f"{field}.plan requires status proposed or agreed")
    nodes = plan.get("nodes")
    if not isinstance(nodes, dict) or not nodes:
        raise ValueError(f"{field}.plan.nodes must be a nonempty object")
    graph = {}
    for key, node in nodes.items():
        if not isinstance(key, str) or not re.fullmatch(
            r"[a-z0-9][a-z0-9_-]{0,63}", key
        ):
            raise ValueError(
                f"{field}.plan node handles must be short lowercase identifiers"
            )
        if (
            not isinstance(node, dict)
            or not isinstance(node.get("label"), str)
            or not node["label"].strip()
        ):
            raise ValueError(f"{field}.plan.nodes.{key} requires a label")
        needs = node.get("needs", [])
        if not isinstance(needs, list) or any(
            not isinstance(item, str) for item in needs
        ):
            raise ValueError(
                f"{field}.plan.nodes.{key}.needs must be a list of node handles"
            )
        if len(needs) != len(set(needs)) or any(item not in nodes for item in needs):
            raise ValueError(
                f"{field}.plan.nodes.{key}.needs has duplicate or unknown nodes"
            )
        graph[key] = needs
    try:
        tuple(TopologicalSorter(graph).static_order())
    except CycleError as error:
        raise ValueError(f"{field}.plan dependencies must be acyclic") from error
    current = plan.get("current")
    if current is not None and (not isinstance(current, str) or current not in nodes):
        raise ValueError(f"{field}.plan.current must name a plan node")


def parts(task: dict[str, Any], *, active_only: bool = False) -> list[dict[str, Any]]:
    """Expose link-bearing context; routine retrieval excludes distant plan nodes."""
    result = [task["frame"]] if "frame" in task else []
    plan = task.get("plan", {})
    nodes = plan.get("nodes", {})
    if active_only:
        current = plan.get("current")
        keys = [current, *nodes[current].get("needs", [])] if current else []
    else:
        keys = list(nodes)
    result.extend(nodes[key] for key in keys)
    return result
