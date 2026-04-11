#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════╗
# ║    NIFTY 50 Monitor — Arch Linux Setup Script        ║
# ╚══════════════════════════════════════════════════════╝

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
MONITOR="$SCRIPT_DIR/stock_monitor.py"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║       NIFTY 50 Monitor — Arch Linux Setup            ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── 1. Python check ──────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 not found. Run: sudo pacman -S python"
    exit 1
fi

PYVER=$(python3 --version)
echo "✓ Found $PYVER"

# ── 2. Create virtual environment ────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "→ Creating virtual environment at .venv/ ..."
    python3 -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# ── 3. Activate and install deps ─────────────────────────
source "$VENV_DIR/bin/activate"
echo "→ Installing dependencies..."
pip install --upgrade pip -q
pip install yfinance pandas rich schedule requests -q
echo "✓ All dependencies installed"

# ── 4. Make monitor executable ───────────────────────────
chmod +x "$MONITOR"
echo "✓ stock_monitor.py is executable"

# ── 5. Create launcher shell script ──────────────────────
cat > "$SCRIPT_DIR/run.sh" << 'EOF'
#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/.venv/bin/activate"
python "$DIR/stock_monitor.py" "$@"
EOF
chmod +x "$SCRIPT_DIR/run.sh"
echo "✓ Launcher created: run.sh"

# ── 6. Optional: systemd timer for auto-scan ─────────────
read -rp "
Set up systemd timer to auto-scan every 30 min? [y/N] " setup_timer

if [[ "$setup_timer" =~ ^[Yy]$ ]]; then
    SERVICE_FILE="$HOME/.config/systemd/user/nifty-monitor.service"
    TIMER_FILE="$HOME/.config/systemd/user/nifty-monitor.timer"

    mkdir -p "$HOME/.config/systemd/user"

    cat > "$SERVICE_FILE" << SEOF
[Unit]
Description=NIFTY 50 Stock Monitor Scan

[Service]
Type=oneshot
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/run.sh --export --alerts
StandardOutput=append:$SCRIPT_DIR/scan_log.txt
StandardError=append:$SCRIPT_DIR/scan_log.txt
SEOF

    cat > "$TIMER_FILE" << TEOF
[Unit]
Description=Run NIFTY 50 Monitor every 30 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min
Persistent=true

[Install]
WantedBy=timers.target
TEOF

    systemctl --user daemon-reload
    systemctl --user enable --now nifty-monitor.timer
    echo "✓ Systemd timer enabled — scans every 30 min"
    echo "  Logs: $SCRIPT_DIR/scan_log.txt"
    echo "  Status: systemctl --user status nifty-monitor.timer"
fi

# ── 7. Summary ───────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Setup complete! Here's how to use:                  ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║                                                      ║"
echo "║  Full NIFTY 50 scan:                                 ║"
echo "║    ./run.sh                                          ║"
echo "║                                                      ║"
echo "║  Watch mode (auto-refresh every 30 min):             ║"
echo "║    ./run.sh --watch                                  ║"
echo "║                                                      ║"
echo "║  Deep dive on one stock:                             ║"
echo "║    ./run.sh --stock RELIANCE                         ║"
echo "║    ./run.sh --stock HDFCBANK                         ║"
echo "║                                                      ║"
echo "║  Show only buy/avoid signals:                        ║"
echo "║    ./run.sh --alerts                                 ║"
echo "║                                                      ║"
echo "║  Export results to CSV:                              ║"
echo "║    ./run.sh --export                                 ║"
echo "║                                                      ║"
echo "║  Top 10 by score + export:                           ║"
echo "║    ./run.sh --top 10 --export                        ║"
echo "║                                                      ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
