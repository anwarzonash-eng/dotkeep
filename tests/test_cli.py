from conftest import write
from dotkeep.cli import main


def setup(repo):
    write(repo / "bashrc", "x")
    write(repo / "dotkeep.toml", '[links]\n".bashrc" = "bashrc"\n')


def test_link_then_status(repo, home, capsys):
    setup(repo)
    assert main(["--repo", str(repo), "--home", str(home), "status"]) == 1
    assert "missing" in capsys.readouterr().out
    assert main(["--repo", str(repo), "--home", str(home), "link"]) == 0
    assert main(["--repo", str(repo), "--home", str(home), "status"]) == 0
    assert "ok" in capsys.readouterr().out


def test_dry_run_output(repo, home, capsys):
    setup(repo)
    main(["--repo", str(repo), "--home", str(home), "link", "--dry-run"])
    assert "would link" in capsys.readouterr().out
    assert not (home / ".bashrc").exists()


def test_missing_manifest(repo, home, capsys):
    assert main(["--repo", str(repo), "--home", str(home), "status"]) == 1
    assert "no dotkeep.toml" in capsys.readouterr().err
