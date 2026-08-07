from conftest import write
from dotkeep.doctor import run_checks


def levels(checks):
    return [c.level for c in checks]


def test_missing_repo(tmp_path, home):
    [c] = run_checks(tmp_path / "nope", home)
    assert c.level == "fail" and "dotkeep init" in c.message


def test_healthy_setup(repo, home):
    (repo / ".git").mkdir()
    write(repo / "bashrc")
    write(repo / "dotkeep.toml", '[links]\n".bashrc" = "bashrc"\n')
    assert levels(run_checks(repo, home, can_symlink=lambda: True)) == ["ok", "ok"]


def test_reports_problems(repo, home):
    write(repo / "dotkeep.toml", '[links]\n".bashrc" = "bashrc"\n')
    write(home / ".dotkeep-backup" / ".bashrc", "old")
    checks = run_checks(repo, home, can_symlink=lambda: False)
    assert levels(checks) == ["ok", "fail", "fail", "warn", "warn"]
    assert "Developer Mode" in checks[2].message


def test_copy_mode_does_not_need_symlinks(repo, home):
    (repo / ".git").mkdir()
    write(repo / "dotkeep.toml", '[settings]\nmode = "copy"\n')
    checks = run_checks(repo, home, can_symlink=lambda: False)
    assert levels(checks) == ["ok", "ok"]
