import pytest

from conftest import write
from dotkeep.manifest import Entry, ManifestError, load


def test_loads_links(repo):
    write(repo / "dotkeep.toml", '[links]\n".bashrc" = "bash/bashrc"\n".gitconfig" = "git/config"\n')
    m = load(repo)
    assert m.entries == [Entry(".bashrc", "bash/bashrc"), Entry(".gitconfig", "git/config")]


def test_empty_manifest_has_no_entries(repo):
    write(repo / "dotkeep.toml", "")
    assert load(repo).entries == []


def test_missing_manifest(repo):
    with pytest.raises(ManifestError, match="no dotkeep.toml"):
        load(repo)


def test_invalid_toml(repo):
    write(repo / "dotkeep.toml", "[links\n")
    with pytest.raises(ManifestError):
        load(repo)


def test_source_must_be_a_string(repo):
    write(repo / "dotkeep.toml", '[links]\n".bashrc" = 3\n')
    with pytest.raises(ManifestError, match="must be a string"):
        load(repo)


MULTI = """
[links]
".bashrc" = "bash/bashrc"
".config/Code/User/settings.json" = "vscode/settings.json"

[links.windows]
"AppData/Roaming/Code/User/settings.json" = "vscode/settings.json"
".bashrc" = "bash/bashrc-gitbash"

[links.macos]
"Library/Application Support/Code/User/settings.json" = "vscode/settings.json"
"""


def test_platform_sections(repo):
    write(repo / "dotkeep.toml", MULTI)
    linux = {e.target: e.source for e in load(repo, "linux").entries}
    assert linux == {".bashrc": "bash/bashrc", ".config/Code/User/settings.json": "vscode/settings.json"}

    windows = {e.target: e.source for e in load(repo, "windows").entries}
    assert windows[".bashrc"] == "bash/bashrc-gitbash"
    assert "AppData/Roaming/Code/User/settings.json" in windows
    assert "Library/Application Support/Code/User/settings.json" not in windows


def test_unknown_platform_section(repo):
    write(repo / "dotkeep.toml", '[links.beos]\n".x" = "x"\n')
    with pytest.raises(ManifestError, match="unknown platform"):
        load(repo)
