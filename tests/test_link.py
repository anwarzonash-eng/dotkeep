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


def test_backs_up_existing_file(repo, home):
    write(repo / "bashrc", "new")
    write(home / ".bashrc", "old")
    [r] = link_all(manifest(repo, **{".bashrc": "bashrc"}), home)
    assert r.action == "backed-up"
    assert (home / ".bashrc").read_text() == "new"
    assert (home / ".dotkeep-backup" / ".bashrc").read_text() == "old"


def test_no_backup_leaves_existing_file(repo, home):
    write(repo / "bashrc", "new")
    write(home / ".bashrc", "old")
    [r] = link_all(manifest(repo, **{".bashrc": "bashrc"}), home, backup=False)
    assert r.action == "skipped"
    assert (home / ".bashrc").read_text() == "old"


def test_leaves_foreign_symlink_alone(repo, home, tmp_path):
    write(repo / "bashrc", "new")
    other = write(tmp_path / "other", "other")
    (home / ".bashrc").symlink_to(other)
    [r] = link_all(manifest(repo, **{".bashrc": "bashrc"}), home)
    assert r.action == "skipped"
    assert (home / ".bashrc").resolve() == other.resolve()


def test_dry_run_changes_nothing(repo, home):
    write(repo / "bashrc", "new")
    write(repo / "vimrc", "set nu")
    write(home / ".bashrc", "old")
    results = link_all(manifest(repo, **{".bashrc": "bashrc", ".vimrc": "vimrc"}), home, dry_run=True)
    assert [r.action for r in results] == ["backed-up", "linked"]
    assert (home / ".bashrc").read_text() == "old"
    assert not (home / ".vimrc").exists()
    assert not (home / ".dotkeep-backup").exists()


def test_creates_missing_parent_folders(repo, home):
    write(repo / "config/nvim/init.lua", "x")
    [r] = link_all(manifest(repo, **{".config/nvim/init.lua": "config/nvim/init.lua"}), home)
    assert r.action == "linked"
    assert (home / ".config/nvim/init.lua").read_text() == "x"
