from conftest import write
from dotkeep.linker import link_all
from dotkeep.manifest import Entry, Manifest


def manifest(repo, **links):
    return Manifest(repo, [Entry(t, s) for t, s in links.items()])


def test_creates_symlink(repo, home):
    write(repo / "bashrc", "export EDITOR=vim\n")
    [r] = link_all(manifest(repo, **{".bashrc": "bashrc"}), home)
    assert r.action == "linked"
    assert (home / ".bashrc").is_symlink()
    assert (home / ".bashrc").read_text() == "export EDITOR=vim\n"


def test_second_run_is_ok(repo, home):
    write(repo / "bashrc")
    m = manifest(repo, **{".bashrc": "bashrc"})
    link_all(m, home)
    assert [r.action for r in link_all(m, home)] == ["ok"]


def test_missing_source_is_an_error(repo, home):
    [r] = link_all(manifest(repo, **{".bashrc": "bashrc"}), home)
    assert r.action == "error"
    assert not (home / ".bashrc").exists()


def test_does_not_touch_existing_file(repo, home):
    write(repo / "bashrc", "new")
    write(home / ".bashrc", "old")
    [r] = link_all(manifest(repo, **{".bashrc": "bashrc"}), home)
    assert r.action == "skipped"
    assert (home / ".bashrc").read_text() == "old"
