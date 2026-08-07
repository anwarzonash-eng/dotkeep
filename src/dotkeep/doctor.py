"""Checks behind `dotkeep doctor`."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .linker import BACKUP_DIR
from .manifest import MANIFEST_NAME, ManifestError, load


@dataclass
class Check:
    level: str  # "ok", "warn" or "fail"
    message: str


def symlinks_supported() -> bool:
    """Windows only allows symlinks with Developer Mode or admin rights, so try one."""
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp, "source")
        source.write_text("")
        try:
            os.symlink(source, Path(tmp, "link"))
        except (OSError, NotImplementedError):
            return False
    return True


def run_checks(repo: Path, home: Path, can_symlink: Callable[[], bool] = symlinks_supported) -> list[Check]:
    if not repo.is_dir():
        return [Check("fail", f"{repo} does not exist (create it with `dotkeep init`)")]
    try:
        manifest = load(repo)
    except ManifestError as e:
        return [Check("fail", str(e))]

    checks = [Check("ok", f"{MANIFEST_NAME} has {len(manifest.entries)} entries for this platform")]
    missing = [e.source for e in manifest.entries if not (repo / e.source).exists()]
    if missing:
        checks.append(Check("fail", "missing from the repo: " + ", ".join(missing)))

    if manifest.mode == "copy":
        checks.append(Check("ok", "copy mode, symlinks are not needed"))
    elif can_symlink():
        checks.append(Check("ok", "symlinks work here"))
    else:
        checks.append(Check(
            "fail",
            'cannot create symlinks; on Windows turn on Developer Mode, or set mode = "copy" under [settings]',
        ))

    if not (repo / ".git").exists():
        checks.append(Check("warn", f"{repo} is not a git repository, so changes are not tracked"))

    backups = home / BACKUP_DIR
    count = sum(1 for p in backups.rglob("*") if p.is_file()) if backups.is_dir() else 0
    if count:
        checks.append(Check("warn", f"{count} backed-up file(s) in {backups}; delete them once you have checked them"))
    return checks
