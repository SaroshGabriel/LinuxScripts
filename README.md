# LinuxScripts

Personal Linux utilities and desktop config I run day to day on Arch — a Python
market scanner plus shell/WM tooling. All current content lives on **`main`** as
self-contained directories.

## Contents

### `niftyMonitor/` — Nifty 50 stock research scanner
Python CLI that pulls quotes and scores NSE stocks across 27 sectors (~270
stocks), ranks them into **buy / watch / avoid**, and exports an atomic,
deduplicated CSV.
- `stock_monitor.py` — scanner · `run.sh` / `setup.sh` — wrappers · `--listsectors` to enumerate
- API key is read at runtime via a helper (`_td_key()`), never hard-coded.

```bash
cd niftyMonitor && ./setup.sh && ./run.sh
```

### `aliasSyncWithBashrc/` — portable shell environment
- `syncAliases.sh` — bidirectional sync of `aliases.conf` ⇄ `~/.bashrc`
- `MySession.sh` — "ghost session" tooling for a borrowed machine; auto-commits on exit
- `aliases.conf` — alias source of truth · `README_aliases.md` — details

### `waybarConfig/` — Waybar status bar
`config.jsonc`, `style.css`, and helper `scripts/` for the Hyprland bar.

### `hyprlock/`
`hyprlock.conf` — screen-locker config.

### `setupWorkspace.sh`
One-shot workspace bootstrap.

## Notes

- Each directory is self-contained; secrets come from env/runtime helpers, not committed literals.
- **Heads-up on branches:** this repo carries a large number of legacy branches
  (`tut1`–`tut250`, old `hyprland*`/`waybar*` configs, etc.) from earlier
  experiments. They are not maintained — **`main` is the only current branch.**
  Worth pruning someday.

> `MySession.sh` embeds an **AES-encrypted** PAT for unattended push. Treat the
> encryption passphrase as sensitive; prefer an env var / credential helper if you fork this.
