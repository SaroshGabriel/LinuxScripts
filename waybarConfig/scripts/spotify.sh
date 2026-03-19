#!/bin/bash
# Spotify now playing
STATUS=$(playerctl --player=spotify status 2>/dev/null)
if [ "$STATUS" = "Playing" ] || [ "$STATUS" = "Paused" ]; then
    ARTIST=$(playerctl --player=spotify metadata artist 2>/dev/null)
    TITLE=$(playerctl --player=spotify metadata title 2>/dev/null)
    echo "{\"text\": \"  $ARTIST - $TITLE\", \"class\": \"$STATUS\"}"
else
    echo "{\"text\": \"\", \"class\": \"stopped\"}"
fi
