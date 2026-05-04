# dotkeep

A small tool to keep my dotfiles in one git folder and link them into place on each machine.

You keep the real files in a folder such as `~/dotfiles`, list them in `dotkeep.toml`, and `dotkeep link` puts symlinks in your home directory that point back to the folder.

Written in Python (3.11+), standard library only.

## Usage

```toml
# ~/dotfiles/dotkeep.toml
[links]
".bashrc" = "bash/bashrc"
".gitconfig" = "git/config"
```

```bash
pip install -e .
dotkeep link --dry-run   # see what would change
dotkeep link             # create the links
dotkeep status           # ok / missing / conflict / wrong-link / no-source
```

If a real file is already where a link should go, `link` moves it to `~/.dotkeep-backup/` first. Use `--no-backup` to skip those files instead.

Use `--repo PATH` if your dotfiles are not in `~/dotfiles`.

## Tests

```bash
pip install -e ".[dev]"
pytest
```
