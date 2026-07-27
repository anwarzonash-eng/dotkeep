"""Reading the dotkeep.toml manifest."""

from __future__ import annotations

import json
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

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


def read_links(table: dict, where: str) -> dict[str, str]:
    for target, source in table.items():
        if not isinstance(source, str):
            raise ManifestError(f'{where}."{target}" must be a string')
    return dict(table)


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
    path = repo / MANIFEST_NAME
    if path.exists():
        return False
    repo.mkdir(parents=True, exist_ok=True)
    path.write_text(TEMPLATE, encoding="utf-8")
    return True
