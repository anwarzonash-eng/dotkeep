"""Creating and checking the links in the home directory.

In "symlink" mode (the default) each target is a symlink into the repo. In
"copy" mode, for systems where symlinks are not available, the files are copied
and compared by content.
"""

from __future__ import annotations

import filecmp
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from .manifest import Entry, Manifest

BACKUP_DIR = ".dotkeep-backup"
WINDOWS_PREFIX = "\\\\?\\"


@dataclass
class Result:
    entry: Entry
    action: str  # "linked", "copied", "backed-up", "ok", "skipped" or "error"
    detail: str = ""


def link_all(
    manifest: Manifest, home: Path, backup: bool = True, dry_run: bool = False, mode: str | None = None
) -> list[Result]:
    mode = mode or manifest.mode
    return [link_one(manifest.repo, home, entry, backup, dry_run, mode) for entry in manifest.entries]


def link_one(
    repo: Path, home: Path, entry: Entry, backup: bool = True, dry_run: bool = False, mode: str = "symlink"
) -> Result:
    """Link (or copy) one entry. With dry_run, report what would happen without changing anything."""
    source = (repo / entry.source).absolute()
    target = home / entry.target
    if not source.exists():
        return Result(entry, "error", f"{entry.source} is missing from the repo")
    if target.is_symlink() and target.resolve() == source.resolve():
        return Result(entry, "ok")
    if target.is_symlink():
        return Result(entry, "skipped", "already a link to somewhere else")
    if mode == "copy" and target.exists() and same_content(source, target):
        return Result(entry, "ok")

    action, detail = ("copied" if mode == "copy" else "linked"), ""
    if target.exists():
        if not backup:
            return Result(entry, "skipped", "something is already there")
        saved = home / BACKUP_DIR / entry.target
        action, detail = "backed-up", f"old file moved to {saved}"
        if not dry_run:
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(target, saved)
    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        place(source, target, mode)
    return Result(entry, action, detail)


def place(source: Path, target: Path, mode: str) -> None:
    if mode == "copy":
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
    else:
        os.symlink(source, target, target_is_directory=source.is_dir())


def same_content(a: Path, b: Path) -> bool:
    if a.is_dir() != b.is_dir():
        return False
    if not a.is_dir():
        return filecmp.cmp(a, b, shallow=False)
    files_a = {p.relative_to(a) for p in a.rglob("*") if p.is_file()}
    files_b = {p.relative_to(b) for p in b.rglob("*") if p.is_file()}
    return files_a == files_b and all(filecmp.cmp(a / f, b / f, shallow=False) for f in files_a)


def status_all(manifest: Manifest, home: Path, mode: str | None = None) -> list[Result]:
    mode = mode or manifest.mode
    return [status_one(manifest.repo, home, entry, mode) for entry in manifest.entries]


def status_one(repo: Path, home: Path, entry: Entry, mode: str = "symlink") -> Result:
    """Check one entry without changing anything.

    Actions: "ok", "missing" (nothing at the target), "conflict" (a real file
    is in the way), "modified" (copy mode: the copy differs from the repo),
    "wrong-link" (a link to somewhere else) or "no-source".
    """
    source = (repo / entry.source).absolute()
    target = home / entry.target
    if not source.exists():
        return Result(entry, "no-source", f"{entry.source} is missing from the repo")
    if target.is_symlink():
        if target.resolve() == source.resolve():
            return Result(entry, "ok")
        return Result(entry, "wrong-link", f"points to {link_text(target)}")
    if target.exists():
        if mode == "copy":
            if same_content(source, target):
                return Result(entry, "ok")
            return Result(entry, "modified", "differs from the repo")
        return Result(entry, "conflict", "a file is in the way")
    return Result(entry, "missing")


def unlink_all(manifest: Manifest, home: Path, dry_run: bool = False) -> list[Result]:
    """Remove links that point into the repo. Anything else is left alone."""
    results = []
    for entry in manifest.entries:
        r = status_one(manifest.repo, home, entry)
        if r.action == "ok":
            if not dry_run:
                (home / entry.target).unlink()
            results.append(Result(entry, "unlinked"))
        else:
            results.append(Result(entry, "skipped", "not linked by dotkeep"))
    return results


def link_text(path: Path) -> str:
    """Where a link points, for messages, without the Windows extended-path prefix."""
    text = os.readlink(path)
    return text.removeprefix(WINDOWS_PREFIX)


class AddError(Exception):
    pass


def default_source(target: str) -> str:
    """Where a file goes in the repo: ".config/nvim/init.lua" -> "config/nvim/init.lua"."""
    parts = Path(target).parts
    return "/".join([parts[0].lstrip(".") or parts[0], *parts[1:]])


def add_file(repo: Path, home: Path, path: Path) -> Entry:
    """Move a file from home into the repo and link it back."""
    path = path.absolute()
    try:
        target = path.relative_to(home.absolute()).as_posix()
    except ValueError:
        raise AddError(f"{path} is not inside {home}") from None
    if path.is_symlink():
        raise AddError(f"{path} is already a link")
    if not path.exists():
        raise AddError(f"{path} does not exist")

    entry = Entry(target, default_source(target))
    dest = repo / entry.source
    if dest.exists():
        raise AddError(f"{entry.source} already exists in the repo")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(path, dest)
    os.symlink(dest.absolute(), path, target_is_directory=dest.is_dir())
    return entry
