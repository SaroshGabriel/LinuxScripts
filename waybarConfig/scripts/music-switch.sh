#!/bin/bash

# Get all players
PLAYERS=($(playerctl -l 2>/dev/null))

if [ ${#PLAYERS[@]} -eq 0 ]; then
    notify-send "🎵 Music" "No players available"
    exit 0
fi

# Get currently active player (the one that's playing)
CURRENT=""
for player in "${PLAYERS[@]}"; do
    STATUS=$(playerctl -p "$player" status 2>/dev/null)
    if [ "$STATUS" = "Playing" ]; then
        CURRENT="$player"
        break
    fi
done

# If nothing playing, use first player
if [ -z "$CURRENT" ]; then
    CURRENT="${PLAYERS[0]}"
fi

# Find current player index
CURRENT_INDEX=0
for i in "${!PLAYERS[@]}"; do
    if [[ "${PLAYERS[$i]}" == "$CURRENT" ]]; then
        CURRENT_INDEX=$i
        break
    fi
done

# Get next player (cycle)
NEXT_INDEX=$(( (CURRENT_INDEX + 1) % ${#PLAYERS[@]} ))
NEXT_PLAYER="${PLAYERS[$NEXT_INDEX]}"

# Switch to next player (pause current, unpause next)
playerctl -p "$CURRENT" pause 2>/dev/null
playerctl -p "$NEXT_PLAYER" play 2>/dev/null

# Show notification
PLAYER_NAME=$(echo "$NEXT_PLAYER" | sed 's/.*\.//' | sed 's/^./\u&/')
notify-send "🎵 Switched to" "$PLAYER_NAME"
