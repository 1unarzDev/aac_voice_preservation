#!/usr/bin/env bash
# Stops aacv-* containers if VRAM > 14000 MiB or GPU temp > 85C. Logs every 30s.
while true; do
  read mem temp < <(nvidia-smi --query-gpu=memory.used,temperature.gpu --format=csv,noheader,nounits | tr -d ',')
  echo "$(date +%T) mem=$mem temp=$temp" >> runs/gpu_watchdog.log
  if [ "$mem" -gt 14000 ] || [ "$temp" -gt 85 ]; then
    echo "$(date +%T) LIMIT EXCEEDED -> stopping aacv containers" >> runs/gpu_watchdog.log
    docker ps --format '{{.Names}}' | grep '^aacv-' | xargs -r docker stop
  fi
  sleep 30
done
