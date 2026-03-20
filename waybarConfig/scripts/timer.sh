#!/bin/bash
# ============================================================
# timer.sh - Waybar Timer Module
# Supports: Stopwatch (count up) + Countdown (count down)
# Controls: play/pause, reset, switch mode
# State stored in /tmp for waybar to read
# ============================================================

STATE_FILE="/tmp/waybar_timer_state"
TIME_FILE="/tmp/waybar_timer_time"
MODE_FILE="/tmp/waybar_timer_mode"
COUNTDOWN_FILE="/tmp/waybar_timer_countdown"

# Initialize files if they don't exist
[ ! -f "$STATE_FILE" ] && echo "stopped" > "$STATE_FILE"
[ ! -f "$TIME_FILE" ] && echo "0" > "$TIME_FILE"
[ ! -f "$MODE_FILE" ] && echo "stopwatch" > "$MODE_FILE"
[ ! -f "$COUNTDOWN_FILE" ] && echo "1500" > "$COUNTDOWN_FILE"  # 25 min default

get_state()    { cat "$STATE_FILE"; }
get_time()     { cat "$TIME_FILE"; }
get_mode()     { cat "$MODE_FILE"; }
get_countdown(){ cat "$COUNTDOWN_FILE"; }

format_time() {
    local total=$1
    local h=$((total / 3600))
    local m=$(( (total % 3600) / 60 ))
    local s=$((total % 60))
    if [ "$h" -gt 0 ]; then
        printf "%02d:%02d:%02d" "$h" "$m" "$s"
    else
        printf "%02d:%02d" "$m" "$s"
    fi
}

case "$1" in
    # ── Toggle play/pause ────────────────────────────────────
    toggle)
        state=$(get_state)
        if [ "$state" = "running" ]; then
            echo "paused" > "$STATE_FILE"
        else
            echo "running" > "$STATE_FILE"
            mode=$(get_mode)
            # Background ticker
            (
                while [ "$(get_state)" = "running" ]; do
                    sleep 1
                    if [ "$(get_state)" != "running" ]; then break; fi
                    t=$(get_time)
                    mode=$(get_mode)
                    if [ "$mode" = "stopwatch" ]; then
                        echo $((t + 1)) > "$TIME_FILE"
                    else
                        if [ "$t" -le 0 ]; then
                            echo "stopped" > "$STATE_FILE"
                            notify-send "⏰ Timer" "Countdown finished!" -u critical 2>/dev/null
                            break
                        fi
                        echo $((t - 1)) > "$TIME_FILE"
                    fi
                done
            ) &
        fi
        ;;

    # ── Reset ────────────────────────────────────────────────
    reset)
        echo "stopped" > "$STATE_FILE"
        mode=$(get_mode)
        if [ "$mode" = "stopwatch" ]; then
            echo "0" > "$TIME_FILE"
        else
            echo "$(get_countdown)" > "$TIME_FILE"
        fi
        ;;

    # ── Switch mode ──────────────────────────────────────────
    switch)
        echo "stopped" > "$STATE_FILE"
        mode=$(get_mode)
        if [ "$mode" = "stopwatch" ]; then
            echo "countdown" > "$MODE_FILE"
            echo "$(get_countdown)" > "$TIME_FILE"
        else
            echo "stopwatch" > "$MODE_FILE"
            echo "0" > "$TIME_FILE"
        fi
        ;;

    # ── Set countdown time ───────────────────────────────────
    set)
        # Usage: timer.sh set 25 (sets 25 minutes)
        minutes=${2:-25}
        seconds=$((minutes * 60))
        echo "$seconds" > "$COUNTDOWN_FILE"
        echo "$seconds" > "$TIME_FILE"
        echo "stopped" > "$STATE_FILE"
        echo "countdown" > "$MODE_FILE"
        ;;

    # ── Output for waybar ────────────────────────────────────
    status)
        state=$(get_state)
        mode=$(get_mode)
        time=$(get_time)
        formatted=$(format_time "$time")

        if [ "$mode" = "stopwatch" ]; then
            icon="⏱"
        else
            icon="⏳"
        fi

        if [ "$state" = "running" ]; then
            play_icon="⏸"
        else
            play_icon="▶"
        fi

        echo "{\"text\": \"$icon $formatted $play_icon\", \"class\": \"$state\", \"tooltip\": \"Mode: $mode | Click to play/pause | Right-click to reset\"}"
        ;;
esac
