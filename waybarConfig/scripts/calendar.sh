#!/bin/bash

# Kill any existing calendar popup
pkill -f "yad.*Calendar"

# Show calendar with much larger window for better spacing
yad --calendar \
    --title="📅 Calendar" \
    --width=480 \
    --height=420 \
    --center \
    --borders=20 \
    --undecorated \
    --button="Close:0" \
    --skip-taskbar \
    --on-top \
    --show-weeks \
    --day=$(date +%d) \
    --month=$(date +%m) \
    --year=$(date +%Y)
