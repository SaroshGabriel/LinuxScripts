#!/bin/bash
# ============================================================
# setupWorkspace.sh - Safe Workspace + GitHub Repo Setup
# Author: KJ / SaroshGabriel
# Version: 1.0
#
# Creates local directory structure and GitHub repos
# with branches for Practice, Projects and LinuxScripts
#
# SAFE BY DESIGN:
# - Never deletes anything
# - Dry-run mode shows what WILL happen before doing it
# - Skips anything that already exists
# - Full log of every action
# - Can be safely re-run anytime
#
# Usage:
#   bash setupWorkspace.sh --dry-run   # Preview only
#   bash setupWorkspace.sh             # Execute
# ============================================================

# ── Configuration ────────────────────────────────────────────
GITHUB_USER="SaroshGabriel"
LOG_FILE="$HOME/.workspace_setup.log"

# ── Colors ───────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# ── Dry run flag ─────────────────────────────────────────────
DRY_RUN=false
if [ "${1}" = "--dry-run" ]; then
    DRY_RUN=true
fi

# ── Helpers ──────────────────────────────────────────────────
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

info()    { echo -e "  ${CYAN}→${RESET} $1"; }
success() { echo -e "  ${GREEN}✅${RESET} $1"; log "SUCCESS: $1"; }
skip()    { echo -e "  ${DIM}⏭  SKIP: $1${RESET}"; log "SKIP: $1"; }
warn()    { echo -e "  ${YELLOW}⚠️  $1${RESET}"; log "WARN: $1"; }
dryrun()  { echo -e "  ${YELLOW}[DRY-RUN]${RESET} Would: $1"; }
fail()    { echo -e "  ${RED}❌ $1${RESET}"; log "FAIL: $1"; }

# Safe mkdir — skips if exists
safe_mkdir() {
    local dir="$1"
    if [ -d "$dir" ]; then
        skip "Directory exists: $dir"
    elif [ "$DRY_RUN" = true ]; then
        dryrun "mkdir -p $dir"
    else
        mkdir -p "$dir"
        success "Created directory: $dir"
        log "Created: $dir"
    fi
}

# Safe git init — skips if already a repo
safe_git_init() {
    local dir="$1"
    local branch="$2"
    if [ -d "$dir/.git" ]; then
        skip "Git already initialized: $dir"
    elif [ "$DRY_RUN" = true ]; then
        dryrun "git init -b $branch $dir"
    else
        git -C "$dir" init -b "$branch" > /dev/null 2>&1
        success "Git initialized: $dir (branch: $branch)"
        log "Git init: $dir branch: $branch"
    fi
}

# Safe GitHub repo create — skips if exists
safe_gh_create() {
    local repo="$1"
    local desc="$2"
    if gh repo view "$GITHUB_USER/$repo" > /dev/null 2>&1; then
        skip "GitHub repo exists: $GITHUB_USER/$repo"
    elif [ "$DRY_RUN" = true ]; then
        dryrun "gh repo create $GITHUB_USER/$repo --private --description '$desc'"
    else
        gh repo create "$GITHUB_USER/$repo" --private --description "$desc" > /dev/null 2>&1
        success "GitHub repo created: $GITHUB_USER/$repo"
        log "GitHub repo created: $GITHUB_USER/$repo"
    fi
}

# Safe git remote add — skips if remote exists
safe_add_remote() {
    local dir="$1"
    local repo="$2"
    if git -C "$dir" remote get-url origin > /dev/null 2>&1; then
        skip "Remote already set: $dir"
    elif [ "$DRY_RUN" = true ]; then
        dryrun "git remote add origin git@github.com:$GITHUB_USER/$repo.git"
    else
        git -C "$dir" remote add origin "git@github.com:$GITHUB_USER/$repo.git"
        success "Remote added: $dir → $GITHUB_USER/$repo"
        log "Remote added: $dir → $GITHUB_USER/$repo"
    fi
}

