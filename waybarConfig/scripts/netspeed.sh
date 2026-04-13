#!/bin/bash
rx1=$(cat /proc/net/dev | awk 'NR>2{rx+=$2} END{print rx}')
tx1=$(cat /proc/net/dev | awk 'NR>2{tx+=$10} END{print tx}')
sleep 1
rx2=$(cat /proc/net/dev | awk 'NR>2{rx+=$2} END{print rx}')
tx2=$(cat /proc/net/dev | awk 'NR>2{tx+=$10} END{print tx}')
echo "$rx1 $rx2 $tx1 $tx2" | awk '{
    rx=($2-$1)/1024/1024;
    tx=($4-$3)/1024/1024;
    printf "↓%.2fM ↑%.2fM\n", rx, tx
}'
