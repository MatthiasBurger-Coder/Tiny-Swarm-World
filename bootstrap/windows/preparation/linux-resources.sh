#!/bin/sh
# Read only; invoked only in an already running selected distribution.
set -eu
memory=$(awk '/^MemTotal:/{printf "%.0f",$2*1024}' /proc/meminfo)
swap=$(awk '/^SwapTotal:/{printf "%.0f",$2*1024}' /proc/meminfo)
# Present RAM pages exclude physical address holes; usable memory remains separate.
page_size=$(getconf PAGESIZE)
case "$page_size" in 4096|8192|16384|32768|65536) ;; *) exit 2 ;; esac
physical=$(awk -v size="$page_size" '
function finish() { if (zone != "" && !found) bad=1 }
/^Node/ {
    finish()
    if (NF != 4 || $1 != "Node" || $2 !~ /^[0-9]+,$/ || $3 != "zone") {bad=1; next}
    zone=$4; identity=$2 zone; found=0
    if (seen[identity]++) bad=1
    if (zone !~ /^(DMA|DMA32|Normal|HighMem|Movable|Device)$/) bad=1
    zones++
    next
}
$1 == "present" {
    if (zone == "" || found++ || NF != 2 || $2 !~ /^[0-9]+$/ || length($2) > 16) {bad=1; next}
    pages=$2+0
    if (pages > int(9007199254740991/size)) {bad=1; next}
    if (zone != "Device") total+=pages
    if (total > int(9007199254740991/size)) bad=1
}
END {
    finish()
    if (bad || !zones || total <= 0) exit 2
    printf "%.0f", total*size
}' /proc/zoneinfo) || exit 2
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
printf 'effective_physical_memory_bytes=%s\neffective_memory_bytes=%s\neffective_swap_bytes=%s\neffective_processors=%s\n' "$physical" "$memory" "$swap" "$(nproc)"
df -B1 --output=avail / | awk 'NR==2{printf "effective_disk_bytes=%.0f\n",$1}'
