from pathlib import Path

import pytest


@pytest.fixture
def home(tmp_path: Path) -> Path:
    path = tmp_path / "home"
    path.mkdir()
    return path


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = tmp_path / "dotfiles"
    path.mkdir()
    return path


def write(path: Path, text: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
