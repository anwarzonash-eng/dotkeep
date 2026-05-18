"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .linker import Result, link_all, status_all, unlink_all
from .manifest import ManifestError, load


def user_path(text: str) -> Path:
    # "~" is not expanded by every shell (or when quoted), so do it here
    return Path(text).expanduser()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dotkeep", description="Keep dotfiles in one folder and link them into place.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--repo", type=user_path, default=Path.home() / "dotfiles", help="dotfiles folder (default: ~/dotfiles)")
    parser.add_argument("--home", type=user_path, default=Path.home(), help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)

    p_link = sub.add_parser("link", help="link every file in the manifest into place")
    p_link.add_argument("-n", "--dry-run", action="store_true", help="show what would change, change nothing")
    p_link.add_argument("--no-backup", action="store_true", help="skip files that already exist instead of moving them aside")

    p_unlink = sub.add_parser("unlink", help="remove the links (the files in the repo stay)")
    p_unlink.add_argument("-n", "--dry-run", action="store_true", help="show what would change, change nothing")

    sub.add_parser("status", help="show the state of every link")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = load(args.repo)
    except ManifestError as e:
        print(f"dotkeep: {e}", file=sys.stderr)
        return 1

    if args.command == "link":
        results = link_all(manifest, args.home, backup=not args.no_backup, dry_run=args.dry_run)
        for r in results:
            action = r.action
            if args.dry_run and action in ("linked", "backed-up"):
                action = "would " + ("link" if action == "linked" else "back up")
            show(action, r)
        return 1 if any(r.action == "error" for r in results) else 0

    if args.command == "unlink":
        for r in unlink_all(manifest, args.home, dry_run=args.dry_run):
            show("would unlink" if args.dry_run and r.action == "unlinked" else r.action, r)
        return 0

    if args.command == "status":
        results = status_all(manifest, args.home)
        for r in results:
            show(r.action, r)
        return 0 if all(r.action == "ok" for r in results) else 1
    return 0


def show(label: str, r: Result) -> None:
    print(f"{label:10} {r.entry.target}" + (f"  ({r.detail})" if r.detail else ""))
