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


def test_repo_path_expands_tilde(monkeypatch, tmp_path):
    from dotkeep.cli import build_parser

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    args = build_parser().parse_args(["--repo", "~/dots", "status"])
    assert args.repo == tmp_path / "dots"


def test_add_updates_manifest_then_status_is_ok(repo, home):
    write(repo / "dotkeep.toml", "[links]\n")
    write(home / ".vimrc", "set nu")
    assert main(["--repo", str(repo), "--home", str(home), "add", str(home / ".vimrc")]) == 0
    assert '".vimrc" = "vimrc"' in (repo / "dotkeep.toml").read_text()
    assert main(["--repo", str(repo), "--home", str(home), "status"]) == 0


def test_status_summary(repo, home, capsys):
    write(repo / "a")
    write(repo / "b")
    write(repo / "dotkeep.toml", '[links]\n".a" = "a"\n".b" = "b"\n".c" = "c"\n')
    main(["--repo", str(repo), "--home", str(home), "status"])
    assert capsys.readouterr().out.splitlines()[-1] == "2 missing, 1 no-source"


def test_list(repo, home, capsys):
    write(repo / "dotkeep.toml", '[links]\n".bashrc" = "bash/bashrc"\n".config/git/config" = "git/config"\n')
    assert main(["--repo", str(repo), "--home", str(home), "list"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        ".bashrc             ->  bash/bashrc",
        ".config/git/config  ->  git/config",
    ]


def test_repo_from_environment(monkeypatch, tmp_path):
    from dotkeep.cli import build_parser

    monkeypatch.setenv("DOTKEEP_REPO", str(tmp_path / "elsewhere"))
    assert build_parser().parse_args(["status"]).repo == tmp_path / "elsewhere"
    assert build_parser().parse_args(["--repo", str(tmp_path), "status"]).repo == tmp_path


def test_init(tmp_path, home, capsys):
    repo = tmp_path / "new" / "dotfiles"
    assert main(["--repo", str(repo), "--home", str(home), "init"]) == 0
    assert (repo / "dotkeep.toml").exists()
    assert main(["--repo", str(repo), "--home", str(home), "list"]) == 0
    assert main(["--repo", str(repo), "--home", str(home), "init"]) == 1
    assert "already exists" in capsys.readouterr().err


def test_init_template_works_with_add(tmp_path, home):
    repo = tmp_path / "dotfiles"
    main(["--repo", str(repo), "--home", str(home), "init"])
    write(home / ".zshrc", "x")
    main(["--repo", str(repo), "--home", str(home), "add", str(home / ".zshrc")])
    from dotkeep.manifest import Entry, load

    assert load(repo).entries == [Entry(".zshrc", "zshrc")]


def test_add_as_needs_one_path(repo, home, capsys):
    write(home / ".a")
    write(home / ".b")
    code = main(["--repo", str(repo), "--home", str(home), "add", str(home / ".a"), str(home / ".b"), "--as", "x"])
    assert code == 2
    assert "one file" in capsys.readouterr().err


def test_quiet_hides_ok_lines(repo, home, capsys):
    write(repo / "a")
    write(repo / "b")
    write(repo / "dotkeep.toml", '[links]\n".a" = "a"\n".b" = "b"\n')
    main(["--repo", str(repo), "--home", str(home), "link"])
    (home / ".b").unlink()
    capsys.readouterr()
    main(["--repo", str(repo), "--home", str(home), "-q", "status"])
    out = capsys.readouterr().out
    assert ".a" not in out
    assert "missing" in out and ".b" in out
