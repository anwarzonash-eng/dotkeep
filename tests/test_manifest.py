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
