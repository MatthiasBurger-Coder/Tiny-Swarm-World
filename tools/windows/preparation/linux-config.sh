#!/bin/sh
# Fixed bounded helper. Invoked only in an already-running selected distribution.
set -eu
mode=${1:-inspect}
expected=${2:-}
expected_metadata=${3:-}
file=/etc/wsl.conf
safe=true
if [ -L "$file" ]; then safe=false; fi
if [ -e "$file" ]; then
    [ -f "$file" ] || safe=false
    [ "$(stat -c '%u:%g' "$file")" = '0:0' ] || safe=false
    permissions=$(stat -c '%a' "$file")
    metadata=$(stat -c '%u:%g:%a' "$file")
    case "$permissions" in 600|640|644) ;; *) safe=false;; esac
    hash=$(sha256sum "$file" | cut -d ' ' -f 1)
else hash=absent; metadata=absent; fi
check_ini() {
    awk '
    /^[[:space:]]*[#;]/ || /^[[:space:]]*$/ {next}
    /^[[:space:]]*\[/ {
      line=$0; sub(/^[[:space:]]*/,"",line); sub(/[[:space:]]*$/,"",line)
      if(line !~ /^\[[A-Za-z0-9_.-]+\]$/) exit 2
      section=tolower(substr(line,2,length(line)-2)); if(sections[section]++) exit 2; next
    }
    {line=$0; p=index(line,"="); if(!p || !section) exit 2; key=substr(line,1,p-1); gsub(/^[[:space:]]+|[[:space:]]+$/,"",key); key=tolower(key); if(keys[section ":" key]++) exit 2}
    ' "$file"
}
if [ -e "$file" ] && ! check_ini; then safe=false; fi
configured=false
if [ "$safe" = true ] && [ -e "$file" ]; then
    if awk '/^[[:space:]]*\[/ {s=tolower($0);gsub(/[[:space:]]/,"",s)} s=="[boot]" && tolower($0) ~ /^[[:space:]]*systemd[[:space:]]*=/ {v=$0;sub(/^[^=]*=/,"",v);gsub(/[[:space:]]/,"",v); if(tolower(v)=="true") found=1} END {exit !found}' "$file"; then configured=true; fi
fi
if [ "$mode" = inspect ]; then
    ID=$(sed -n 's/^ID=\("\{0,1\}\)\([a-z0-9-]*\)\1$/\2/p' /etc/os-release)
    VERSION_ID=$(sed -n 's/^VERSION_ID=\("\{0,1\}\)\([0-9.]*\)\1$/\2/p' /etc/os-release)
    [ "$ID" = ubuntu ] && [ -n "$VERSION_ID" ] || exit 2
    printf 'linux_id=ubuntu\nrelease=%s\nlinux_architecture=%s\nconfig_safe=%s\nconfig_hash=%s\nconfig_metadata=%s\nsystemd_configured=%s\npid1=%s\n' "$VERSION_ID" "$(uname -m)" "$safe" "$hash" "$metadata" "$configured" "$(cat /proc/1/comm)"
    packages=false
    if dpkg-query -W -f='${Status}\n' systemd systemd-sysv 2>/dev/null | awk 'BEGIN{n=0} $0=="install ok installed"{n++} END{exit n!=2}'; then packages=true; fi
    printf 'systemd_packages=%s\n' "$packages"
    # Carry this existing running-only lifecycle observation into W06; its recheck never executes Linux.
    observed_address=$(hostname -I 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i ~ /^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$/){print $i;exit}}')
    printf 'observed_wsl_address=%s\n' "$observed_address"
    exit 0
fi
[ "$mode" = apply ] && [ "$safe" = true ] && [ "$hash" = "$expected" ] && [ "$metadata" = "$expected_metadata" ] || exit 2
# /etc lock inode is held throughout compare/replace; no unrelated file changes.
lock=/etc/.tsw-wsl-conf.lock
# Atomic directory acquisition never follows/truncates a preexisting inode.
umask 077
mkdir "$lock" 2>/dev/null || exit 2
[ ! -L "$lock" ] && [ "$(stat -c '%u:%g:%a' "$lock")" = '0:0:700' ] || exit 2
trap 'rmdir "$lock"' EXIT HUP INT TERM
if [ -e "$file" ]; then current=$(sha256sum "$file" | cut -d ' ' -f 1); else current=absent; fi
[ "$current" = "$expected" ] || exit 2
check_ini_if_present() { [ ! -e "$file" ] || check_ini; }
check_ini_if_present || exit 2
tmp=$(mktemp /etc/.tsw-wsl-conf.XXXXXX)
trap 'rm -f "$tmp"; rmdir "$lock"' EXIT HUP INT TERM
if [ -e "$file" ]; then
    awk '
    function finish(){if(boot && !key){print "systemd=true";key=1}}
    /^[[:space:]]*\[/ {finish(); s=tolower($0);gsub(/[[:space:]]/,"",s);boot=(s=="[boot]");if(boot) seen=1}
    boot && tolower($0) ~ /^[[:space:]]*systemd[[:space:]]*=/ {print "systemd=true";key=1;next}
    {print}
    END{finish();if(!seen){print "";print "[boot]";print "systemd=true"}}
    ' "$file" > "$tmp"
    # Keep private recovery bytes/metadata; never publish configuration contents.
    backup=$(mktemp /etc/.tsw-backup-wsl-conf.XXXXXX)
    cat "$file" > "$backup"
    chmod 600 "$backup"
    printf 'original_metadata=%s\noriginal_sha256=%s\n' "$metadata" "$hash" > "$backup.metadata"
    chmod 600 "$backup.metadata"
    sync -f "$backup"
    sync -f "$backup.metadata"
    chmod --reference="$file" "$tmp"
    chown --reference="$file" "$tmp"
else printf '[boot]\nsystemd=true\n' > "$tmp"; chmod 644 "$tmp"; chown 0:0 "$tmp"; fi
# Recheck hostile path/metadata and bytes before replacing.
[ ! -L "$file" ] || exit 2
if [ -e "$file" ]; then [ "$(sha256sum "$file" | cut -d ' ' -f 1)" = "$expected" ] && [ "$(stat -c '%u:%g:%a' "$file")" = "$metadata" ] || exit 2; else [ "$expected" = absent ] || exit 2; fi
sync -f "$tmp"
mv -T "$tmp" "$file"
sync -f /etc
