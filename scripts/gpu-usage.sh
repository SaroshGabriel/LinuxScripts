#!/bin/bash

# Get GPU usage percentage
gpu_usage=$(cat /sys/class/drm/card0/device/gpu_busy_percent 2>/dev/null || echo "0")

# Get GPU temperature (from amdgpu hwmon1 or hwmon2)
gpu_temp=$(cat /sys/class/hwmon/hwmon1/temp1_input 2>/dev/null || cat /sys/class/hwmon/hwmon2/temp1_input 2>/dev/null || echo "0")
gpu_temp=$((gpu_temp / 1000))

# Get VRAM usage
vram_used=$(cat /sys/class/drm/card0/device/mem_info_vram_used 2>/dev/null || echo "0")
vram_total=$(cat /sys/class/drm/card0/device/mem_info_vram_total 2>/dev/null || echo "1")

# Convert to MB
vram_used_mb=$((vram_used / 1024 / 1024))
vram_total_mb=$((vram_total / 1024 / 1024))

# Calculate percentage
if [ "$vram_total_mb" -gt 0 ]; then
    vram_percent=$((vram_used_mb * 100 / vram_total_mb))
else
    vram_percent=0
fi

# Output JSON for Waybar
echo "{\"text\":\"󰢮 ${gpu_usage}%\", \"tooltip\":\"GPU: ${gpu_usage}%\\nTemp: ${gpu_temp}°C\\nVRAM: ${vram_used_mb}MB / ${vram_total_mb}MB (${vram_percent}%)\"}"
