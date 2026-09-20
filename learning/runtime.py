"""Pi is one interface to the shared records, independent of their ownership."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import sys


def start_pi(vault: Path, root: Path, args: argparse.Namespace) -> None:
    pi = shutil.which("pi")
    if not pi:
        raise ValueError("Pi is not available in the learning launcher's PATH")
    if not vault.is_dir():
        raise ValueError(f"Vault does not exist: {vault}")
    runtime = Path(__file__).resolve().parent
    root.mkdir(parents=True, exist_ok=True)
    assets = (
        Path(os.environ.get("LEARNING_ASSETS", vault / "assets/learn"))
        .expanduser()
        .resolve()
    )
    assets.mkdir(parents=True, exist_ok=True)
    os.environ.update(
        {
            "LEARNING_ROOT": str(root),
            "LEARNING_VAULT": str(vault),
            "VAULT_DIR": str(vault),
            "LEARNING_ASSETS": str(assets),
            "LEARNING_PYTHON": sys.executable,
            "LEARNING_PACKAGE": str(runtime.parent),
            "LEARNING_OPEN": "0" if args.no_open or args.headless or args.json else "1",
        }
    )
    prompt = (
        "You are a personal study tutor. Use the learn skill for study requests. "
        "The learner talks here; your Markdown is automatically mirrored into Obsidian. "
        "Responses focus only on study content; handle all record keeping under the hood.\n"
        f"Course sources and prior learning: {vault}\n"
        f"Shared learning records and sessions: {root}\n"
        f"Generated study assets: {assets}\n"
        "Use native file tools for source discovery. "
        "The skill's scripts/learn provides planning, Journal context and saved study notes."
    )
    sessions = Path(
        os.environ.get(
            "LEARNING_SESSION_DIR",
            Path.home() / "Library/Application Support/Learning/pi-sessions",
        )
    )
    command = [
        pi,
        "--provider",
        "openai-codex",
        "--no-context-files",
        "--no-extensions",
        "--no-skills",
        "--no-prompt-templates",
        "--extension",
        str(runtime / "pi.ts"),
        "--extension",
        "npm:pi-web-search@1.6.0",
        "--skill",
        str(runtime / "skills/learn"),
        "--system-prompt",
        prompt,
        "--session-dir",
        str(sessions),
        "--tools",
        "read,bash,edit,write,grep,find,ls",
    ]
    if args.resume:
        command.append("--continue")
    if args.headless or args.json:
        command.append("--print")
    if args.json:
        command.extend(["--mode", "json"])
    if args.prompt:
        command.append(args.prompt)
    os.chdir(root)
    os.execv(pi, command)
