"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .linker import link_all
from .manifest import ManifestError, load


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dotkeep", description="Keep dotfiles in one folder and link them into place.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--repo", type=Path, default=Path.home() / "dotfiles", help="dotfiles folder (default: ~/dotfiles)")
    parser.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("link", help="link every file in the manifest into place")
    args = parser.parse_args(argv)

    try:
        manifest = load(args.repo)
    except ManifestError as e:
        print(f"dotkeep: {e}", file=sys.stderr)
        return 1

    if args.command == "link":
        failed = False
        for r in link_all(manifest, args.home):
            print(f"{r.action:8} {r.entry.target}" + (f"  ({r.detail})" if r.detail else ""))
            failed |= r.action == "error"
        return 1 if failed else 0
    return 0
