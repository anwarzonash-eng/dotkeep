"""Reading the dotkeep.toml manifest."""

from __future__ import annotations

import json
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

MANIFEST_NAME = "dotkeep.toml"
PLATFORMS = ("linux", "macos", "windows")
MODES = ("symlink", "copy")


def current_platform() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


class ManifestError(Exception):
    pass


@dataclass(frozen=True)
class Entry:
    target: str  # where the file should appear, relative to home (".bashrc")
    source: str  # where it lives in the repo ("bash/bashrc")


@dataclass
class Manifest:
    repo: Path
    entries: list[Entry]
    mode: str = "symlink"


def load(repo: Path, platform: str | None = None) -> Manifest:
    """Load the manifest. Entries in [links.<platform>] are added for the
    current platform and override [links] entries with the same target."""
    platform = platform or current_platform()
    path = repo / MANIFEST_NAME
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ManifestError(f"no {MANIFEST_NAME} in {repo}") from None
    except tomllib.TOMLDecodeError as e:
        raise ManifestError(f"{path}: {e}") from None

    settings = data.get("settings", {})
    mode = settings.get("mode", "symlink") if isinstance(settings, dict) else None
    if mode not in MODES:
        raise ManifestError(f"settings.mode must be one of {', '.join(MODES)}")

    links = data.get("links", {})
    if not isinstance(links, dict):
        raise ManifestError("[links] must be a table")

    found: dict[str, str] = {}
    overrides: dict[str, str] = {}
    for key, value in links.items():
        if isinstance(value, dict):
            if key not in PLATFORMS:
                raise ManifestError(f"[links.{key}]: unknown platform, use one of {', '.join(PLATFORMS)}")
            if key == platform:
                overrides = read_links(value, f"links.{key}")
        else:
            found.update(read_links({key: value}, "links"))
    found.update(overrides)
    return Manifest(repo, [Entry(t, s) for t, s in found.items()], mode)


def read_links(table: dict[str, object], where: str) -> dict[str, str]:
    links: dict[str, str] = {}
    for target, source in table.items():
        if not isinstance(source, str):
            raise ManifestError(f'{where}."{target}" must be a string')
        check_relative(target, f'{where}: target "{target}"', "your home folder")
        check_relative(source, f'{where}."{target}": source "{source}"', "the repo")
        links[target] = source
    return links


def check_relative(path: str, what: str, base: str) -> None:
    """Paths must stay inside their base folder: no absolute paths, no "..", no "~"."""
    if not path.strip():
        raise ManifestError(f"{what} is empty")
    if PurePosixPath(path).is_absolute() or PureWindowsPath(path).is_absolute() or PureWindowsPath(path).drive:
        raise ManifestError(f"{what} must be relative to {base}")
    if path.startswith("~"):
        raise ManifestError(f"{what} must be relative to {base}, without ~")
    if ".." in PureWindowsPath(path).parts:
        raise ManifestError(f'{what} must not use ".."')


def add_entries(repo: Path, entries: list[Entry]) -> None:
    """Append entries to the [links] table.

    The file is edited as text so comments and layout stay as they are.
    """
    path = repo / MANIFEST_NAME
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    new = [f"{quote(e.target)} = {quote(e.source)}" for e in entries]

    start = next((i for i, line in enumerate(lines) if line.strip() == "[links]"), None)
    if start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines += ["[links]", *new]
    else:
        # insert after the last key in the table, before any trailing blank or comment lines
        end = start + 1
        i = start + 1
        while i < len(lines) and not lines[i].lstrip().startswith("["):
            if lines[i].strip() and not lines[i].lstrip().startswith("#"):
                end = i + 1
            i += 1
        lines[end:end] = new
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def quote(text: str) -> str:
    # a JSON string is also a valid TOML basic string
    return json.dumps(text, ensure_ascii=False)


TEMPLATE = """\
# dotkeep manifest: target (relative to home) = source (relative to this folder)
# Add files with `dotkeep add ~/.bashrc`, then `dotkeep link` on other machines.

[links]

# Entries that only apply on one platform (linux, macos, windows):
# [links.windows]
# "AppData/Roaming/Code/User/settings.json" = "vscode/settings.json"
"""


def init(repo: Path) -> bool:
    """Create the repo folder and a starter manifest. Returns False if one already exists."""
    if repo.exists() and not repo.is_dir():
        raise ManifestError(f"{repo} exists but is not a folder")
    path = repo / MANIFEST_NAME
    if path.exists():
        return False
    repo.mkdir(parents=True, exist_ok=True)
    path.write_text(TEMPLATE, encoding="utf-8")
    return True


def remove_targets(repo: Path, targets: set[str]) -> int:
    """Delete the lines for these targets from every table. Returns how many lines went."""
    path = repo / MANIFEST_NAME
    kept, removed = [], 0
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith(("#", "[")) and "=" in stripped:
            try:
                key = next(iter(tomllib.loads(line)), None)
            except tomllib.TOMLDecodeError:
                key = None
            if key in targets:
                removed += 1
                continue
        kept.append(line)
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    return removed


def all_sources(repo: Path) -> set[str]:
    """Every source named in the manifest, on any platform."""
    data = tomllib.loads((repo / MANIFEST_NAME).read_text(encoding="utf-8"))
    sources: set[str] = set()
    for value in data.get("links", {}).values():
        if isinstance(value, str):
            sources.add(value)
        elif isinstance(value, dict):
            sources.update(v for v in value.values() if isinstance(v, str))
    return sources
