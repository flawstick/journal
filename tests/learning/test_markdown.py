import pytest

from learning.markdown import obsidian_math


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (r"\(P\) swaps coordinates.", "$P$ swaps coordinates."),
        (r"\[P(4,-1,7)=\;?\]", "$$\nP(4,-1,7)=\\;?\n$$"),
        (
            "\\[\n\\begin{aligned}a&=b\\\\ c&=d\\end{aligned}\n\\]",
            "$$\n\\begin{aligned}a&=b\\\\ c&=d\\end{aligned}\n$$",
        ),
        (r"`\(code\)` then \(x\)", r"`\(code\)` then $x$"),
        (r"`` `\(code\)` `` then \(x\)", r"`` `\(code\)` `` then $x$"),
        ("```tex\n\\[literal\\]\n```\n\\(x\\)", "```tex\n\\[literal\\]\n```\n$x$"),
        ("~~~~\n\\(literal\\)\n~~~~\n\\(x\\)", "~~~~\n\\(literal\\)\n~~~~\n$x$"),
        ("```\n\\(unfinished code\\)", "```\n\\(unfinished code\\)"),
        ("    \\(code\\)\n\n\\(x\\)", "    \\(code\\)\n\n$x$"),
        (r"$\text{\(literal\)}$ and \(x\)", r"$\text{\(literal\)}$ and $x$"),
        (r"$$\text{\[literal\]}$$", r"$$\text{\[literal\]}$$"),
        (r"\\(escaped\\) and \(x\)", r"\\(escaped\\) and $x$"),
        (r"An unmatched \( stays untouched.", r"An unmatched \( stays untouched."),
    ],
)
def test_obsidian_math(source: str, expected: str) -> None:
    assert obsidian_math(source) == expected
    assert obsidian_math(expected) == expected
