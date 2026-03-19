# aliases.conf

A portable, well-commented alias configuration file for bash.
Works on any Linux system — just set your `PROJECT_BASE` at the top.

---

## 📦 What's Inside

| Section | Description |
|---|---|
| `PROJECT_BASE` | Dynamic base path — set once, works everywhere |
| Meta Aliases | `addAlias`, `aliases`, `aliasgrep` |
| Navigation | `proj`, `pyrev`, `bashrev`, `log` |
| Tree | `treee` — visual directory explorer |
| Python | `py`, `venv`, `jup`, `pyreq`, etc. |
| Git | `gs`, `ga`, `gc`, `gp`, `gday`, etc. |
| System | `c`, `bye`, `restart`, `myip`, `ll`, etc. |
| Arch Linux | `update`, `pacs`, `pacr`, `cleanup`, etc. |
| Hyprland | `wb`, `snap`, `snapr`, `wallpaper` |

---

## 🚀 Quick Start

### Option 1 — Append to bashrc directly
```bash
cat aliases.conf >> ~/.bashrc
source ~/.bashrc
```

### Option 2 — Source it from bashrc (recommended)
Add this line to your `~/.bashrc`:
```bash
source /path/to/aliases.conf
```
This way edits to `aliases.conf` are picked up automatically on new terminal sessions.

### Option 3 — Use the sync script
```bash
bash syncAliases.sh
```
This bidirectionally syncs `aliases.conf` with your `~/.bashrc`.

---

## ⚙️ Configuration

At the top of `aliases.conf`, set your projects base directory:
```bash
export PROJECT_BASE="$HOME/Projects"
```
This is the only line you need to change when using on a new system.

---

## ➕ Adding New Aliases

### Method 1 — Using `addAlias` (fastest)
```bash
addAlias "myalias=echo hello world"
```
This adds the alias to `~/.bashrc` and sources it immediately.

### Method 2 — Edit aliases.conf directly
Add your alias with a comment:
```bash
# myalias - does something useful
alias myalias='echo hello world'
```
Then sync:
```bash
bash syncAliases.sh
```

### Method 3 — Edit bashrc directly
Then run sync to pull it into aliases.conf:
```bash
bash syncAliases.sh
```

---

## 🖥️ Portability Notes

- **Arch Linux specific** aliases are clearly marked in comments — comment them out on other distros
- **Hyprland specific** aliases are clearly marked — comment them out on other WMs
- `PROJECT_BASE` auto-expands to the correct home directory on any user/system
- All paths use `$HOME` instead of hardcoded `/home/username`

---

## 📁 Recommended Git Structure

```
your-dotfiles/
├── aliases.conf        ← this file
├── syncAliases.sh      ← sync tool
├── README.md           ← this readme
└── .gitignore
```

---

## 🔄 Keeping It Updated

After cloning on a new machine:
```bash
git clone git@github.com:YOUR_USERNAME/dotfiles.git ~/dotfiles
bash ~/dotfiles/syncAliases.sh --install-cron
```

This installs a daily cron job that auto-syncs at 9:00 AM.
