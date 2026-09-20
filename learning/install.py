"""Maintain local client links and launch artifacts from this repository."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
import shlex
import shutil
import sys
import zipfile


def install_codex_instructions(package: Path, support: Path) -> None:
    target = Path.home() / ".codex/config.toml"
    original = target.read_text(encoding="utf-8") if target.exists() else ""
    start, end = "# Learning communication\n", "# End learning communication\n"
    instruction = (package / "clients/codex/instructions.md").read_text().strip()
    block = start + "developer_instructions = " + json.dumps(instruction) + "\n" + end
    if start in original:
        before, _, tail = original.partition(start)
        _, separator, after = tail.partition(end)
        if not separator:
            raise ValueError("incomplete learning communication block in Codex config")
        updated = before + block + after
    else:
        if re.search(r"(?m)^developer_instructions\s*=", original):
            raise ValueError(
                "merge existing Codex developer instructions before installing"
            )
        updated = block + original
    if updated != original:
        backup = support / "backups" / datetime.now().strftime("%Y%m%d-%H%M%S")
        backup.mkdir(parents=True, exist_ok=True)
        if target.exists():
            shutil.copy2(target, backup / "codex-config.toml")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(updated, encoding="utf-8")


def install_command(repo: Path, support: Path) -> None:
    """Install the terminal entrypoint without launching a new terminal window."""
    pi = shutil.which("pi")
    if pi is None:
        raise ValueError("Pi must already be installed to build the study command")
    command = Path.home() / ".local/bin/study"
    content = (
        "#!/bin/sh\nexport PATH="
        + shlex.quote(str(Path(pi).parent))
        + ':"$PATH"\ncd '
        + shlex.quote(str(repo))
        + " || exit 1\nexec "
        + shlex.quote(sys.executable)
        + ' -m learning start "$@"\n'
    )
    old_launchers = [Path.home() / "Applications/Study.app", support / "Study.command"]
    replaced = [path for path in old_launchers if path.exists()]
    if command.exists() and command.read_text() != content:
        replaced.append(command)
    if replaced:
        backup = support / "backups" / datetime.now().strftime("%Y%m%d-%H%M%S-cli")
        backup.mkdir(parents=True, exist_ok=True)
        for path in replaced:
            shutil.move(str(path), str(backup / path.name))
    command.parent.mkdir(parents=True, exist_ok=True)
    command.write_text(content, encoding="utf-8")
    command.chmod(0o755)


def install() -> None:
    package = Path(__file__).resolve().parent
    repo = package.parent
    support = Path.home() / "Library/Application Support/Learning"
    support.mkdir(parents=True, exist_ok=True)
    install_codex_instructions(package, support)
    skill = package / "skills/learn"
    for host in (".agents", ".claude"):
        target = Path.home() / host / "skills/learn"
        if target.is_symlink() and target.resolve() == skill:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() or target.is_symlink():
            backup = support / "backups" / datetime.now().strftime("%Y%m%d-%H%M%S")
            backup.mkdir(parents=True, exist_ok=True)
            shutil.move(str(target), str(backup / f"{host[1:]}-learn"))
        target.symlink_to(skill, target_is_directory=True)

    install_command(repo, support)

    # Claude stores uploaded skills remotely; only the stable local locator is uploaded.
    router = package / "clients/claude/teach/SKILL.md"
    with zipfile.ZipFile(
        support / "learn-claude.zip", "w", zipfile.ZIP_DEFLATED
    ) as archive:
        archive.write(router, "teach/SKILL.md")


if __name__ == "__main__":
    install()