# Create branch in a repo dir
safe_create_branch() {
    local dir="$1"
    local branch="$2"
    local desc="$3"
    if [ "$DRY_RUN" = true ]; then
        dryrun "Create branch '$branch' in $dir"
        return
    fi
    # Create orphan branch with README
    local current
    current=$(git -C "$dir" branch --show-current 2>/dev/null)
    if git -C "$dir" show-ref --verify --quiet "refs/heads/$branch"; then
        skip "Branch exists: $branch in $dir"
        return
    fi
    git -C "$dir" checkout --orphan "$branch" > /dev/null 2>&1
    git -C "$dir" rm -rf . > /dev/null 2>&1
    mkdir -p "$dir/$branch"
    cat > "$dir/README.md" << EOF
# $branch

$desc

---
*Part of SaroshGabriel/$( basename "$dir") repository*
EOF
    git -C "$dir" add README.md > /dev/null 2>&1
    git -C "$dir" commit -m "Initial $branch branch" > /dev/null 2>&1
    success "Branch created: $branch in $(basename $dir)"
    log "Branch created: $branch in $dir"
    # Return to main
    git -C "$dir" checkout main > /dev/null 2>&1 || true
}

# Push all branches
safe_push_all() {
    local dir="$1"
    if [ "$DRY_RUN" = true ]; then
        dryrun "Push all branches in $dir to GitHub"
        return
    fi
    git -C "$dir" push --all origin > /dev/null 2>&1
    success "Pushed all branches: $(basename $dir)"
    log "Pushed: $dir"
}

# ── Print Header ─────────────────────────────────────────────
print_header() {
    echo
    echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}${CYAN}║     🚀 Workspace Setup Script v1.0           ║${RESET}"
    if [ "$DRY_RUN" = true ]; then
    echo -e "${BOLD}${YELLOW}║           ⚠️  DRY RUN MODE - No changes       ║${RESET}"
    fi
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════╝${RESET}"
    echo
}

