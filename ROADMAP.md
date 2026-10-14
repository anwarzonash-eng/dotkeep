# Roadmap

Things I want to add, roughly in this order.

## 0.4 – machines and secrets
- [ ] Per-host sections (`[links.host.work-laptop]`) next to the per-platform ones
- [ ] Simple templates: `{{ name }}`-style placeholders filled from a local, untracked `dotkeep.local.toml`
- [ ] Keep secrets out of the repo: entries marked `private = true` are copied from a local folder, never committed
- [ ] `dotkeep diff` to show what changed between a copy and the repo (copy mode)
- [ ] `dotkeep pull` to bring edited copies back into the repo (copy mode)

## 0.5 – everyday use
- [ ] `dotkeep sync`: `git pull` in the repo, then `link`
- [ ] `--json` output for `status` and `list`
- [ ] Shell completions for bash, zsh, fish and PowerShell
- [ ] `dotkeep edit TARGET` to open the repo copy in `$EDITOR`
- [ ] Clean up empty folders left behind by `unlink` and `remove`
- [ ] `dotkeep backups` to list and restore files from `~/.dotkeep-backup`

## Robustness
- [ ] Windows: fall back to directory junctions for folders when symlinks are not allowed
- [ ] Relative symlinks as an option, so the repo can be moved
- [ ] Detect when two entries point at the same target
- [ ] Lock file to stop two runs at the same time
- [ ] Property-based tests for the manifest text editing (`add_entries`, `remove_targets`)

## Release
- [ ] Publish to PyPI with trusted publishing, tag releases
- [ ] `pipx install dotkeep` instructions
- [ ] Short docs site with a migration guide from GNU Stow
