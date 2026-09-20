"""Obsidian math delimiters at the lesson publication boundary."""

from __future__ import annotations

import re

# Consume literal/code regions before considering TeX delimiters.
_REGIONS = re.compile(
    r"(?P<fence>^ {0,3}(?P<mark>`{3,}|~{3,})[^\n]*\n"
    r".*?(?:^ {0,3}(?P=mark)[`~]*[ \t]*(?:\n|$)|\Z))"
    r"|(?P<indent>^(?: {4}|\t)[^\n]*(?:\n|$))"
    r"|(?P<code>(?P<ticks>`+)(?!`).*?(?<!`)(?P=ticks)(?!`))"
    r"|(?P<escaped>\\\\)"
    r"|(?P<dollars>(?<!\\)\$\$.*?(?<!\\)\$\$|(?<!\\)\$[^\n$]+?(?<!\\)\$)"
    r"|\\\((?P<inline>[^\n]*?)\\\)"
    r"|\\\[(?P<display>.*?)\\\]",
    re.MULTILINE | re.DOTALL,
)


def obsidian_math(text: str) -> str:
    """Normalize paired TeX math; leave code and existing dollar math untouched."""

    def replace(match: re.Match[str]) -> str:
        inline = match.group("inline")
        if inline is not None:
            return f"${inline.strip()}$"
        display = match.group("display")
        if display is not None:
            return f"$$\n{display.strip()}\n$$"
        return match[0]

    return _REGIONS.sub(replace, text)