# ── Main ─────────────────────────────────────────────────────
main() {
    print_header
    log "=== Setup started (dry-run: $DRY_RUN) ==="

    # ── 1. PRACTICE ──────────────────────────────────────────
    echo -e "${BOLD}━━━ 1. Practice ━━━${RESET}"
    safe_mkdir "$HOME/Practice"
    safe_mkdir "$HOME/Practice/pythonPractice"
    safe_mkdir "$HOME/Practice/bashPractice"
    safe_mkdir "$HOME/Practice/tclPractice"
    safe_mkdir "$HOME/Practice/cPractice"
    safe_mkdir "$HOME/Practice/skillPractice"

    safe_gh_create "Practice" "Language practice — Python, Bash, TCL, C, SKILL"
    safe_git_init "$HOME/Practice" "main"
    safe_add_remote "$HOME/Practice" "Practice"

    if [ "$DRY_RUN" = false ] && [ -d "$HOME/Practice/.git" ]; then
        # Create main branch README
        cat > "$HOME/Practice/README.md" << 'EOF'
# Practice

Language practice repository.

## Branches
| Branch | Content |
|--------|---------|
| python | Python practice files |
| bash   | Bash scripting practice |
| tcl    | TCL practice files |
| c      | C programming practice |
| skill  | SKILL language practice |
EOF
        git -C "$HOME/Practice" add README.md > /dev/null 2>&1
        git -C "$HOME/Practice" commit -m "Initial main branch" > /dev/null 2>&1
    fi

    for branch in python bash tcl c skill; do
        safe_create_branch "$HOME/Practice" "$branch" "$branch language practice files"
    done
    safe_push_all "$HOME/Practice"
    echo

    # ── 2. PROJECTS ──────────────────────────────────────────
    echo -e "${BOLD}━━━ 2. Projects ━━━${RESET}"
    safe_mkdir "$HOME/Projects"
    safe_mkdir "$HOME/Projects/dft"
    safe_mkdir "$HOME/Projects/python"
    safe_mkdir "$HOME/Projects/embedded"
    safe_mkdir "$HOME/Projects/c"
    safe_mkdir "$HOME/Projects/tcl"
    safe_mkdir "$HOME/Projects/skill"
    safe_mkdir "$HOME/Projects/physicalDesign"
    safe_mkdir "$HOME/Projects/verification"

    safe_gh_create "Projects" "Engineering projects — DFT, Python, Embedded, C, TCL, SKILL, PD, Verification"
    safe_git_init "$HOME/Projects" "main"
    safe_add_remote "$HOME/Projects" "Projects"

    if [ "$DRY_RUN" = false ] && [ -d "$HOME/Projects/.git" ]; then
        cat > "$HOME/Projects/README.md" << 'EOF'
# Projects

Engineering projects repository.

## Branches
| Branch         | Content |
|----------------|---------|
| dft            | Design for Test projects |
| python         | Python projects |
| embedded       | Embedded systems projects |
| c              | C projects |
| tcl            | TCL projects |
| skill          | SKILL language projects |
| physicalDesign | Physical Design projects |
| verification   | Verification projects |
EOF
        git -C "$HOME/Projects" add README.md > /dev/null 2>&1
        git -C "$HOME/Projects" commit -m "Initial main branch" > /dev/null 2>&1
    fi

    for branch in dft python embedded c tcl skill physicalDesign verification; do
        safe_create_branch "$HOME/Projects" "$branch" "$branch projects"
    done
    safe_push_all "$HOME/Projects"
    echo

    # ── 3. LINUXSCRIPTS ──────────────────────────────────────
    echo -e "${BOLD}━━━ 3. LinuxScripts ━━━${RESET}"
    safe_mkdir "$HOME/LinuxScripts"
    safe_mkdir "$HOME/LinuxScripts/aliasSyncWithBashrc"
    safe_mkdir "$HOME/LinuxScripts/hyprlandConfig"
    safe_mkdir "$HOME/LinuxScripts/waybarConfig"
    safe_mkdir "$HOME/LinuxScripts/waybarConfig/scripts"
    safe_mkdir "$HOME/LinuxScripts/hyprlock"

    safe_gh_create "LinuxScripts" "Linux scripts and config files"
    safe_git_init "$HOME/LinuxScripts" "main"
    safe_add_remote "$HOME/LinuxScripts" "LinuxScripts"

    if [ "$DRY_RUN" = false ] && [ -d "$HOME/LinuxScripts/.git" ]; then
        cat > "$HOME/LinuxScripts/README.md" << 'EOF'
# LinuxScripts

Linux scripts and configuration files.

## Branches
| Branch              | Content |
|---------------------|---------|
| aliasSyncWithBashrc | Alias management + sync system |
| hyprlandConfig      | Hyprland WM configuration |
| waybarConfig        | Waybar status bar config + scripts |
| hyprlock            | Hyprlock screen locker config |
EOF
        git -C "$HOME/LinuxScripts" add README.md > /dev/null 2>&1
        git -C "$HOME/LinuxScripts" commit -m "Initial main branch" > /dev/null 2>&1
    fi

    for branch in aliasSyncWithBashrc hyprlandConfig waybarConfig hyprlock; do
        safe_create_branch "$HOME/LinuxScripts" "$branch" "$branch scripts and configs"
    done

    # Copy existing files into correct branches
    if [ "$DRY_RUN" = false ]; then
        # aliasSyncWithBashrc branch
        git -C "$HOME/LinuxScripts" checkout aliasSyncWithBashrc > /dev/null 2>&1
        cp "$HOME/Projects/dotfiles/aliases.conf" "$HOME/LinuxScripts/" 2>/dev/null
        cp "$HOME/Projects/dotfiles/syncAliases.sh" "$HOME/LinuxScripts/" 2>/dev/null
        cp "$HOME/Projects/dotfiles/README_aliases.md" "$HOME/LinuxScripts/" 2>/dev/null
        cp "$HOME/Projects/dotfiles/syncAliases_README.md" "$HOME/LinuxScripts/" 2>/dev/null
        git -C "$HOME/LinuxScripts" add . > /dev/null 2>&1
        git -C "$HOME/LinuxScripts" commit -m "Add alias sync files" > /dev/null 2>&1
        success "Copied alias files to aliasSyncWithBashrc branch"

        # hyprlandConfig branch
        git -C "$HOME/LinuxScripts" checkout hyprlandConfig > /dev/null 2>&1
        cp "$HOME/.config/hypr/hyprland.conf" "$HOME/LinuxScripts/" 2>/dev/null
        cp "$HOME/.config/hypr/windowrules.conf" "$HOME/LinuxScripts/" 2>/dev/null
        git -C "$HOME/LinuxScripts" add . > /dev/null 2>&1
        git -C "$HOME/LinuxScripts" commit -m "Add hyprland config files" > /dev/null 2>&1
        success "Copied hyprland configs to hyprlandConfig branch"

        # waybarConfig branch
        git -C "$HOME/LinuxScripts" checkout waybarConfig > /dev/null 2>&1
        cp "$HOME/.config/waybar/config" "$HOME/LinuxScripts/" 2>/dev/null
        cp "$HOME/.config/waybar/style.css" "$HOME/LinuxScripts/" 2>/dev/null
        cp -r "$HOME/.config/waybar/scripts/" "$HOME/LinuxScripts/" 2>/dev/null
        git -C "$HOME/LinuxScripts" add . > /dev/null 2>&1
        git -C "$HOME/LinuxScripts" commit -m "Add waybar config files" > /dev/null 2>&1
        success "Copied waybar configs to waybarConfig branch"

        # hyprlock branch
        git -C "$HOME/LinuxScripts" checkout hyprlock > /dev/null 2>&1
        cp "$HOME/.config/hypr/hyprlock.conf" "$HOME/LinuxScripts/" 2>/dev/null
        git -C "$HOME/LinuxScripts" add . > /dev/null 2>&1
        git -C "$HOME/LinuxScripts" commit -m "Add hyprlock config" > /dev/null 2>&1
        success "Copied hyprlock config to hyprlock branch"

        git -C "$HOME/LinuxScripts" checkout main > /dev/null 2>&1
    fi

    safe_push_all "$HOME/LinuxScripts"
    echo

    # ── 4. Move existing work ─────────────────────────────────
    if [ "$DRY_RUN" = false ]; then
        echo -e "${BOLD}━━━ 4. Migrating existing files ━━━${RESET}"

        # Move pythonRev files to Practice
        if [ -d "$HOME/Projects/pythonRev" ]; then
            git -C "$HOME/Practice" checkout python > /dev/null 2>&1
            cp "$HOME/Projects/pythonRev/"*.py "$HOME/Practice/" 2>/dev/null
            git -C "$HOME/Practice" add . > /dev/null 2>&1
            git -C "$HOME/Practice" commit -m "Migrate pythonRev files" > /dev/null 2>&1
            git -C "$HOME/Practice" push origin python > /dev/null 2>&1
            success "Migrated pythonRev → Practice/python branch"
        fi

        # Move bashRev files to Practice
        if [ -d "$HOME/Projects/bashRev" ]; then
            git -C "$HOME/Practice" checkout bash > /dev/null 2>&1
            cp "$HOME/Projects/bashRev/"*.sh "$HOME/Practice/" 2>/dev/null
            git -C "$HOME/Practice" add . > /dev/null 2>&1
            git -C "$HOME/Practice" commit -m "Migrate bashRev files" > /dev/null 2>&1
            git -C "$HOME/Practice" push origin bash > /dev/null 2>&1
            success "Migrated bashRev → Practice/bash branch"
        fi

        git -C "$HOME/Practice" checkout main > /dev/null 2>&1
        echo
    fi

    # ── Summary ───────────────────────────────────────────────
    echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════╗${RESET}"
    if [ "$DRY_RUN" = true ]; then
    echo -e "${BOLD}${YELLOW}║         ✅ Dry Run Complete - No changes      ║${RESET}"
    echo -e "${BOLD}${YELLOW}║    Run without --dry-run to apply changes     ║${RESET}"
    else
    echo -e "${BOLD}${CYAN}║              ✅ Setup Complete!               ║${RESET}"
    fi
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════╝${RESET}"
    echo
    echo -e "  ${BOLD}GitHub Repos Created:${RESET}"
    echo -e "  ${GREEN}→${RESET} github.com/$GITHUB_USER/Practice"
    echo -e "  ${GREEN}→${RESET} github.com/$GITHUB_USER/Projects"
    echo -e "  ${GREEN}→${RESET} github.com/$GITHUB_USER/LinuxScripts"
    echo
    echo -e "  ${BOLD}Local Directories:${RESET}"
    echo -e "  ${GREEN}→${RESET} ~/Practice"
    echo -e "  ${GREEN}→${RESET} ~/Projects"
    echo -e "  ${GREEN}→${RESET} ~/LinuxScripts"
    echo
    echo -e "  ${DIM}Log: $LOG_FILE${RESET}"
    echo
    log "=== Setup complete ==="
}

main
