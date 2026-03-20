#!/bin/bash
# ============================================================
# MySession.sh - Ghost Session Tool
# Author: KJ
# Version: 1.0
#
# Temporarily loads your aliases onto any borrowed Linux system.
# On exit: restores the system exactly as it was, and syncs
# any NEW aliases you added back to your aliases.conf (git).
#
# Usage:
#   source MySession.sh --start    → load your aliases
#   source MySession.sh --end      → clean exit, sync new aliases
#   source MySession.sh --status   → show session info
#   source MySession.sh --help     → show this help
#
# MUST be sourced (not run with bash) for alias changes to
# take effect in your current shell:
#   source MySession.sh --start   ✅
#   bash MySession.sh --start     ❌ (aliases won't stick)
# ============================================================

# ── Guard: must be sourced ───────────────────────────────────
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "⚠️  MySession.sh must be SOURCED, not executed directly."
    echo "   Run: source MySession.sh --start"
    exit 1
fi

# ── Configuration ────────────────────────────────────────────
_MS_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_MS_ALIASES_CONF="$_MS_SCRIPT_DIR/aliases.conf"
_MS_GITHUB_RAW_URL="https://raw.githubusercontent.com/SaroshGabriel/LinuxScripts/main/aliasSyncWithBashrc/aliases.conf"
# ↑ Replace SaroshGabriel with your actual GitHub username before pushing

_MS_BASHRC="$HOME/.bashrc"
_MS_SNAPSHOT="$HOME/.bashrc_ms_snapshot"
_MS_SESSION_LOG="$HOME/.mysession.log"
_MS_TRACKED_FILE="$HOME/.mysession_aliases_tracked"

# ── Colors ───────────────────────────────────────────────────
_MS_RED='\033[0;31m'
_MS_GREEN='\033[0;32m'
_MS_YELLOW='\033[1;33m'
_MS_CYAN='\033[0;36m'
_MS_MAGENTA='\033[0;35m'
_MS_BOLD='\033[1m'
_MS_DIM='\033[2m'
_MS_RESET='\033[0m'

# ── Helpers ──────────────────────────────────────────────────

_ms_log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$_MS_SESSION_LOG"
}

_ms_header() {
    echo -e "\n${_MS_BOLD}${_MS_CYAN}╔══════════════════════════════════════════════╗${_MS_RESET}"
    echo -e "${_MS_BOLD}${_MS_CYAN}║       👻  MySession Ghost Tool v1.0          ║${_MS_RESET}"
    echo -e "${_MS_BOLD}${_MS_CYAN}╚══════════════════════════════════════════════╝${_MS_RESET}\n"
}

_ms_divider() {
    echo -e "${_MS_DIM}──────────────────────────────────────────────${_MS_RESET}"
}

# Extract alias names from a file
_ms_get_alias_names() {
    grep -E "^alias [^=]+=" "$1" 2>/dev/null | sed -n "s/^alias \([^=]*\)=.*/\1/p"
}

# Extract full alias lines from a file
_ms_get_alias_lines() {
    grep -E "^alias [^=]+=" "$1" 2>/dev/null
}

# ── Fetch aliases.conf (local or GitHub) ─────────────────────

