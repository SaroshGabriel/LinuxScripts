#!/bin/bash
TIME=$(date "+%I:%M:%S %p")
DAY=$(date "+%A")
DATE=$(date "+%d %B %Y")
echo "{\"text\": \"<span color='#EF3946'>$TIME</span>  <span color='#50fa7b'>$DAY</span>  <span color='#ffb86c'>$DATE</span>\", \"class\": \"clock\"}"
