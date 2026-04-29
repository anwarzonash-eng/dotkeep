"""Creating and checking the links in the home directory."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from .manifest import Entry, Manifest

BACKUP_DIR = ".dotkeep-backup"


@dataclass
class Result:
    entry: Entry
    action: str  # "linked", "backed-up", "ok", "skipped" or "error"
    detail: str = ""


def link_all(manifest: Manifest, home: Path, backup: bool = True, dry_run: bool = False) -> list[Result]:
    return [link_one(manifest.repo, home, entry, backup, dry_run) for entry in manifest.entries]


def link_one(repo: Path, home: Path, entry: Entry, backup: bool = True, dry_run: bool = False) -> Result:
    """Link one entry. With dry_run, report what would happen without changing anything."""
    source = (repo / entry.source).absolute()
    target = home / entry.target
    if not source.exists():
        return Result(entry, "error", f"{entry.source} is missing from the repo")
    if target.is_symlink() and target.resolve() == source.resolve():
        return Result(entry, "ok")
    if target.is_symlink():
        return Result(entry, "skipped", "already a link to somewhere else")

    action, detail = "linked", ""
    if target.exists():
        if not backup:
            return Result(entry, "skipped", "something is already there")
        saved = home / BACKUP_DIR / entry.target
        action, detail = "backed-up", f"old file moved to {saved}"
        if not dry_run:
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(target, saved)
    if not dry_run:
        os.symlink(source, target, target_is_directory=source.is_dir())
    return Result(entry, action, detail)


def status_all(manifest: Manifest, home: Path) -> list[Result]:
    return [status_one(manifest.repo, home, entry) for entry in manifest.entries]


def status_one(repo: Path, home: Path, entry: Entry) -> Result:
    """Check one entry without changing anything.

    Actions: "ok", "missing" (nothing at the target), "conflict" (a real file
    is in the way), "wrong-link" (a link to somewhere else) or "no-source".
    """
    source = (repo / entry.source).absolute()
    target = home / entry.target
    if not source.exists():
        return Result(entry, "no-source", f"{entry.source} is missing from the repo")
    if target.is_symlink():
        if target.resolve() == source.resolve():
            return Result(entry, "ok")
        return Result(entry, "wrong-link", f"points to {os.readlink(target)}")
    if target.exists():
        return Result(entry, "conflict", "a file is in the way")
    return Result(entry, "missing")
