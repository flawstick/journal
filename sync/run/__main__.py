"""Unified runtime CLI for journal sync and session/media utilities."""

from __future__ import annotations

import argparse
import sys

from sync.log import configure_logging, get_logger, resolve_logging_settings
from sync.run.parser import build_parser

logger = get_logger(__name__)


def _dispatch(args: argparse.Namespace) -> int:
    if args.domain == "period":
        from sync.run import wiring

        command = args.period_command
        if command in ("all", "daily"):
            wiring.run_daily_sync()
        if command in ("all", "weekly"):
            wiring.run_weekly_sync(
                date_arg=args.date if command == "weekly" else None,
                no_cleanup=args.no_cleanup if command == "weekly" else False,
            )
        if command in ("all", "monthly"):
            wiring.run_monthly_sync(
                month_arg=args.month if command == "monthly" else None,
                no_cleanup=args.no_cleanup if command == "monthly" else False,
            )
        if command in ("all", "yearly"):
            wiring.run_yearly_sync(
                year_arg=args.year if command == "yearly" else None,
            )
        return 0
    if args.domain == "session":
        if args.session_command == "skip":
            from sync.study.flow_automation import run_session_skip

            return run_session_skip(args.state)
        if args.session_command == "remind":
            from sync.study.flow_automation import run_session_remind

            return run_session_remind(args.state)
        from sync.run.commands.session import cmd_session_rename, cmd_session_undo

        if args.session_command == "rename":
            return cmd_session_rename(args)
        return cmd_session_undo(args)
    if args.domain == "grades":
        from sync.run.commands.grades import cmd_grades_sync

        return cmd_grades_sync(args)
    if args.media_command == "podcast":
        from sync.run.commands.media_podcast import cmd_media_podcast_add

        return cmd_media_podcast_add(args)
    from sync.run.commands.media_books import cmd_media_book_annotations_import

    return cmd_media_book_annotations_import(args)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    level, log_format = resolve_logging_settings(args)
    configure_logging(level=level, log_format=log_format)

    try:
        return _dispatch(args)
    except Exception:
        logger.exception("sync.run command failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
