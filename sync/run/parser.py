"""CLI parser construction for sync.run."""

from __future__ import annotations

import argparse

from sync.log import add_logging_cli_args


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    add_logging_cli_args(parser)
    domain = parser.add_subparsers(dest="domain", required=True)

    period = domain.add_parser("period", help="Run daily/period journal sync")
    period_sub = period.add_subparsers(dest="period_command", required=True)

    period_sub.add_parser("all", help="Run daily + all period sync commands")

    period_sub.add_parser("daily", help="Run daily sync")

    period_weekly = period_sub.add_parser("weekly", help="Run weekly sync")
    period_weekly.add_argument("--date", help="Date within week (YYYY-MM-DD)")
    period_weekly.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Skip cleanup of previous period",
    )

    period_monthly = period_sub.add_parser("monthly", help="Run monthly sync")
    period_monthly.add_argument("--month", help="Month (YYYY-MM)")
    period_monthly.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Skip cleanup of previous period",
    )

    period_yearly = period_sub.add_parser("yearly", help="Run yearly sync")
    period_yearly.add_argument("--year", help="Year (YYYY)")

    session = domain.add_parser("session", help="Run Flow session operations")
    session_sub = session.add_subparsers(dest="session_command", required=True)

    session_rename = session_sub.add_parser(
        "rename", help="Rename most recent focus session"
    )
    session_rename.add_argument("title")
    session_rename.add_argument("--confirm", action="store_true")

    session_undo = session_sub.add_parser(
        "undo", help="Delete most recent focus session"
    )
    session_undo_mode = session_undo.add_mutually_exclusive_group()
    session_undo_mode.add_argument("--confirm", action="store_true")
    session_undo_mode.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable preview",
    )

    session_skip = session_sub.add_parser(
        "skip", help="Execute or manage skip automation"
    )
    session_skip.add_argument(
        "--state",
        choices=["toggle", "status"],
        help="Manage launchd skip automation state",
    )

    session_remind = session_sub.add_parser(
        "remind", help="Execute or manage resume reminder automation"
    )
    session_remind.add_argument(
        "--state",
        choices=["toggle", "status"],
        help="Manage launchd remind automation state",
    )

    grades = domain.add_parser("grades", help="Run grades note operations")
    grades_sub = grades.add_subparsers(dest="grades_command", required=True)

    grades_sync = grades_sub.add_parser(
        "sync", help="Recompute OVERALL summary values in GRADES.md"
    )
    grades_sync.add_argument(
        "degree",
        choices=["bsc", "msc"],
        help="Degree whose grades note should be synchronized",
    )

    media = domain.add_parser("media", help="Run media note operations")
    media_sub = media.add_subparsers(dest="media_command", required=True)

    media_podcast = media_sub.add_parser("podcast", help="Run podcast note operations")
    media_podcast_sub = media_podcast.add_subparsers(
        dest="podcast_command", required=True
    )

    media_podcast_add = media_podcast_sub.add_parser(
        "add", help="Create podcast note from a YouTube URL"
    )
    media_podcast_add.add_argument("url")
    media_podcast_add.add_argument("--date", help="Override date (YYYY-MM-DD)")
    media_podcast_add.add_argument(
        "--title",
        help="Override fetched title when metadata lookup fails",
    )
    media_podcast_add.add_argument(
        "--host",
        help="Override fetched host when metadata lookup fails",
    )

    media_book = media_sub.add_parser("book", help="Run book note operations")
    media_book_sub = media_book.add_subparsers(dest="book_command", required=True)

    media_book_annotations = media_book_sub.add_parser(
        "annotations",
        help="Run book annotation operations",
    )
    media_book_annotations_sub = media_book_annotations.add_subparsers(
        dest="book_annotations_command",
        required=True,
    )

    media_book_annotations_import = media_book_annotations_sub.add_parser(
        "import",
        help="Import Kindle Notebook HTML annotations into a book note",
    )
    media_book_annotations_import.add_argument(
        "html_path",
        help="Absolute path to Kindle Notebook HTML export",
    )
    media_book_annotations_import.add_argument(
        "--note",
        required=True,
        help="Absolute path to target book markdown note",
    )
    media_book_annotations_import.add_argument(
        "--work",
        help="Override the work title to import from anthology exports",
    )

    return parser
