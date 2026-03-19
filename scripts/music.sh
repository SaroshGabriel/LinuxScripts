#!/bin/bash

# Check if Spotify is running
if playerctl -l 2>/dev/null | grep -q "spotify"; then
    STATUS=$(playerctl -p spotify status 2>/dev/null)
    ARTIST=$(playerctl -p spotify metadata artist 2>/dev/null)
    TITLE=$(playerctl -p spotify metadata title 2>/dev/null)
    
    if [ "$STATUS" = "Playing" ]; then
        ICON=""
    else
        ICON=""
    fi
    
    if [ -n "$ARTIST" ] && [ -n "$TITLE" ]; then
        echo "$ICON $ARTIST - $TITLE"
    else
        echo " Spotify"
    fi
else
    echo " Spotify"
fi
