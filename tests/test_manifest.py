import pytest

from conftest import write
from dotkeep.manifest import Entry, ManifestError, add_entries, load


def test_loads_links(repo):
    write(repo / "dotkeep.toml", '[links]\n".bashrc" = "bash/bashrc"\n".gitconfig" = "git/config"\n')
    m = load(repo)
    assert m.entries == [Entry(".bashrc", "bash/bashrc"), Entry(".gitconfig", "git/config")]


def test_empty_manifest_has_no_entries(repo):
    write(repo / "dotkeep.toml", "")
    assert load(repo).entries == []


def test_missing_manifest(repo):
    with pytest.raises(ManifestError, match="no dotkeep.toml"):
        load(repo)


def test_invalid_toml(repo):
    write(repo / "dotkeep.toml", "[links\n")
    with pytest.raises(ManifestError):
        load(repo)


def test_source_must_be_a_string(repo):
    write(repo / "dotkeep.toml", '[links]\n".bashrc" = 3\n')
    with pytest.raises(ManifestError, match="must be a string"):
        load(repo)


MULTI = """
[links]
".bashrc" = "bash/bashrc"
".config/Code/User/settings.json" = "vscode/settings.json"

[links.windows]
"AppData/Roaming/Code/User/settings.json" = "vscode/settings.json"
".bashrc" = "bash/bashrc-gitbash"

[links.macos]
"Library/Application Support/Code/User/settings.json" = "vscode/settings.json"
"""


def test_platform_sections(repo):
    write(repo / "dotkeep.toml", MULTI)
    linux = {e.target: e.source for e in load(repo, "linux").entries}
    assert linux == {".bashrc": "bash/bashrc", ".config/Code/User/settings.json": "vscode/settings.json"}

    windows = {e.target: e.source for e in load(repo, "windows").entries}
    assert windows[".bashrc"] == "bash/bashrc-gitbash"
    assert "AppData/Roaming/Code/User/settings.json" in windows
    assert "Library/Application Support/Code/User/settings.json" not in windows


def test_unknown_platform_section(repo):
    write(repo / "dotkeep.toml", '[links.beos]\n".x" = "x"\n')
    with pytest.raises(ManifestError, match="unknown platform"):
        load(repo)


def test_add_entries_keeps_comments_and_other_tables(repo):
    write(repo / "dotkeep.toml", '# my dotfiles\n[links]\n".bashrc" = "bashrc"  # shell\n\n[links.windows]\n".x" = "x"\n')
    add_entries(repo, [Entry(".vimrc", "vimrc")])
    text = (repo / "dotkeep.toml").read_text()
    assert text.startswith("# my dotfiles\n[links]\n\".bashrc\" = \"bashrc\"  # shell\n\".vimrc\" = \"vimrc\"\n\n[links.windows]")
    assert Entry(".vimrc", "vimrc") in load(repo, "linux").entries


def test_add_entries_creates_manifest(repo):
    add_entries(repo, [Entry(".config/My App/conf", 'config/My App/conf')])
    assert load(repo).entries == [Entry(".config/My App/conf", "config/My App/conf")]


def test_add_entries_goes_above_trailing_comments(repo):
    write(repo / "dotkeep.toml", '[links]\n".a" = "a"\n\n# [links.windows]\n# ".b" = "b"\n')
    add_entries(repo, [Entry(".c", "c")])
    assert (repo / "dotkeep.toml").read_text() == '[links]\n".a" = "a"\n".c" = "c"\n\n# [links.windows]\n# ".b" = "b"\n'


def test_add_entries_into_empty_table(repo):
    write(repo / "dotkeep.toml", "[links]\n\n# comment\n")
    add_entries(repo, [Entry(".c", "c")])
    assert (repo / "dotkeep.toml").read_text() == '[links]\n".c" = "c"\n\n# comment\n'


@pytest.mark.parametrize(
    "line, message",
    [
        ('"/etc/passwd" = "x"', "must be relative"),
        ('"C:/Users/me/.x" = "x"', "must be relative"),
        ('"~/.bashrc" = "bashrc"', "without ~"),
        ('"../outside" = "x"', '".."'),
        ('".bashrc" = "../../secret"', '".."'),
        ('".bashrc" = "a\\\\..\\\\..\\\\b"', '".."'),
        ('"" = "x"', "is empty"),
    ],
)
def test_paths_must_stay_inside(repo, line, message):
    write(repo / "dotkeep.toml", f"[links]\n{line}\n")
    with pytest.raises(ManifestError, match=message):
        load(repo)
