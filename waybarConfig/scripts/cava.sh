#!/bin/bash

# Cava for waybar - shows visualizer bars

# Create named pipe if it doesn't exist
FIFO="/tmp/cava.fifo"
if [[ ! -p $FIFO ]]; then
    mkfifo $FIFO
fi

# Kill existing cava instance
pkill -f "cava -p"

# Start cava in background
cava -p ~/.config/cava/config_waybar > $FIFO &

# Read from pipe and format for waybar
while read -r line; do
    # Get music status
    STATUS=$(playerctl status 2>/dev/null || echo "Stopped")
    
    if [[ "$STATUS" == "Playing" ]]; then
        # Show visualizer bars
        echo "{\"text\":\"$line\", \"class\":\"playing\"}"
    else
        # Show paused/stopped icon
        echo "{\"text\":\"⏸\", \"class\":\"paused\"}"
    fi
done < $FIFO
