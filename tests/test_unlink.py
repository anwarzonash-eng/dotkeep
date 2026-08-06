from conftest import write
from dotkeep.linker import link_all, unlink_all
from dotkeep.manifest import Entry, Manifest


def test_removes_only_our_links(repo, home):
    write(repo / "a")
    write(repo / "b")
    m = Manifest(repo, [Entry(".a", "a"), Entry(".b", "b")])
    link_all(Manifest(repo, [m.entries[0]]), home)
    write(home / ".b", "mine")

    assert [r.action for r in unlink_all(m, home)] == ["unlinked", "skipped"]
    assert not (home / ".a").exists()
    assert (home / ".b").read_text() == "mine"
    assert (repo / "a").exists()


def test_dry_run(repo, home):
    write(repo / "a")
    m = Manifest(repo, [Entry(".a", "a")])
    link_all(m, home)
    unlink_all(m, home, dry_run=True)
    assert (home / ".a").is_symlink()


def test_restore_leaves_a_real_copy(repo, home):
    write(repo / "a", "content")
    m = Manifest(repo, [Entry(".a", "a")])
    link_all(m, home)
    assert [r.action for r in unlink_all(m, home, restore=True)] == ["restored"]
    assert not (home / ".a").is_symlink()
    assert (home / ".a").read_text() == "content"


def test_restore_folder(repo, home):
    write(repo / "nvim/init.lua", "x")
    m = Manifest(repo, [Entry(".config/nvim", "nvim")])
    link_all(m, home)
    unlink_all(m, home, restore=True)
    assert not (home / ".config/nvim").is_symlink()
    assert (home / ".config/nvim/init.lua").read_text() == "x"
