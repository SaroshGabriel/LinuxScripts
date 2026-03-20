#!/bin/bash
# ============================================================
# syncAliases.sh - Bidirectional Alias Sync Tool
# Author: KJ
# Version: 1.0
# 
# Syncs aliases between ~/.bashrc and aliases.conf
# Run manually or schedule via cron for daily auto-sync
# ============================================================

# ── Configuration ────────────────────────────────────────────
BASHRC="$HOME/.bashrc"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALIASES_CONF="$SCRIPT_DIR/aliases.conf"
BACKUP_DIR="$HOME/.alias_backups"
LOG_FILE="$HOME/.alias_sync.log"

# ── Colors ───────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# ── Helpers ──────────────────────────────────────────────────

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

print_header() {
    echo -e "\n${BOLD}${CYAN}╔══════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}${CYAN}║       🔄  Alias Sync Tool v1.0           ║${RESET}"
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════╝${RESET}\n"
}

progress_bar() {
    local current=$1
    local total=$2
    local label=$3
    local width=40
    local percent=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))
    local bar=""
    for ((i=0; i<filled; i++)); do bar+="█"; done
    for ((i=0; i<empty; i++)); do bar+="░"; done
    printf "\r  ${CYAN}[${bar}]${RESET} ${percent}%% - ${label}"
    if [ "$current" -eq "$total" ]; then echo; fi
}

backup_files() {
    mkdir -p "$BACKUP_DIR"
    local ts
    ts=$(date '+%Y%m%d_%H%M%S')
    cp "$BASHRC" "$BACKUP_DIR/bashrc_$ts.bak"
    cp "$ALIASES_CONF" "$BACKUP_DIR/aliases_conf_$ts.bak"
    echo -e "  ${DIM}📦 Backups saved to $BACKUP_DIR${RESET}"
    log "Backup created: bashrc_$ts.bak + aliases_conf_$ts.bak"
}

# Extract alias name from a line like: alias name='command'
get_alias_name() {
    echo "$1" | sed -n "s/^alias \([^=]*\)=.*/\1/p"
}

# Extract alias command from a line like: alias name='command'
get_alias_command() {
    echo "$1" | sed -n "s/^alias [^=]*=\(.*\)/\1/p"
}

# Get all alias lines from a file (ignoring comments and blanks)
get_aliases_from_file() {
    grep -E "^alias [^=]+=" "$1" 2>/dev/null
}

# ── Main Sync Logic ──────────────────────────────────────────

