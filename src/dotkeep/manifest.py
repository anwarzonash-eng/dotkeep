"""Reading the dotkeep.toml manifest."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

MANIFEST_NAME = "dotkeep.toml"


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


def load(repo: Path) -> Manifest:
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

    entries = []
    for target, source in links.items():
        if not isinstance(source, str):
            raise ManifestError(f'links."{target}" must be a string')
        entries.append(Entry(target, source))
    return Manifest(repo, entries)
