#!/bin/bash

# Check if Spotify is running
if ! playerctl -l 2>/dev/null | grep -q "spotify"; then
    notify-send "🎵 Spotify" "Spotify is not running"
    exit 0
fi

# Get Spotify info
STATUS=$(playerctl -p spotify status 2>/dev/null)
ARTIST=$(playerctl -p spotify metadata artist 2>/dev/null)
TITLE=$(playerctl -p spotify metadata title 2>/dev/null)
ALBUM=$(playerctl -p spotify metadata album 2>/dev/null)
ART_URL=$(playerctl -p spotify metadata mpris:artUrl 2>/dev/null)

# Download album art (smaller size)
ALBUM_ART="/tmp/spotify_cover.jpg"
if [ -n "$ART_URL" ]; then
    curl -s "$ART_URL" -o "$ALBUM_ART" 2>/dev/null
    # Resize to 200x200
    convert "$ALBUM_ART" -resize 200x200 "$ALBUM_ART" 2>/dev/null
fi

# Show compact floating window
yad --form \
    --title="🎵 Spotify" \
    --width=350 \
    --height=320 \
    --center \
    --borders=20 \
    --image="$ALBUM_ART" \
    --image-on-top \
    --text="<b>$TITLE</b>\n<i>$ARTIST</i>\n<small>$ALBUM</small>" \
    --button="⏮:bash -c 'playerctl -p spotify previous'" \
    --button="⏯:bash -c 'playerctl -p spotify play-pause'" \
    --button="⏭:bash -c 'playerctl -p spotify next'" \
    --button="✖:0" \
    --skip-taskbar \
    --on-top \
    --undecorated

# Clean up
rm -f "$ALBUM_ART"
