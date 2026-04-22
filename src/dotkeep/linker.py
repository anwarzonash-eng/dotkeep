"""Creating the links in the home directory."""

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


def link_all(manifest: Manifest, home: Path, backup: bool = True) -> list[Result]:
    return [link_one(manifest.repo, home, entry, backup) for entry in manifest.entries]


def link_one(repo: Path, home: Path, entry: Entry, backup: bool = True) -> Result:
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
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(target, saved)
        action, detail = "backed-up", f"old file moved to {saved}"
    os.symlink(source, target, target_is_directory=source.is_dir())
    return Result(entry, action, detail)
