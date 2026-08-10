"""Command-line interface."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .doctor import run_checks
from .linker import AddError, Result, add_file, link_all, status_all, unlink_all
from .manifest import MANIFEST_NAME, ManifestError, add_entries, init, load


GREEN, YELLOW, RED, CYAN, DIM, RESET = "\033[32m", "\033[33m", "\033[31m", "\033[36m", "\033[2m", "\033[0m"
LABEL_COLORS = {
    "ok": GREEN, "linked": GREEN, "copied": GREEN, "relinked": GREEN, "added": GREEN,
    "backed-up": YELLOW, "missing": YELLOW, "modified": YELLOW,
    "conflict": RED, "wrong-link": RED, "no-source": RED, "error": RED, "fail": RED, "warn": YELLOW,
    "unlinked": CYAN, "restored": CYAN, "skipped": DIM,
}
use_color = False


def user_path(text: str) -> Path:
    # "~" is not expanded by every shell (or when quoted), so do it here
    return Path(text).expanduser()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dotkeep", description="Keep dotfiles in one folder and link them into place.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    default_repo = user_path(os.environ.get("DOTKEEP_REPO", "~/dotfiles"))
    parser.add_argument("--repo", type=user_path, default=default_repo, help="dotfiles folder (default: $DOTKEEP_REPO or ~/dotfiles)")
    parser.add_argument("--mode", choices=["symlink", "copy"], help="override settings.mode from the manifest")
    parser.add_argument("--no-color", action="store_true", help="plain output (also set by NO_COLOR)")
    parser.add_argument("--home", type=user_path, default=Path.home(), help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="create the dotfiles folder and a starter dotkeep.toml")

    p_link = sub.add_parser("link", help="link every file in the manifest into place")
    p_link.add_argument("-n", "--dry-run", action="store_true", help="show what would change, change nothing")
    p_link.add_argument("-f", "--force", action="store_true", help="replace links that point somewhere else")
    p_link.add_argument("--no-backup", action="store_true", help="skip files that already exist instead of moving them aside")

    p_add = sub.add_parser("add", help="move a file into the repo and link it back")
    p_add.add_argument("paths", nargs="+", type=user_path, metavar="PATH")

    p_unlink = sub.add_parser("unlink", help="remove the links (the files in the repo stay)")
    p_unlink.add_argument("-n", "--dry-run", action="store_true", help="show what would change, change nothing")
    p_unlink.add_argument("--restore", action="store_true", help="leave a real copy of each file in place of the link")

    sub.add_parser("status", help="show the state of every link")
    sub.add_parser("list", help="list the entries for this platform")
    sub.add_parser("doctor", help="check the setup for common problems")
    return parser


def main(argv: list[str] | None = None) -> int:
    global use_color
    args = build_parser().parse_args(argv)
    use_color = sys.stdout.isatty() and not args.no_color and "NO_COLOR" not in os.environ
    if args.command == "init":
        if init(args.repo):
            print(f"created {args.repo / MANIFEST_NAME}")
            return 0
        print(f"dotkeep: {args.repo / MANIFEST_NAME} already exists", file=sys.stderr)
        return 1
    if args.command == "add":
        return cmd_add(args)
    if args.command == "doctor":
        checks = run_checks(args.repo, args.home)
        for c in checks:
            print(f"{paint(c.level, 5)} {c.message}")
        return 1 if any(c.level == "fail" for c in checks) else 0
    try:
        manifest = load(args.repo)
    except ManifestError as e:
        print(f"dotkeep: {e}", file=sys.stderr)
        return 1

    if args.command == "link":
        results = link_all(
            manifest, args.home, backup=not args.no_backup, dry_run=args.dry_run, mode=args.mode, force=args.force
        )
        would = {"linked": "link", "copied": "copy", "relinked": "relink", "backed-up": "back up"}
        for r in results:
            action = r.action
            if args.dry_run and action in would:
                action = "would " + would[action]
            show(action, r)
        return 1 if any(r.action == "error" for r in results) else 0

    if args.command == "unlink":
        for r in unlink_all(manifest, args.home, dry_run=args.dry_run, mode=args.mode, restore=args.restore):
            label = r.action
            if args.dry_run and label in ("unlinked", "restored"):
                label = "would " + ("unlink" if label == "unlinked" else "restore")
            show(label, r)
        return 0

    if args.command == "list":
        width = max((len(e.target) for e in manifest.entries), default=0)
        for e in manifest.entries:
            print(f"{e.target:{width}}  ->  {e.source}")
        return 0

    if args.command == "status":
        results = status_all(manifest, args.home, mode=args.mode)
        for r in results:
            show(r.action, r)
        return 0 if all(r.action == "ok" for r in results) else 1
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    failed = False
    added = []
    for path in args.paths:
        try:
            added.append(add_file(args.repo, args.home, path))
        except AddError as e:
            print(f"dotkeep: {e}", file=sys.stderr)
            failed = True
    if added:
        add_entries(args.repo, added)
        for entry in added:
            print(f"{paint('added', 10)} {entry.target}  ->  {entry.source}")
    return 1 if failed else 0


def show(label: str, r: Result) -> None:
    print(f"{paint(label, 10)} {r.entry.target}" + (f"  ({r.detail})" if r.detail else ""))


def paint(label: str, width: int) -> str:
    text = f"{label:{width}}"
    color = LABEL_COLORS.get(label.split()[-1] if label.startswith("would") else label)
    if not use_color or not color:
        return text
    return f"{color}{text}{RESET}"