_ms_fetch_aliases_conf() {
    # Priority 1: local file next to MySession.sh
    if [ -f "$_MS_ALIASES_CONF" ]; then
        echo -e "  ${_MS_GREEN}📁 aliases.conf found locally.${_MS_RESET}"
        _ms_log "Using local aliases.conf: $_MS_ALIASES_CONF"
        return 0
    fi

    # Priority 2: fetch from GitHub
    echo -e "  ${_MS_YELLOW}⚠️  Local aliases.conf not found. Fetching from GitHub...${_MS_RESET}"

    if command -v curl &>/dev/null; then
        curl -fsSL "$_MS_GITHUB_RAW_URL" -o "$_MS_ALIASES_CONF"
    elif command -v wget &>/dev/null; then
        wget -q "$_MS_GITHUB_RAW_URL" -O "$_MS_ALIASES_CONF"
    else
        echo -e "  ${_MS_RED}❌ Neither curl nor wget found. Cannot fetch aliases.conf.${_MS_RESET}"
        _ms_log "FAILED: no curl/wget to fetch aliases.conf"
        return 1
    fi

    if [ $? -eq 0 ] && [ -s "$_MS_ALIASES_CONF" ]; then
        echo -e "  ${_MS_GREEN}✅ aliases.conf fetched from GitHub.${_MS_RESET}"
        _ms_log "Fetched aliases.conf from GitHub"
        return 0
    else
        echo -e "  ${_MS_RED}❌ Failed to fetch aliases.conf from GitHub.${_MS_RESET}"
        echo -e "  ${_MS_DIM}   Check: $_MS_GITHUB_RAW_URL${_MS_RESET}"
        _ms_log "FAILED: GitHub fetch returned empty or error"
        return 1
    fi
}

# ── START SESSION ─────────────────────────────────────────────

_ms_start() {
    _ms_header

    # Block double-start
    if [ -f "$_MS_SNAPSHOT" ]; then
        echo -e "  ${_MS_YELLOW}⚠️  A session is already active on this machine.${_MS_RESET}"
        echo -e "  ${_MS_DIM}   Run: source MySession.sh --end  to close it first.${_MS_RESET}\n"
        return 1
    fi

    echo -e "${_MS_BOLD}━━━ Step 1: Fetching Your Aliases ━━━${_MS_RESET}\n"
    _ms_fetch_aliases_conf || return 1

    echo -e "\n${_MS_BOLD}━━━ Step 2: Snapshotting This System's bashrc ━━━${_MS_RESET}\n"
    cp "$_MS_BASHRC" "$_MS_SNAPSHOT"
    echo -e "  ${_MS_GREEN}📸 Snapshot saved: $_MS_SNAPSHOT${_MS_RESET}"
    _ms_log "Session START. Snapshot: $_MS_SNAPSHOT"

    echo -e "\n${_MS_BOLD}━━━ Step 3: Injecting Your Aliases ━━━${_MS_RESET}\n"

    # Record which alias names we are about to inject (for clean removal later)
    local my_alias_names
    my_alias_names=$(_ms_get_alias_names "$_MS_ALIASES_CONF")
    echo "$my_alias_names" > "$_MS_TRACKED_FILE"

    # Count
    local count
    count=$(echo "$my_alias_names" | grep -c '.' 2>/dev/null || echo 0)

    # Append to bashrc with clear markers
    {
        echo ""
        echo "# ── MySession START ($(date '+%Y-%m-%d %H:%M:%S')) ──────────────"
        echo "source $_MS_ALIASES_CONF"
        echo "# ── MySession END ────────────────────────────────────────────────"
    } >> "$_MS_BASHRC"

    # Load aliases into current live shell immediately
    # shellcheck disable=SC1090
    source "$_MS_ALIASES_CONF"

    echo -e "  ${_MS_GREEN}✅ $count aliases injected into bashrc + live shell.${_MS_RESET}"
    _ms_log "Injected $count aliases from aliases.conf"

    _ms_divider
    echo -e "\n  ${_MS_MAGENTA}👻 Ghost session active.${_MS_RESET}"
    echo -e "  ${_MS_DIM}   This machine will be restored when you run:${_MS_RESET}"
    echo -e "  ${_MS_BOLD}   source MySession.sh --end${_MS_RESET}\n"
}

# ── END SESSION ───────────────────────────────────────────────

