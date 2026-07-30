import pytest

from conftest import write
from dotkeep.linker import link_all, status_all, unlink_all
from dotkeep.manifest import Entry, Manifest, ManifestError, load


def copy_manifest(repo, *entries):
    return Manifest(repo, list(entries), mode="copy")


def test_mode_from_settings(repo):
    write(repo / "dotkeep.toml", '[settings]\nmode = "copy"\n\n[links]\n')
    assert load(repo).mode == "copy"
    write(repo / "dotkeep.toml", '[settings]\nmode = "hardlink"\n')
    with pytest.raises(ManifestError, match="settings.mode"):
        load(repo)


def test_copies_file_and_reports_ok(repo, home):
    write(repo / "bashrc", "x")
    m = copy_manifest(repo, Entry(".bashrc", "bashrc"))
    assert [r.action for r in link_all(m, home)] == ["copied"]
    assert not (home / ".bashrc").is_symlink()
    assert (home / ".bashrc").read_text() == "x"
    assert [r.action for r in link_all(m, home)] == ["ok"]
    assert [r.action for r in status_all(m, home)] == ["ok"]


def test_modified_copy(repo, home):
    write(repo / "bashrc", "x")
    m = copy_manifest(repo, Entry(".bashrc", "bashrc"))
    link_all(m, home)
    (home / ".bashrc").write_text("changed")
    assert [r.action for r in status_all(m, home)] == ["modified"]


def test_copies_folders(repo, home):
    write(repo / "nvim/init.lua", "a")
    write(repo / "nvim/lua/plugins.lua", "b")
    m = copy_manifest(repo, Entry(".config/nvim", "nvim"))
    link_all(m, home)
    assert (home / ".config/nvim/lua/plugins.lua").read_text() == "b"
    assert [r.action for r in status_all(m, home)] == ["ok"]
    write(home / ".config/nvim/extra.lua", "c")
    assert [r.action for r in status_all(m, home)] == ["modified"]


def test_mode_argument_overrides_manifest(repo, home):
    write(repo / "bashrc", "x")
    m = Manifest(repo, [Entry(".bashrc", "bashrc")])
    link_all(m, home, mode="copy")
    assert not (home / ".bashrc").is_symlink()


def test_unlink_removes_unchanged_copies_only(repo, home):
    write(repo / "a", "a")
    write(repo / "nvim/init.lua", "x")
    write(repo / "b", "b")
    m = copy_manifest(repo, Entry(".a", "a"), Entry(".config/nvim", "nvim"), Entry(".b", "b"))
    link_all(m, home)
    (home / ".b").write_text("edited")

    assert [r.action for r in unlink_all(m, home)] == ["unlinked", "unlinked", "skipped"]
    assert not (home / ".a").exists()
    assert not (home / ".config/nvim").exists()
    assert (home / ".b").read_text() == "edited"
