import pytest

from conftest import write
from dotkeep.linker import AddError, add_file, default_source


def test_default_source():
    assert default_source(".vimrc") == "vimrc"
    assert default_source(".config/nvim/init.lua") == "config/nvim/init.lua"
    assert default_source("bin/tool") == "bin/tool"


def test_moves_and_links(repo, home):
    f = write(home / ".config" / "nvim" / "init.lua", "vim.o.number = true")
    entry = add_file(repo, home, f)
    assert entry.target == ".config/nvim/init.lua"
    assert (repo / "config/nvim/init.lua").read_text() == "vim.o.number = true"
    assert f.is_symlink()
    assert f.read_text() == "vim.o.number = true"


def test_refuses_outside_home(repo, home, tmp_path):
    with pytest.raises(AddError, match="not inside"):
        add_file(repo, home, write(tmp_path / "elsewhere"))


def test_refuses_missing_and_links(repo, home, tmp_path):
    with pytest.raises(AddError, match="does not exist"):
        add_file(repo, home, home / ".nope")
    (home / ".link").symlink_to(write(tmp_path / "x"))
    with pytest.raises(AddError, match="already a link"):
        add_file(repo, home, home / ".link")


def test_refuses_to_overwrite_repo_file(repo, home):
    write(repo / "vimrc", "repo")
    with pytest.raises(AddError, match="already exists"):
        add_file(repo, home, write(home / ".vimrc", "home"))
    assert (home / ".vimrc").read_text() == "home"


def test_add_as(repo, home):
    f = write(home / ".config" / "Code" / "User" / "settings.json", "{}")
    entry = add_file(repo, home, f, "vscode/settings.json")
    assert entry.source == "vscode/settings.json"
    assert (repo / "vscode/settings.json").read_text() == "{}"
    assert f.read_text() == "{}"


def test_refuses_files_inside_the_repo(home):
    repo = home / "dotfiles"
    write(repo / "notes.txt")
    with pytest.raises(AddError, match="inside the repo"):
        add_file(repo, home, repo / "notes.txt")
    with pytest.raises(AddError, match="inside the repo"):
        add_file(repo, home, repo)
    assert (repo / "notes.txt").exists()
