"""Correction relationships shared by evidence retrieval and assessment freshness."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any


def correction_links(observations: dict[str, Any]) -> dict[str, set[str]]:
    """Index corrections in both directions so every linked event stays visible."""
    links: defaultdict[str, set[str]] = defaultdict(set)
    for key, observation in observations.items():
        for target in observation.get("corrects", []):
            links[key].add(target)
            links[target].add(key)
    return dict(links)


def expand_corrections(links: dict[str, set[str]], selected: Iterable[str]) -> set[str]:
    """Return the complete correction components containing selected observations."""
    expanded = set(selected)
    pending = list(expanded)
    while pending:
        for linked in links.get(pending.pop(), ()):
            if linked not in expanded:
                expanded.add(linked)
                pending.append(linked)
    return expanded
