"""Creating the links in the home directory."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .manifest import Entry, Manifest


@dataclass
class Result:
    entry: Entry
    action: str  # "linked", "ok", "skipped" or "error"
    detail: str = ""


def link_all(manifest: Manifest, home: Path) -> list[Result]:
    return [link_one(manifest.repo, home, entry) for entry in manifest.entries]


def link_one(repo: Path, home: Path, entry: Entry) -> Result:
    source = (repo / entry.source).absolute()
    target = home / entry.target
    if not source.exists():
        return Result(entry, "error", f"{entry.source} is missing from the repo")
    if target.is_symlink() and target.resolve() == source.resolve():
        return Result(entry, "ok")
    if target.exists() or target.is_symlink():
        return Result(entry, "skipped", "something is already there")
    os.symlink(source, target, target_is_directory=source.is_dir())
    return Result(entry, "linked")
