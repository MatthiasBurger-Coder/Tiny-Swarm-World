#!/usr/bin/env bash
# Minimal interpreter boundary; full package planning belongs to the Python service.
tsw_python_prerequisites() {
  local read_only=0 release_id='' release_version='' key value kernel profile=service-access
  local -a missing=() before=() candidates=() verified=()
  local fingerprint evidence_path state_directory
  for value in "$@"; do
    case "$value" in
      --help|-h)
        printf 'Usage: ./prepare_linux.sh [--preflight|--dry-run] [--service-profile default|service-access]\nPrepare Ubuntu 24.04/26.04 native or WSL2 Linux prerequisites and Incus readiness.\nApply prompts separately for packages, user Python, Incus startup/access and resolved resources. New Incus group access requires logout/login. Existing resources are preserved. Services are not verified.\nNext: ./prepare_linux.sh --dry-run\n'
        return 10 ;;
      --preflight|--dry-run)
        ((read_only == 0)) || { printf 'BLOCKED: Choose one read-only mode.\n' >&2; return 2; }
        read_only=1 ;;
    esac
  done
  # Validate all arguments before even minimal APT work.
  while (($#)); do
    case "$1" in
      --preflight|--dry-run) shift ;;
      --service-profile)
        [[ "${2:-}" == default || "${2:-}" == service-access ]] || { printf 'BLOCKED: Invalid profile. Next: ./prepare_linux.sh --help\n' >&2; return 2; }
        profile="$2"; shift 2 ;;
      *) printf 'BLOCKED: Unknown argument. Next: ./prepare_linux.sh --help\n' >&2; return 2 ;;
    esac
  done
  [[ "$(uname -s)" == Linux && "$(uname -m)" == x86_64 ]] || { printf 'BLOCKED: Ubuntu x86_64 Linux is required.\n' >&2; return 2; }
  while IFS='=' read -r key value; do
    value="${value%\"}"; value="${value#\"}"
    case "$key" in ID) release_id="$value" ;; VERSION_ID) release_version="$value" ;; esac
  done < /etc/os-release
  [[ "$release_id" == ubuntu && ( "$release_version" == 24.04 || "$release_version" == 26.04 ) ]] || { printf 'BLOCKED: Ubuntu 24.04 or 26.04 is required before APT.\n' >&2; return 2; }
  kernel="$(uname -r)"
  if [[ "${kernel,,}" == *microsoft* || "${kernel,,}" == *wsl* ]]; then
    [[ "${kernel,,}" == *microsoft-standard* && -d /run/systemd/system ]] || { printf 'BLOCKED: WSL2 with systemd is required. Next: ./prepare_linux.sh --dry-run after WSL preparation.\n' >&2; return 2; }
  fi
  [[ -f requirements.lock && -f requirements.build.lock && -f pyproject.toml && -f src/tiny_swarm_world/prepare_linux.py ]] || { printf 'BLOCKED: Release assets missing. Extract the complete trusted release and run ./prepare_linux.sh --dry-run.\n' >&2; return 2; }
  if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 12))' >/dev/null 2>&1; then
    return 0
  fi
  tsw_shell_assets_and_paths || { printf 'BLOCKED: Unsafe release assets, lock or venv. Next: ./prepare_linux.sh --dry-run from a complete owned release.\n' >&2; return 2; }
  for value in python3 python3-venv; do
    if [[ "$(timeout 10 dpkg-query --show '--showformat=${Status}' -- "$value" 2>/dev/null || true)" != 'install ok installed' ]]; then missing+=("$value"); fi
  done
  # An installed but unusable interpreter must not trigger an implicit upgrade/reinstall.
  ((${#missing[@]})) || { printf 'BLOCKED: Installed Python is unusable or older than 3.12. Inspect python3, then run ./prepare_linux.sh --dry-run.\n' >&2; return 2; }
  printf 'Interpreter prerequisite plan: %s\n' "${missing[*]}"
  if ((read_only)); then
    printf 'BLOCKED: Python bootstrap required. No changes made. Next: ./prepare_linux.sh\n'
    return 2
  fi
  [[ "$EUID" != 0 ]] || { printf 'BLOCKED: Run preparation as an ordinary user; only APT elevates.\n' >&2; return 2; }
  tsw_minimum_capacity "$profile" "$kernel" || return 2
  fingerprint="$(tsw_shell_fingerprint)"
  state_directory="${XDG_STATE_HOME:-$HOME/.local/state}/tiny-swarm-world/evidence/native-preparation"
  tsw_evidence_guard "$state_directory" || { printf 'BLOCKED: Evidence storage is unsafe.\n' >&2; return 2; }
  printf 'Plan: Ubuntu index refresh (900s), candidate review, separately approved install (1800s). Lock/network timeout 30s; retries 0.\n'
  local answer=''
  read -r -p "Refresh Ubuntu APT indexes, then review interpreter candidates? Type 'yes': " answer || true
  [[ "$answer" == yes ]] || { printf 'BLOCKED: Consent missing. Next: ./prepare_linux.sh\n' >&2; return 2; }
  before=("${missing[@]}")
  missing=()
  for value in "${before[@]}"; do
    if [[ "$(timeout 10 dpkg-query --show '--showformat=${Status}' -- "$value" 2>/dev/null || true)" != 'install ok installed' ]]; then missing+=("$value"); fi
  done
  [[ "${before[*]}" == "${missing[*]}" ]] || { printf 'BLOCKED: Package plan changed. Next: ./prepare_linux.sh --dry-run\n' >&2; return 2; }
  tsw_shell_assets_and_paths && [[ "$(tsw_shell_fingerprint)" == "$fingerprint" ]] || { printf 'BLOCKED: Target or assets changed after consent.\n' >&2; return 2; }
  command -v timeout >/dev/null && command -v sudo >/dev/null || { printf 'BLOCKED: timeout and sudo are required.\n' >&2; return 2; }
  umask 077
  mkdir -p "$state_directory" || return 2
  tsw_evidence_guard "$state_directory" || return 2
  evidence_path="$(mktemp "$state_directory/interpreter-XXXXXX")" || return 2
  printf 'stage=interpreter_packages\nstatus=started\nrelease=%s\nplanned=%s\n' "$release_version" "${missing[*]}" > "$evidence_path" || { printf 'BLOCKED: Interpreter evidence write failed; no APT ran.\n' >&2; return 2; }
  printf 'Protected interpreter evidence: %s\n' "$evidence_path"
  if ! timeout 900 sudo -n apt-get -o DPkg::Lock::Timeout=30 -o Acquire::Retries=0 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30 -o APT::Update::Error-Mode=any update >/dev/null 2>&1; then
    tsw_interpreter_partial "$evidence_path" "${missing[@]}"; return 4
  fi
  for value in "${missing[@]}"; do
    key="$(timeout 10 apt-cache policy -- "$value" 2>/dev/null | awk '/^[[:space:]]*Candidate:/ {print $2}')"
    [[ "$key" =~ ^[A-Za-z0-9.+:~_-]+$ ]] || { tsw_interpreter_partial "$evidence_path" "${missing[@]}"; return 4; }
    candidates+=("$value=$key")
  done
  printf 'Index refresh completed; Ubuntu candidates: %s\n' "${candidates[*]}"
  answer=''
  read -r -p "Install these exact interpreter candidates? Type 'yes': " answer || true
  [[ "$answer" == yes ]] || { tsw_interpreter_partial "$evidence_path" "${missing[@]}"; return 4; }
  tsw_shell_assets_and_paths && [[ "$(tsw_shell_fingerprint)" == "$fingerprint" ]] && tsw_minimum_capacity "$profile" "$kernel" || { tsw_interpreter_partial "$evidence_path" "${missing[@]}"; return 4; }
  for value in "${missing[@]}"; do
    [[ "$(timeout 10 dpkg-query --show '--showformat=${Status}' -- "$value" 2>/dev/null || true)" != 'install ok installed' ]] || { tsw_interpreter_partial "$evidence_path" "${missing[@]}"; return 4; }
    key="$(timeout 10 apt-cache policy -- "$value" 2>/dev/null | awk '/^[[:space:]]*Candidate:/ {print $2}')"
    verified+=("$value=$key")
  done
  [[ "${candidates[*]}" == "${verified[*]}" ]] || { tsw_interpreter_partial "$evidence_path" "${missing[@]}"; return 4; }
  if ! timeout 1800 sudo -n apt-get -o DPkg::Lock::Timeout=30 -o Acquire::Retries=0 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30 install --yes --no-install-recommends --no-upgrade -- "${candidates[@]}" >/dev/null 2>&1; then
    tsw_interpreter_partial "$evidence_path" "${missing[@]}"; return 4
  fi
  if ! python3 -c 'import sys, venv; raise SystemExit(sys.version_info < (3, 12))' >/dev/null 2>&1; then
    tsw_interpreter_partial "$evidence_path" "${missing[@]}"; return 4
  fi
  printf 'status=succeeded\n' >> "$evidence_path" || { printf 'PARTIAL: Interpreter prepared but evidence write failed. Next: ./prepare_linux.sh --dry-run\n' >&2; return 4; }
  return 0
}

# Only the minimum interpreter guard lives here; Python owns the full host plan.
tsw_minimum_capacity() {
  local cpus memory=0 available='' key value rest
  local minimum_cpus=8 minimum_memory=15728640 minimum_disk=157286400
  if [[ "$1" == default ]]; then minimum_cpus=4; minimum_memory=16777216; minimum_disk=62914560; fi
  if [[ "${2,,}" == *microsoft* || "${2,,}" == *wsl* ]]; then minimum_memory=16777216; fi
  cpus="$(getconf _NPROCESSORS_ONLN)"
  while read -r key value rest; do [[ "$key" == MemTotal: ]] && memory="$value"; done < /proc/meminfo
  available="$(df -Pk . | awk 'NR == 2 {print $4}')"
  [[ "$cpus" =~ ^[0-9]+$ && "$memory" =~ ^[0-9]+$ && "$available" =~ ^[0-9]+$ ]] || { printf 'BLOCKED: Capacity facts unavailable.
' >&2; return 2; }
  ((cpus >= minimum_cpus && memory >= minimum_memory && available >= minimum_disk)) || { printf 'BLOCKED: Insufficient profile capacity. Next: ./prepare_linux.sh --dry-run after providing capacity.
' >&2; return 2; }
}


tsw_shell_assets_and_paths() {
  local path existing asset
  [[ -w . && -O . && "$PWD" != /mnt/[a-z]/* ]] || return 1
  for asset in requirements.lock requirements.build.lock pyproject.toml src/tiny_swarm_world/prepare_linux.py; do
    [[ -f "$asset" && -O "$asset" && ! -L "$asset" ]] || return 1
    path="$PWD/$asset"
    while [[ "$path" != / ]]; do [[ ! -L "$path" ]] || return 1; path="${path%/*}"; [[ -n "$path" ]] || path=/; done
  done
  for asset in requirements.lock requirements.build.lock; do
    awk '
      { line=$0; sub(/#.*/, "", line); continuation=sub(/\\[[:space:]]*$/, "", line); logical=logical " " line; if (continuation) next;
        sub(/^[[:space:]]+/, "", logical); sub(/[[:space:]]+$/, "", logical);
        if (logical != "") {
          count=split(logical, fields, /[[:space:]]+/);
          if (count < 2 || fields[1] !~ /^[A-Za-z0-9_.-]+==[^[:space:];]+$/) exit 1;
          for (i=2;i<=count;i++) if (fields[i] !~ /^--hash=sha256:[a-f0-9]+$/ || length(fields[i]) != 78) exit 1;
          entries++;
        } logical="";
      }
      END { if (!entries || logical != "") exit 1 }
    ' "$asset" || return 1
  done
  path="${TSW_NATIVE_LINUX_VENV:-$PWD/.tiny-swarm-world/install-venv}"
  [[ "$path" == /* ]] || path="$PWD/$path"
  [[ "$path" != /mnt/[a-z]/* ]] || return 1
  existing="$path"
  while [[ "$existing" != / ]]; do [[ ! -L "$existing" ]] || return 1; existing="${existing%/*}"; [[ -n "$existing" ]] || existing=/; done
  existing="$path"
  while [[ ! -e "$existing" ]]; do existing="${existing%/*}"; [[ -n "$existing" ]] || existing=/; done
  [[ -O "$existing" && -w "$existing" ]] || return 1
  if [[ -e "$path" ]]; then
    [[ -d "$path" && -f "$path/pyvenv.cfg" && ! -L "$path/pyvenv.cfg" ]] || return 1
    asset="$(timeout 10 find "$path" ! -uid "$EUID" -print -quit)" || return 1
    [[ -z "$asset" ]] || return 1
  fi
}

tsw_shell_fingerprint() {
  uname -s -m -r
  [[ -d /run/systemd/system ]] && printf 'systemd_present\n' || printf 'systemd_absent\n'
  sha256sum /etc/os-release requirements.lock requirements.build.lock pyproject.toml
  stat -c '%d:%i:%u' .
  printf '%s\n' "${TSW_NATIVE_LINUX_VENV:-.tiny-swarm-world/install-venv}"
}

tsw_evidence_guard() {
  local path="$1" existing="$1"
  while [[ "$existing" != / ]]; do [[ ! -L "$existing" ]] || return 1; existing="${existing%/*}"; [[ -n "$existing" ]] || existing=/; done
  existing="$path"
  while [[ ! -e "$existing" ]]; do existing="${existing%/*}"; [[ -n "$existing" ]] || existing=/; done
  [[ -O "$existing" && -w "$existing" ]] || return 1
  for existing in "$path" "${path%/*}" "${path%/evidence/*}"; do
    if [[ -e "$existing" ]]; then [[ "$(stat -c '%a:%u:%g' "$existing")" == "700:$EUID:$(id -g)" ]] || return 1; fi
  done
}

tsw_interpreter_partial() {
  local evidence="$1" package status
  shift
  printf 'status=partial\nindex_changes=possible\n' >> "$evidence" || printf 'PARTIAL: Protected evidence write also failed.\n' >&2
  printf 'PARTIAL: Interpreter preparation stopped; indexes may have changed. No later stages ran.\n' >&2
  for package in "$@"; do
    status="$(timeout 10 dpkg-query --show '--showformat=${Status}' -- "$package" 2>/dev/null || true)"
    [[ "$status" == 'install ok installed' ]] && status=installed || status=missing_or_unknown
    printf 'Observed %s: %s\n' "$package" "$status" | tee -a "$evidence" >&2
  done
  printf 'Next: ./prepare_linux.sh --dry-run (inspect connectivity/APT locks; do not delete locks).\n' >&2
}
