# Changelog

## 0.2.0

- Copy mode (`[settings] mode = "copy"` or `--mode copy`) for machines without symlink support; `status` reports `modified` copies
- `doctor` command: symlink support, missing sources, git, leftover backups
- `unlink --restore` leaves real copies in place of the links
- `link --force` replaces links that point somewhere else
- `add --as` to choose the path inside the repo
- Backups never overwrite earlier backups (`.1`, `.2`, ... suffixes)
- Manifest paths are validated (no absolute paths, `~` or `..`)
- `--quiet`, and permission errors are reported instead of crashing

## 0.1.0

- `init`, `add`, `link`, `unlink`, `status` and `list`
- `dotkeep.toml` with per-platform `[links.linux]`, `[links.macos]` and `[links.windows]` sections
- Existing files are backed up before linking, `--dry-run` everywhere it changes files
- Repo path from `--repo` or `DOTKEEP_REPO`, colored output
