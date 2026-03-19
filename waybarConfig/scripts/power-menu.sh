#!/bin/bash
chosen=$(echo -e "⏻ Shutdown\n Reboot\n Logout\n Lock" | rofi -dmenu -p "Power")
case $chosen in
    "⏻ Shutdown") systemctl poweroff ;;
    " Reboot") systemctl reboot ;;
    " Logout") hyprctl dispatch exit ;;
    " Lock") hyprlock ;;
esac
