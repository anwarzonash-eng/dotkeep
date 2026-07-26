from conftest import write
from dotkeep.linker import link_all, status_all
from dotkeep.manifest import Entry, Manifest


def test_each_state(repo, home, tmp_path):
    for name in ("a", "b", "c", "d"):
        write(repo / name)
    m = Manifest(repo, [Entry(".a", "a"), Entry(".b", "b"), Entry(".c", "c"), Entry(".d", "d"), Entry(".e", "e")])
    link_all(Manifest(repo, [m.entries[0]]), home)
    write(home / ".c", "in the way")
    (home / ".d").symlink_to(write(tmp_path / "elsewhere"))

    assert [r.action for r in status_all(m, home)] == ["ok", "missing", "conflict", "wrong-link", "no-source"]


def test_link_text_strips_windows_prefix(monkeypatch, tmp_path):
    from dotkeep import linker

    monkeypatch.setattr(linker.os, "readlink", lambda p: r"\\?\C:\Users\me\x")
    assert linker.link_text(tmp_path) == r"C:\Users\me\x"