_ms_end() {
    _ms_header

    # Guard: no active session
    if [ ! -f "$_MS_SNAPSHOT" ]; then
        echo -e "  ${_MS_YELLOW}⚠️  No active session found. Nothing to clean up.${_MS_RESET}\n"
        return 1
    fi

    echo -e "${_MS_BOLD}━━━ Step 1: Detecting New Aliases You Added ━━━${_MS_RESET}\n"

    # Get alias names that were in aliases.conf at session start
    local original_names
    original_names=$(cat "$_MS_TRACKED_FILE" 2>/dev/null)

    # Get current alias names in bashrc (excluding snapshot content)
    local current_bashrc_aliases
    current_bashrc_aliases=$(_ms_get_alias_lines "$_MS_BASHRC")

    # Find aliases in current bashrc that are NOT in original tracked list
    local new_aliases=()
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        local name
        name=$(echo "$line" | sed -n "s/^alias \([^=]*\)=.*/\1/p")
        if [ -n "$name" ] && ! grep -qx "$name" "$_MS_TRACKED_FILE" 2>/dev/null; then
            new_aliases+=("$line")
        fi
    done <<< "$current_bashrc_aliases"

    if [ ${#new_aliases[@]} -eq 0 ]; then
        echo -e "  ${_MS_DIM}ℹ️  No new aliases detected during this session.${_MS_RESET}"
    else
        echo -e "  ${_MS_GREEN}🆕 Found ${#new_aliases[@]} new alias(es) added during session:${_MS_RESET}\n"
        for a in "${new_aliases[@]}"; do
            echo -e "     ${_MS_CYAN}$a${_MS_RESET}"
        done
        echo
    fi

    echo -e "\n${_MS_BOLD}━━━ Step 2: Restoring Borrowed System's bashrc ━━━${_MS_RESET}\n"
    cp "$_MS_SNAPSHOT" "$_MS_BASHRC"
    echo -e "  ${_MS_GREEN}✅ bashrc restored to original state.${_MS_RESET}"
    _ms_log "bashrc restored from snapshot"

    echo -e "\n${_MS_BOLD}━━━ Step 3: Unaliasing Your Aliases from Live Shell ━━━${_MS_RESET}\n"
    local unaliased=0
    while IFS= read -r name; do
        [ -z "$name" ] && continue
        if alias "$name" &>/dev/null 2>&1; then
            unalias "$name" 2>/dev/null
            ((unaliased++))
        fi
    done < "$_MS_TRACKED_FILE"
    echo -e "  ${_MS_GREEN}✅ $unaliased aliases removed from live shell.${_MS_RESET}"
    _ms_log "Unaliased $unaliased aliases from live shell"

    echo -e "\n${_MS_BOLD}━━━ Step 4: Syncing New Aliases → Your aliases.conf ━━━${_MS_RESET}\n"

    if [ ${#new_aliases[@]} -gt 0 ]; then
        {
            echo ""
            echo "# New aliases synced from borrowed machine on $(date '+%Y-%m-%d')"
            for a in "${new_aliases[@]}"; do
                echo "$a"
            done
        } >> "$_MS_ALIASES_CONF"
        echo -e "  ${_MS_GREEN}✅ ${#new_aliases[@]} new alias(es) appended to aliases.conf.${_MS_RESET}"
        _ms_log "Appended ${#new_aliases[@]} new aliases to aliases.conf"

        # Try to git commit + push
        echo -e "\n  ${_MS_DIM}Attempting git push to sync aliases.conf...${_MS_RESET}"
        if git -C "$_MS_SCRIPT_DIR" rev-parse --is-inside-work-tree &>/dev/null; then
            git -C "$_MS_SCRIPT_DIR" add aliases.conf
            git -C "$_MS_SCRIPT_DIR" commit -m "MySession: sync new aliases from borrowed machine ($(date '+%Y-%m-%d'))"
            git -C "$_MS_SCRIPT_DIR" push
            if [ $? -eq 0 ]; then
                echo -e "  ${_MS_GREEN}✅ aliases.conf pushed to git.${_MS_RESET}"
                _ms_log "git push successful"
            else
                echo -e "  ${_MS_YELLOW}⚠️  git push failed (no network or auth). aliases.conf updated locally.${_MS_RESET}"
                echo -e "  ${_MS_DIM}   Push manually later: git push from $_MS_SCRIPT_DIR${_MS_RESET}"
                _ms_log "git push failed — local update only"
            fi
        else
            echo -e "  ${_MS_YELLOW}⚠️  Not a git repo. aliases.conf updated locally only.${_MS_RESET}"
            echo -e "  ${_MS_DIM}   Push manually from your own machine.${_MS_RESET}"
            _ms_log "Not a git repo — no push attempted"
        fi
    else
        echo -e "  ${_MS_DIM}ℹ️  Nothing to sync.${_MS_RESET}"
    fi

    echo -e "\n${_MS_BOLD}━━━ Step 5: Cleanup ━━━${_MS_RESET}\n"
    rm -f "$_MS_SNAPSHOT" "$_MS_TRACKED_FILE"
    echo -e "  ${_MS_GREEN}✅ Session files cleaned up.${_MS_RESET}"
    _ms_log "Session END. Cleanup done."

    _ms_divider
    echo -e "\n  ${_MS_MAGENTA}👻 Ghost session ended.${_MS_RESET}"
    echo -e "  ${_MS_GREEN}   This machine is back to exactly how you found it.${_MS_RESET}\n"
}

# ── STATUS ────────────────────────────────────────────────────

_ms_status() {
    _ms_header
    if [ -f "$_MS_SNAPSHOT" ]; then
        local tracked_count
        tracked_count=$(wc -l < "$_MS_TRACKED_FILE" 2>/dev/null || echo "?")
        echo -e "  ${_MS_GREEN}👻 Session is ACTIVE${_MS_RESET}"
        echo -e "  ${_MS_DIM}   Snapshot: $_MS_SNAPSHOT${_MS_RESET}"
        echo -e "  ${_MS_DIM}   Aliases injected: $tracked_count${_MS_RESET}"
        echo -e "  ${_MS_DIM}   Log: $_MS_SESSION_LOG${_MS_RESET}"
    else
        echo -e "  ${_MS_DIM}ℹ️  No active session on this machine.${_MS_RESET}"
    fi
    echo
}

# ── HELP ──────────────────────────────────────────────────────

_ms_help() {
    _ms_header
    echo -e "${_MS_BOLD}USAGE${_MS_RESET} (must be sourced, not executed)\n"
    echo -e "  ${_MS_CYAN}source MySession.sh --start${_MS_RESET}    Load your aliases onto this machine"
    echo -e "  ${_MS_CYAN}source MySession.sh --end${_MS_RESET}      Restore machine + sync new aliases to git"
    echo -e "  ${_MS_CYAN}source MySession.sh --status${_MS_RESET}   Check if a session is active"
    echo -e "  ${_MS_CYAN}source MySession.sh --help${_MS_RESET}     Show this help\n"
    echo -e "${_MS_BOLD}WHAT IT DOES${_MS_RESET}\n"
    echo -e "  --start  Snapshots ~/.bashrc, injects your aliases.conf,"
    echo -e "           and loads them live into the current shell.\n"
    echo -e "  --end    Restores ~/.bashrc to its original state,"
    echo -e "           unaliases everything from the live shell,"
    echo -e "           and syncs any new aliases you added back"
    echo -e "           to aliases.conf + pushes to git.\n"
    echo -e "${_MS_BOLD}ALIASES.CONF RESOLUTION${_MS_RESET}\n"
    echo -e "  1st priority → local file next to MySession.sh"
    echo -e "  2nd priority → fetched from GitHub raw URL\n"
    echo -e "${_MS_BOLD}SETUP${_MS_RESET}\n"
    echo -e "  Edit MySession.sh and set _MS_GITHUB_RAW_URL"
    echo -e "  to your actual GitHub raw aliases.conf URL.\n"
}

# ── Entry Point ───────────────────────────────────────────────

case "${1:-}" in
    --start)
        _ms_start
        ;;
    --end)
        _ms_end
        ;;
    --status)
        _ms_status
        ;;
    --help|-h|"")
        _ms_help
        ;;
    *)
        echo -e "${_MS_RED}❌ Unknown option: $1${_MS_RESET}"
        echo -e "   Run: source MySession.sh --help"
        ;;
esac
