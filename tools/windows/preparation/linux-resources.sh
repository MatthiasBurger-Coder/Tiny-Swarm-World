#!/bin/sh
# Read only; invoked only in an already running selected distribution.
set -eu
memory=$(awk '/^MemTotal:/{printf "%.0f",$2*1024}' /proc/meminfo)
swap=$(awk '/^SwapTotal:/{printf "%.0f",$2*1024}' /proc/meminfo)
scope=$(awk -F: '$1=="0" && $2==""{print $3}' /proc/self/cgroup)
case "$scope" in /*) ;; *) exit 2 ;; esac
case "$scope" in *..*|*\\*) exit 2 ;; esac
cgroup=/sys/fs/cgroup$scope
cgroup=${cgroup%/}
while :; do
    # The unified root has no memory controller limit interface on Linux.
    # Only its absence there is expected; all non-root ancestors must be known.
    if [ "$cgroup" = /sys/fs/cgroup ] && [ ! -e "$cgroup/memory.max" ]; then break; fi
    [ -r "$cgroup/memory.max" ] || exit 2
    limit=$(cat "$cgroup/memory.max")
    case "$limit" in max) ;; ''|*[!0-9]*) exit 2 ;; *) if [ "$limit" -lt "$memory" ]; then memory=$limit; fi ;; esac
    [ "$cgroup" = /sys/fs/cgroup ] && break
    cgroup=${cgroup%/*}
done
printf 'effective_memory_bytes=%s\neffective_swap_bytes=%s\neffective_processors=%s\n' "$memory" "$swap" "$(nproc)"
df -B1 --output=avail / | awk 'NR==2{printf "effective_disk_bytes=%.0f\n",$1}'
