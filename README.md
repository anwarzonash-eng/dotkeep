# dotkeep

A small tool to keep my dotfiles in one git folder and link them into place on each machine.

You keep the real files in a folder such as `~/dotfiles`, list them in `dotkeep.toml`, and `dotkeep link` puts symlinks in your home directory that point back to the folder. On a new machine it is `git clone` + `dotkeep link`.

Written in Python (3.11+), standard library only.

## Install

```bash
git clone <this repo> && cd dotkeep
pip install -e .
```

## Usage

```bash
dotkeep add ~/.bashrc ~/.config/nvim/init.lua   # move files into the repo, link them back
dotkeep list                                    # what is in the manifest
dotkeep status                                  # ok / missing / conflict / wrong-link / no-source
dotkeep link --dry-run                          # on a new machine: see what would change
dotkeep link                                    # ... and create the links
dotkeep unlink                                  # remove the links again
dotkeep unlink --restore                        # ... leaving real copies behind
dotkeep doctor                                  # check symlink support, missing files, backups
```

`add` writes the new entries to `dotkeep.toml` for you. The file looks like this:

```toml
[links]
".bashrc" = "bashrc"
".config/nvim/init.lua" = "config/nvim/init.lua"

# only on Windows; same target names override the ones above
[links.windows]
"AppData/Roaming/Code/User/settings.json" = "vscode/settings.json"

[links.macos]
"Library/Application Support/Code/User/settings.json" = "vscode/settings.json"
```

Targets are relative to your home folder, sources are relative to the repo.

If a real file is already where a link should go, `link` moves it to `~/.dotkeep-backup/` first (a second backup of the same file gets a `.1` suffix, and so on). Use `--no-backup` to skip those files instead. Links that point somewhere else are only replaced with `--force`.

`status` exits with `1` when anything is not `ok`, so it can be used in scripts.

Paths in the manifest must stay inside their folder: no absolute paths, `~` or `..`.

## Copy mode

On Windows, creating symlinks needs Developer Mode (or admin rights). If you cannot turn it on, use copy mode: files are copied instead of linked, and `status` shows `modified` when a copy no longer matches the repo.

```toml
[settings]
mode = "copy"
```

or per command: `dotkeep --mode copy link`. `dotkeep doctor` tells you whether symlinks work on the machine.

The repo is `~/dotfiles` by default. Change it with `--repo PATH` or the `DOTKEEP_REPO` environment variable. Colors are turned off with `--no-color` or `NO_COLOR`.

## Tests

```bash
pip install -e ".[dev]"
pytest
```
