"""Command-line interface."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable
from pathlib import Path

from . import __version__
from .doctor import run_checks
from .linker import AddError, Result, add_file, link_all, remove, remove_entry, status_all, unlink_all
from .manifest import MANIFEST_NAME, Manifest, ManifestError, add_entries, all_sources, init, load, remove_targets

GREEN, YELLOW, RED, CYAN, DIM, RESET = "\033[32m", "\033[33m", "\033[31m", "\033[36m", "\033[2m", "\033[0m"
LABEL_COLORS = {
    "ok": GREEN, "linked": GREEN, "copied": GREEN, "relinked": GREEN, "added": GREEN,
    "backed-up": YELLOW, "missing": YELLOW, "modified": YELLOW,
    "conflict": RED, "wrong-link": RED, "no-source": RED, "error": RED, "fail": RED, "warn": YELLOW,
    "unlinked": CYAN, "restored": CYAN, "removed": CYAN, "skipped": DIM,
}
# "would link" is colored like "linked"
WOULD = {"link": "linked", "copy": "copied", "relink": "relinked", "back up": "backed-up",
         "unlink": "unlinked", "restore": "restored"}
use_color = False
quiet = False


def user_path(text: str) -> Path:
    # "~" is not expanded by every shell (or when quoted), so do it here
    return Path(text).expanduser()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dotkeep", description="Keep dotfiles in one folder and link them into place."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    default_repo = user_path(os.environ.get("DOTKEEP_REPO", "~/dotfiles"))
    parser.add_argument(
        "--repo", type=user_path, default=default_repo, help="dotfiles folder (default: $DOTKEEP_REPO or ~/dotfiles)"
    )
    parser.add_argument("--mode", choices=["symlink", "copy"], help="override settings.mode from the manifest")
    parser.add_argument("-q", "--quiet", action="store_true", help="only show changes and problems")
    parser.add_argument("--no-color", action="store_true", help="plain output (also set by NO_COLOR)")
    parser.add_argument("--home", type=user_path, default=Path.home(), help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="create the dotfiles folder and a starter dotkeep.toml")

    p_link = sub.add_parser("link", help="link every file in the manifest into place")
    p_link.add_argument("-n", "--dry-run", action="store_true", help="show what would change, change nothing")
    p_link.add_argument("-f", "--force", action="store_true", help="replace links that point somewhere else")
    p_link.add_argument(
        "--no-backup", action="store_true", help="skip files that already exist instead of moving them aside"
    )

    p_add = sub.add_parser("add", help="move a file into the repo and link it back")
    p_add.add_argument("paths", nargs="+", type=user_path, metavar="PATH")
    p_add.add_argument(
        "--as", dest="source", metavar="REPO_PATH", help="where to put the file in the repo (one PATH only)"
    )

    p_unlink = sub.add_parser("unlink", help="remove the links (the files in the repo stay)")
    p_unlink.add_argument("-n", "--dry-run", action="store_true", help="show what would change, change nothing")
    p_unlink.add_argument("--restore", action="store_true", help="leave a real copy of each file in place of the link")

    p_remove = sub.add_parser("remove", help="stop tracking files: put real copies back and drop them from the repo")
    p_remove.add_argument("targets", nargs="+", metavar="PATH", help="a path in your home folder, such as ~/.vimrc")

    sub.add_parser("status", help="show the state of every link")
    sub.add_parser("list", help="list the entries for this platform")
    sub.add_parser("doctor", help="check the setup for common problems")
    return parser


def main(argv: list[str] | None = None) -> int:
    global use_color, quiet
    args = build_parser().parse_args(argv)
    use_color = sys.stdout.isatty() and not args.no_color and "NO_COLOR" not in os.environ
    quiet = args.quiet

    if args.command in STANDALONE:
        return STANDALONE[args.command](args)
    try:
        manifest = load(args.repo)
    except ManifestError as e:
        print(f"dotkeep: {e}", file=sys.stderr)
        return 1
    return WITH_MANIFEST[args.command](args, manifest)


# commands that work without a valid manifest


def cmd_init(args: argparse.Namespace) -> int:
    try:
        created = init(args.repo)
    except ManifestError as e:
        print(f"dotkeep: {e}", file=sys.stderr)
        return 1
    if created:
        print(f"created {args.repo / MANIFEST_NAME}")
        return 0
    print(f"dotkeep: {args.repo / MANIFEST_NAME} already exists", file=sys.stderr)
    return 1


def cmd_add(args: argparse.Namespace) -> int:
    if args.source and len(args.paths) > 1:
        print("dotkeep: --as works with one file at a time", file=sys.stderr)
        return 2
    failed = False
    added = []
    for path in args.paths:
        try:
            added.append(add_file(args.repo, args.home, path, args.source))
        except AddError as e:
            print(f"dotkeep: {e}", file=sys.stderr)
            failed = True
        except OSError as e:
            print(f"dotkeep: cannot add {path}: {e.strerror or e}", file=sys.stderr)
            failed = True
    if added:
        add_entries(args.repo, added)
        for entry in added:
            print(f"{paint('added', 10)} {entry.target}  ->  {entry.source}")
    return 1 if failed else 0


def cmd_doctor(args: argparse.Namespace) -> int:
    checks = run_checks(args.repo, args.home)
    for c in checks:
        print(f"{paint(c.level, 5)} {c.message}")
    return 1 if any(c.level == "fail" for c in checks) else 0


# commands that need the manifest


def cmd_link(args: argparse.Namespace, manifest: Manifest) -> int:
    results = link_all(
        manifest, args.home, backup=not args.no_backup, dry_run=args.dry_run, mode=args.mode, force=args.force
    )
    would = {"linked": "link", "copied": "copy", "relinked": "relink", "backed-up": "back up"}
    for r in results:
        show("would " + would[r.action] if args.dry_run and r.action in would else r.action, r)
    summary(results)
    return 1 if any(r.action == "error" for r in results) else 0


def cmd_unlink(args: argparse.Namespace, manifest: Manifest) -> int:
    results = unlink_all(manifest, args.home, dry_run=args.dry_run, mode=args.mode, restore=args.restore)
    would = {"unlinked": "unlink", "restored": "restore"}
    for r in results:
        show("would " + would[r.action] if args.dry_run and r.action in would else r.action, r)
    return 1 if any(r.action == "error" for r in results) else 0


def cmd_remove(args: argparse.Namespace, manifest: Manifest) -> int:
    results = []
    for text in args.targets:
        path = user_path(text)
        target = path.absolute().relative_to(args.home.absolute()).as_posix() if path.is_absolute() else text
        results.append(remove_entry(manifest, args.home, target))

    done = {r.entry.target for r in results if r.action == "removed"}
    if done:
        remove_targets(args.repo, done)
        still_used = all_sources(args.repo)
        for r in results:
            source = args.repo / r.entry.source
            if r.action == "removed" and r.entry.source not in still_used and source.exists():
                remove(source)
    for r in results:
        show(r.action, r)
    return 1 if any(r.action == "error" for r in results) else 0


def cmd_list(args: argparse.Namespace, manifest: Manifest) -> int:
    width = max((len(entry.target) for entry in manifest.entries), default=0)
    for entry in manifest.entries:
        print(f"{entry.target:{width}}  ->  {entry.source}")
    return 0


def cmd_status(args: argparse.Namespace, manifest: Manifest) -> int:
    results = status_all(manifest, args.home, mode=args.mode)
    for r in results:
        show(r.action, r)
    summary(results)
    return 0 if all(r.action == "ok" for r in results) else 1


STANDALONE: dict[str, Callable[[argparse.Namespace], int]] = {
    "init": cmd_init,
    "add": cmd_add,
    "doctor": cmd_doctor,
}
WITH_MANIFEST: dict[str, Callable[[argparse.Namespace, Manifest], int]] = {
    "link": cmd_link,
    "unlink": cmd_unlink,
    "remove": cmd_remove,
    "list": cmd_list,
    "status": cmd_status,
}


# output


def show(label: str, r: Result) -> None:
    if quiet and label in ("ok", "skipped"):
        return
    print(f"{paint(label, 10)} {r.entry.target}" + (f"  ({r.detail})" if r.detail else ""))


def summary(results: list[Result]) -> None:
    """One line such as "3 ok, 1 missing" (nothing for an empty manifest)."""
    counts: dict[str, int] = {}
    for r in results:
        counts[r.action] = counts.get(r.action, 0) + 1
    if counts:
        print("\n" + ", ".join(f"{n} {action}" for action, n in counts.items()))


def paint(label: str, width: int) -> str:
    text = f"{label:{width}}"
    key = WOULD.get(label.removeprefix("would "), label) if label.startswith("would ") else label
    color = LABEL_COLORS.get(key)
    if not use_color or not color:
        return text
    return f"{color}{text}{RESET}"
