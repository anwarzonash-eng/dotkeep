"""Whole folders can be entries too (for example ~/.config/nvim)."""

from conftest import write
from dotkeep.linker import add_file, link_all, status_all, unlink_all
from dotkeep.manifest import Entry, Manifest


def test_add_folder(repo, home):
    write(home / ".config/nvim/init.lua", "a")
    write(home / ".config/nvim/lua/keys.lua", "b")
    entry = add_file(repo, home, home / ".config/nvim")
    assert entry == Entry(".config/nvim", "config/nvim")
    assert (home / ".config/nvim").is_symlink()
    assert (home / ".config/nvim/lua/keys.lua").read_text() == "b"
    assert (repo / "config/nvim/init.lua").read_text() == "a"


def test_link_status_unlink_folder(repo, home):
    write(repo / "nvim/init.lua", "a")
    m = Manifest(repo, [Entry(".config/nvim", "nvim")])
    assert [r.action for r in link_all(m, home)] == ["linked"]
    assert [r.action for r in status_all(m, home)] == ["ok"]
    assert [r.action for r in unlink_all(m, home)] == ["unlinked"]
    assert not (home / ".config/nvim").exists()
    assert (repo / "nvim/init.lua").exists()


def test_existing_folder_is_backed_up(repo, home):
    write(repo / "nvim/init.lua", "new")
    write(home / ".config/nvim/init.lua", "old")
    m = Manifest(repo, [Entry(".config/nvim", "nvim")])
    assert [r.action for r in link_all(m, home)] == ["backed-up"]
    assert (home / ".dotkeep-backup/.config/nvim/init.lua").read_text() == "old"
    assert (home / ".config/nvim/init.lua").read_text() == "new"