sync_aliases() {
    print_header

    # Validate files exist
    if [ ! -f "$BASHRC" ]; then
        echo -e "${RED}❌ ~/.bashrc not found!${RESET}"
        exit 1
    fi

    if [ ! -f "$ALIASES_CONF" ]; then
        echo -e "${RED}❌ aliases.conf not found at: $ALIASES_CONF${RESET}"
        exit 1
    fi

    echo -e "${BOLD}📂 Files:${RESET}"
    echo -e "  bashrc:      ${DIM}$BASHRC${RESET}"
    echo -e "  aliases.conf: ${DIM}$ALIASES_CONF${RESET}"
    echo

    # Backup first
    backup_files
    echo

    # Read all aliases
    local bashrc_aliases
    local conf_aliases
    bashrc_aliases=$(get_aliases_from_file "$BASHRC")
    conf_aliases=$(get_aliases_from_file "$ALIASES_CONF")

    # Build associative arrays
    declare -A bashrc_map   # name -> command
    declare -A conf_map     # name -> command

    while IFS= read -r line; do
        [ -z "$line" ] && continue
        local name cmd
        name=$(get_alias_name "$line")
        cmd=$(get_alias_command "$line")
        [ -n "$name" ] && bashrc_map["$name"]="$cmd"
    done <<< "$bashrc_aliases"

    while IFS= read -r line; do
        [ -z "$line" ] && continue
        local name cmd
        name=$(get_alias_name "$line")
        cmd=$(get_alias_command "$line")
        [ -n "$name" ] && conf_map["$name"]="$cmd"
    done <<< "$conf_aliases"

    # ── Step 1: aliases.conf → bashrc ────────────────────────
    echo -e "${BOLD}━━━ Step 1: Syncing aliases.conf → bashrc ━━━${RESET}\n"

    local conf_keys=("${!conf_map[@]}")
    local total=${#conf_keys[@]}
    local count=0
    local added_to_bashrc=()
    local skipped=()
    local pending_updates=()

    for name in "${conf_keys[@]}"; do
        ((count++))
        progress_bar "$count" "$total" "Checking: $name"
        local conf_cmd="${conf_map[$name]}"

        if [ -z "${bashrc_map[$name]+_}" ]; then
            # Not in bashrc at all → add it
            added_to_bashrc+=("$name")
            echo "" >> "$BASHRC"
            echo "alias $name=$conf_cmd" >> "$BASHRC"
            log "Added to bashrc: alias $name=$conf_cmd"
        elif [ "${bashrc_map[$name]}" = "$conf_cmd" ]; then
            # Exact match → skip (no duplicate)
            skipped+=("$name")
        else
            # Same name, different command → ask user
            pending_updates+=("$name")
        fi
    done

    echo
    echo -e "\n  ${GREEN}✅ Added to bashrc:${RESET} ${#added_to_bashrc[@]} aliases"
    echo -e "  ${DIM}⏭  Skipped (exact match):${RESET} ${#skipped[@]} aliases"
    echo

    # ── Step 2: Handle conflicts (same name, different cmd) ──
    if [ ${#pending_updates[@]} -gt 0 ]; then
        echo -e "${BOLD}━━━ Step 2: Resolving Conflicts ━━━${RESET}\n"
        echo -e "  ${YELLOW}⚠️  Found ${#pending_updates[@]} alias(es) with same name but different command.${RESET}\n"

        local conflict_count=0
        local conflict_total=${#pending_updates[@]}

        for name in "${pending_updates[@]}"; do
            ((conflict_count++))
            echo -e "  ${BOLD}[$conflict_count/$conflict_total]${RESET} Conflict: ${CYAN}$name${RESET}"
            echo -e "  ${DIM}  bashrc:      ${RESET}alias $name=${bashrc_map[$name]}"
            echo -e "  ${DIM}  aliases.conf:${RESET} alias $name=${conf_map[$name]}"
            echo
            echo -e "  What do you want to do?"
            echo -e "  ${GREEN}[1]${RESET} Keep bashrc version"
            echo -e "  ${CYAN}[2]${RESET} Use aliases.conf version (update bashrc)"
            echo -e "  ${YELLOW}[3]${RESET} Keep both (rename conf version)"
            echo -e "  ${DIM}[s]${RESET} Skip"
            echo -n "  Choice: "
            read -r choice

            case "$choice" in
                1)
                    echo -e "  ${GREEN}✅ Kept bashrc version.${RESET}\n"
                    log "Conflict '$name': kept bashrc version"
                    ;;
                2)
                    # Replace in bashrc
                    sed -i "s|^alias $name=.*|alias $name=${conf_map[$name]}|" "$BASHRC"
                    echo -e "  ${CYAN}✅ Updated bashrc with aliases.conf version.${RESET}\n"
                    log "Conflict '$name': updated bashrc with conf version"
                    ;;
                3)
                    echo -n "  Enter new name for aliases.conf version: "
                    read -r new_name
                    echo "" >> "$BASHRC"
                    echo "alias $new_name=${conf_map[$name]}" >> "$BASHRC"
                    echo -e "  ${YELLOW}✅ Added as: alias $new_name${RESET}\n"
                    log "Conflict '$name': added conf version as '$new_name'"
                    ;;
                *)
                    echo -e "  ${DIM}⏭  Skipped.${RESET}\n"
                    log "Conflict '$name': skipped"
                    ;;
            esac
        done
    fi

    # ── Step 3: bashrc → aliases.conf ────────────────────────
    echo -e "${BOLD}━━━ Step 3: Syncing bashrc → aliases.conf ━━━${RESET}\n"

    local bashrc_keys=("${!bashrc_map[@]}")
    local total3=${#bashrc_keys[@]}
    local count3=0
    local added_to_conf=()

    for name in "${bashrc_keys[@]}"; do
        ((count3++))
        progress_bar "$count3" "$total3" "Checking: $name"

        if [ -z "${conf_map[$name]+_}" ]; then
            # Check if same command exists under different name in conf
            local bashrc_cmd="${bashrc_map[$name]}"
            local duplicate_found=false
            for conf_name in "${!conf_map[@]}"; do
                if [ "${conf_map[$conf_name]}" = "$bashrc_cmd" ]; then
                    duplicate_found=true
                    break
                fi
            done

            if [ "$duplicate_found" = false ]; then
                added_to_conf+=("$name")
                echo "" >> "$ALIASES_CONF"
                echo "# Synced from bashrc on $(date '+%Y-%m-%d')" >> "$ALIASES_CONF"
                echo "alias $name=$bashrc_cmd" >> "$ALIASES_CONF"
                log "Synced to aliases.conf: alias $name=$bashrc_cmd"
            fi
        fi
    done

    echo
    echo -e "\n  ${GREEN}✅ Added to aliases.conf:${RESET} ${#added_to_conf[@]} aliases"
    echo

    # ── Step 4: Source bashrc ─────────────────────────────────
    echo -e "${BOLD}━━━ Step 4: Applying Changes ━━━${RESET}\n"
    # shellcheck disable=SC1090
    source "$BASHRC"
    echo -e "  ${GREEN}✅ bashrc sourced successfully.${RESET}"
    log "Sync complete. bashrc sourced."

    # ── Summary ──────────────────────────────────────────────
    echo -e "\n${BOLD}${CYAN}╔══════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}${CYAN}║              ✅ Sync Complete             ║${RESET}"
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════╝${RESET}"
    echo -e "  Added to bashrc:       ${GREEN}${#added_to_bashrc[@]}${RESET}"
    echo -e "  Added to aliases.conf: ${GREEN}${#added_to_conf[@]}${RESET}"
    echo -e "  Conflicts resolved:    ${YELLOW}${#pending_updates[@]}${RESET}"
    echo -e "  Log: ${DIM}$LOG_FILE${RESET}\n"
}

# ── Auto-sync via cron ───────────────────────────────────────

install_cron() {
    local cron_job="0 9 * * * bash $SCRIPT_DIR/syncAliases.sh --auto >> $LOG_FILE 2>&1"
    (crontab -l 2>/dev/null | grep -v "syncAliases.sh"; echo "$cron_job") | crontab -
    echo -e "${GREEN}✅ Daily auto-sync scheduled at 9:00 AM via cron.${RESET}"
    log "Cron job installed: $cron_job"
}

remove_cron() {
    crontab -l 2>/dev/null | grep -v "syncAliases.sh" | crontab -
    echo -e "${YELLOW}✅ Auto-sync cron job removed.${RESET}"
    log "Cron job removed."
}

# ── Entry Point ──────────────────────────────────────────────

case "${1:-}" in
    --auto)
        # Silent auto-sync mode for cron
        log "Auto-sync started"
        sync_aliases > /dev/null 2>&1
        log "Auto-sync completed"
        ;;
    --install-cron)
        install_cron
        ;;
    --remove-cron)
        remove_cron
        ;;
    --help|-h)
        echo -e "\n${BOLD}syncAliases.sh${RESET} - Bidirectional alias sync tool\n"
        echo "Usage:"
        echo "  bash syncAliases.sh              # Interactive sync"
        echo "  bash syncAliases.sh --auto       # Silent sync (for cron)"
        echo "  bash syncAliases.sh --install-cron  # Schedule daily auto-sync"
        echo "  bash syncAliases.sh --remove-cron   # Remove auto-sync"
        echo "  bash syncAliases.sh --help       # Show this help"
        echo
        ;;
    *)
        sync_aliases
        ;;
esac
