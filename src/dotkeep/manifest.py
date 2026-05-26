"""Reading the dotkeep.toml manifest."""

from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

MANIFEST_NAME = "dotkeep.toml"
PLATFORMS = ("linux", "macos", "windows")


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
    return Manifest(repo, [Entry(t, s) for t, s in found.items()])


def read_links(table: dict, where: str) -> dict[str, str]:
    for target, source in table.items():
        if not isinstance(source, str):
            raise ManifestError(f'{where}."{target}" must be a string')
    return dict(table)
