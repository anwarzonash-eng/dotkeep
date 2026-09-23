from conftest import write
from dotkeep.cli import main
from dotkeep.manifest import load


def run(repo, home, *args):
    return main(["--repo", str(repo), "--home", str(home), *args])


def test_remove_puts_file_back_and_cleans_repo(repo, home):
    write(repo / "dotkeep.toml", "[links]\n")
    write(home / ".vimrc", "set nu")
    write(home / ".bashrc", "x")
    run(repo, home, "add", str(home / ".vimrc"), str(home / ".bashrc"))

    assert run(repo, home, "remove", str(home / ".vimrc")) == 0
    assert not (home / ".vimrc").is_symlink()
    assert (home / ".vimrc").read_text() == "set nu"
    assert not (repo / "vimrc").exists()
    assert [e.target for e in load(repo).entries] == [".bashrc"]


def test_remove_by_target_name(repo, home):
    write(repo / "dotkeep.toml", "[links]\n")
    write(home / ".zshrc", "z")
    run(repo, home, "add", str(home / ".zshrc"))
    assert run(repo, home, "remove", ".zshrc") == 0
    assert load(repo).entries == []


def test_shared_source_is_kept(repo, home):
    write(repo / "vscode/settings.json", "{}")
    write(repo / "dotkeep.toml", '[links]\n".a" = "vscode/settings.json"\n".b" = "vscode/settings.json"\n')
    run(repo, home, "link")
    run(repo, home, "remove", ".a")
    assert (repo / "vscode/settings.json").exists()
    assert (home / ".a").read_text() == "{}"


def test_unknown_target(repo, home, capsys):
    write(repo / "dotkeep.toml", "[links]\n")
    assert run(repo, home, "remove", ".nope") == 1
    assert "not in the manifest" in capsys.readouterr().out
