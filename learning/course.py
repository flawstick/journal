"""Small, source-grounded course context within an existing learning scope."""

from __future__ import annotations

from datetime import date
import re
from typing import Any


def normalize_context(value: Any, sources: dict[str, Any]) -> dict[str, Any]:
    """Validate optional assessment context without inferring course requirements."""
    if not isinstance(value, dict):
        raise ValueError("course_context must be an object")
    allowed = {
        "assessment",
        "criteria",
        "constraints",
        "unknowns",
        "refs",
        "checked_on",
    }
    unknown = value.keys() - allowed
    if unknown:
        raise ValueError(f"unknown course_context fields: {', '.join(sorted(unknown))}")
    result = dict(value)
    if "assessment" in result and (
        not isinstance(result["assessment"], str) or not result["assessment"].strip()
    ):
        raise ValueError("course_context.assessment must be a nonempty string")
    for field in ("criteria", "constraints", "unknowns"):
        if field in result and (
            not isinstance(result[field], list)
            or any(
                not isinstance(item, str) or not item.strip() for item in result[field]
            )
        ):
            raise ValueError(
                f"course_context.{field} must be a list of nonempty strings"
            )
    if "checked_on" in result:
        checked_on = result["checked_on"]
        if not isinstance(checked_on, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}", checked_on
        ):
            raise ValueError(
                "course_context.checked_on must be a date in YYYY-MM-DD form"
            )
        try:
            date.fromisoformat(checked_on)
        except ValueError as error:
            raise ValueError("course_context.checked_on is not a valid date") from error
    if "refs" in result:
        refs = result["refs"]
        if not isinstance(refs, list):
            raise ValueError("course_context.refs must be a list")
        for ref in refs:
            if (
                not isinstance(ref, dict)
                or set(ref) - {"source", "locator"}
                or not isinstance(ref.get("source"), str)
                or ("locator" in ref and not isinstance(ref["locator"], str))
            ):
                raise ValueError(
                    "course_context.refs must contain source handles and optional string locators"
                )
            if ref["source"] not in sources:
                raise ValueError(f"unknown course_context source: {ref['source']}")
    return result


def context_for_plan(record: dict[str, Any]) -> dict[str, Any]:
    """Project course context and source locations needed to interpret the plan."""
    context = record.get("course_context")
    coverage = record.get("coverage")
    sources = record.get("sources", {})
    referenced: set[str] = set()
    for item in (context, coverage):
        if isinstance(item, dict):
            if "source" in item:
                referenced.add(item["source"])
            referenced.update(ref["source"] for ref in item.get("refs", []))
    result: dict[str, Any] = {}
    if context:
        result["course_context"] = context
    if referenced:
        result["sources"] = {key: sources[key] for key in sorted(referenced)}
    return result
