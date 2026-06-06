# LinuxScripts

> The utilities I actually run on Arch — a market-research scanner, a portable
> shell environment, and Hyprland desktop bits. One repo, self-contained dirs.

![Platform](https://img.shields.io/badge/platform-Arch%20Linux-1793d1?logo=archlinux&logoColor=white)
![Python](https://img.shields.io/badge/Python-3-3776ab?logo=python&logoColor=white)
![Shell](https://img.shields.io/badge/shell-bash-4eaa25?logo=gnubash&logoColor=white)
![Desktop](https://img.shields.io/badge/desktop-Hyprland%20%2F%20Waybar-58e1ff)

A grab-bag of personal tooling that earns its keep day to day. Each top-level
directory stands alone — clone the repo, use whichever piece you need.

---

## Contents

### `niftyMonitor/` — market research scanner (the big one)
A Python CLI (`v3.0`) that scores Indian equities on 8 fundamentals out of 100
and flags **BUY / WATCH / AVOID** in a rich terminal table. Covers the NIFTY 50
plus **27 sectors (~270 stocks)**, and extends to crypto, metals, forex and US
stocks. Exports timestamped CSV; optional watch mode and systemd timer.

```bash
cd niftyMonitor && ./setup.sh && ./run.sh        # NIFTY 50 scan
./run.sh --sectorscan        # all 27 sectors
./run.sh --stock RELIANCE    # single-stock deep dive
```

API key (for the crypto/forex/metals sources) is read at runtime from
`~/.config/stock_monitor/twelvedata_key` — never hard-coded or committed. Full
docs in [`niftyMonitor/README.md`](niftyMonitor/README.md).

### `aliasSyncWithBashrc/` — portable shell environment
- `syncAliases.sh` — two-way sync of `aliases.conf` <-> `~/.bashrc`
- `MySession.sh` — "ghost session" helper for working on a borrowed machine and
  cleaning up after; auto-commits its own changes on exit
- `aliases.conf` — the alias source of truth · `README_aliases.md` — details

### `waybarConfig/` — Waybar status bar
`config.jsonc`, `style.css`, and helper `scripts/` (`clock.sh`, `netspeed.sh`)
for the Hyprland bar.

### `hyprlock/`
`hyprlock.conf` — screen-locker config.

### `setupWorkspace.sh`
One-shot bootstrap that creates the local workspace dirs and GitHub repos.

---

## Conventions

- Each directory is self-contained; secrets come from runtime files / env, never
  committed literals.
- **Branches:** `main` is the only current branch. Older topic branches from
  early experiments are unmaintained.

> Note: `MySession.sh` carries an **AES-encrypted** token for unattended push.
> Treat the passphrase as sensitive; prefer an env var or credential helper if
> you fork this.

---

## Author

**Sarosh (KJ)** · [github.com/ChargeInMotion](https://github.com/ChargeInMotion) · sarosh@chargeinmotion.dev
