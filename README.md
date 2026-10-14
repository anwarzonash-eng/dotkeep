# dotkeep

Keep your dotfiles in one git folder and link them into place on every machine.

You keep the real files in a folder such as `~/dotfiles`, list them in `dotkeep.toml`, and `dotkeep link` puts symlinks in your home folder that point back to it. On a new machine it is `git clone` + `dotkeep link`. It works on Linux, macOS and Windows, and has a copy mode for Windows machines where symlinks are not allowed.

It is for people who want something smaller than a full dotfiles framework: one TOML file, no templates, no daemon. Written in Python 3.11+ with the standard library only.

## Install

```bash
git clone https://github.com/anwarzonash-eng/dotkeep.git
cd dotkeep
pip install -e .
dotkeep --version
```

## Quick start

```bash
dotkeep init                                    # creates ~/dotfiles/dotkeep.toml
dotkeep add ~/.bashrc ~/.config/nvim            # move files (or folders) into the repo, link them back
cd ~/dotfiles && git init && git add . && git commit -m "dotfiles"

# on another machine
git clone <your dotfiles repo> ~/dotfiles
dotkeep link --dry-run                          # see what would change
dotkeep link                                    # create the links
```

Try it without touching your home folder using the example repo:

```bash
dotkeep --repo examples/dotfiles --home /tmp/fake-home link
```

## Commands

| Command | What it does |
| --- | --- |
| `init` | Create the repo folder and a starter `dotkeep.toml` |
| `add PATH... [--as REPO_PATH]` | Move files or folders into the repo, link them back, and add them to the manifest |
| `link [-n] [-f] [--no-backup]` | Link every entry into place (`-n` dry run, `-f` replace links that point elsewhere) |
| `status` | `ok`, `missing`, `conflict`, `wrong-link`, `modified` or `no-source` for each entry; exits `1` if anything is not `ok` |
| `list` | Entries for the current platform |
| `unlink [-n] [--restore]` | Remove the links; `--restore` leaves real copies behind |
| `remove PATH...` | Stop tracking a file: real copy back in home, gone from the repo and the manifest |
| `doctor` | Check symlink support, missing sources, git and leftover backups |

Global options: `--repo PATH` (or `DOTKEEP_REPO`, default `~/dotfiles`), `--mode symlink|copy`, `-q/--quiet`, `--no-color` (or `NO_COLOR`).

## The manifest

```toml
[settings]
mode = "symlink"        # or "copy"

[links]
".bashrc" = "bash/bashrc"
".config/nvim" = "nvim"

# only on Windows; same target names override the ones above
[links.windows]
"AppData/Local/nvim" = "nvim"

[links.macos]
"Library/Application Support/Code/User/settings.json" = "vscode/settings.json"
```

Targets are relative to your home folder, sources are relative to the repo. Both must stay inside their folder: no absolute paths, `~` or `..`. `add` edits the file as text, so your comments stay.

## Safety

- A real file where a link should go is moved to `~/.dotkeep-backup/` first; a second backup of the same file gets a `.1` suffix, and so on. `--no-backup` skips those files instead.
- Links that point somewhere else are only replaced with `--force`.
- `unlink` only removes links that point into the repo (or, in copy mode, copies that still match).
- Every command that changes files has `--dry-run`, except `add` and `remove`, which only touch the paths you name.

## Copy mode

On Windows, creating symlinks needs Developer Mode (or admin rights). If you cannot turn it on, set `mode = "copy"`: files are copied instead of linked, and `status` shows `modified` when a copy no longer matches the repo. `dotkeep doctor` tells you whether symlinks work on the machine.

## Development

```bash
pip install -e ".[dev]"
pytest        # tests
mypy          # strict type check
ruff check    # lint
```

```
src/dotkeep/
  cli.py        argument parsing, one function per command, output
  manifest.py   dotkeep.toml: load, validate, add and remove entries
  linker.py     link, unlink, status, add, remove, backups, copy mode
  doctor.py     setup checks
tests/          pytest suite, uses temporary home and repo folders
examples/       a small example dotfiles repo
```

CI runs the tests on Linux, macOS and Windows with Python 3.11, 3.12 and 3.13.

## Roadmap

Per-host entries, templates, private files and `sync` are next. See [ROADMAP.md](ROADMAP.md) and [CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE)
