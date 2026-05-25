<#
Tiny Swarm World - WSL2 prerequisite preparation for the LXC/LXD/Incus provider path.

This script prepares the Windows/WSL side for the future LXC-native setup path.

It can:
- verify WSL availability
- update WSL
- select a WSL distribution
- convert the selected distribution to WSL2
- enable systemd in /etc/wsl.conf
- optionally configure %UserProfile%\.wslconfig
- collect diagnostic evidence
- optionally check whether LXD or Incus is already available inside WSL

It does not:
- create LXC/LXD/Incus containers
- create Docker Swarm nodes
- install Docker Swarm
- install LXD/Incus automatically
- mutate Windows portproxy/netsh rules
#>

[CmdletBinding()]
param(
    [string]$DistroName = "",

    [ValidateSet("none", "lxd", "incus")]
    [string]$Provider = "none",

    [switch]$CheckOnly,

    [switch]$SkipWslUpdate,

    [bool]$ConvertToWsl2 = $true,

    [bool]$EnableSystemd = $true,

    [switch]$ConfigureWslConfig,

    [bool]$ShutdownAfterChange = $true,

    [switch]$Force,

    [string]$EvidenceDirectory = ".tiny-swarm-world\evidence\windows-wsl-prereq"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Script:ChangedWslConfiguration = $false
$Script:HadWarnings = $false
$Script:HadErrors = $false

function Write-Section {
    param([string]$Title)

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkGray
    Write-Host $Title -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkGray
}

function Write-Ok {
    param([string]$Message)

    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)

    $Script:HadWarnings = $true
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Fail {
    param([string]$Message)

    $Script:HadErrors = $true
    Write-Host "[FAIL] $Message" -ForegroundColor Red
}

function Invoke-External {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [switch]$IgnoreExitCode
    )

    Write-Host "> $FilePath $($Arguments -join ' ')" -ForegroundColor DarkGray

    $output = & $FilePath @Arguments 2>&1
    $exitCode = $LASTEXITCODE

    if ($null -ne $output) {
        $output | ForEach-Object { Write-Host $_ }
    }

    if ($exitCode -ne 0 -and -not $IgnoreExitCode) {
        throw "Command failed with exit code ${exitCode}: $FilePath $($Arguments -join ' ')"
    }

    return [pscustomobject]@{
        ExitCode = $exitCode
        Output   = (($output | ForEach-Object { "$_" }) -join "`n")
    }
}

function Invoke-WslBash {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Distro,

        [Parameter(Mandatory = $true)]
        [string]$ScriptText,

        [switch]$AsRoot,

        [switch]$IgnoreExitCode
    )

    # Normalize Windows CRLF/CR line endings before passing the script to Bash.
    # Without this, Bash can read "set -e\r" and fail with an error like:
    # "bash: line 1: set: -"
    $normalizedScriptText = $ScriptText.Replace("`r`n", "`n").Replace("`r", "`n")
    $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($normalizedScriptText))
    $bashCommand = "printf '%s' '$encoded' | base64 -d | bash"

    $args = @("-d", $Distro)

    if ($AsRoot) {
        $args += @("-u", "root")
    }

    $args += @("--", "bash", "-lc", $bashCommand)

    return Invoke-External -FilePath "wsl.exe" -Arguments $args -IgnoreExitCode:$IgnoreExitCode
}

function Get-WslDistributions {
    $result = Invoke-External -FilePath "wsl.exe" -Arguments @("-l", "-v") -IgnoreExitCode

    if ($result.ExitCode -ne 0) {
        throw "Could not list WSL distributions. Is WSL installed?"
    }

    $cleanOutput = $result.Output -replace "`0", ""
    $distros = @()

    foreach ($rawLine in ($cleanOutput -split "`n")) {
        $line = $rawLine.TrimEnd()

        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        if ($line -match "^\s*NAME\s+STATE\s+VERSION\s*$") {
            continue
        }

        $isDefault = $line.TrimStart().StartsWith("*")
        $withoutMarker = ($line -replace "^\s*\*\s*", "").Trim()

        if ($withoutMarker -match "^(?<Name>.+?)\s{2,}(?<State>\S+)\s+(?<Version>[12])\s*$") {
            $distros += [pscustomobject]@{
                Name      = $Matches["Name"].Trim()
                State     = $Matches["State"].Trim()
                Version   = [int]$Matches["Version"]
                IsDefault = $isDefault
            }
        }
    }

    return $distros
}

function Select-WslDistribution {
    param(
        [object[]]$Distributions,
        [string]$RequestedName
    )

    if ($Distributions.Count -eq 0) {
        throw "No WSL distributions were found. Install an Ubuntu WSL distribution first."
    }

    if (-not [string]::IsNullOrWhiteSpace($RequestedName)) {
        $match = $Distributions | Where-Object { $_.Name -eq $RequestedName } | Select-Object -First 1

        if ($null -eq $match) {
            $available = ($Distributions | ForEach-Object { $_.Name }) -join ", "
            throw "Requested WSL distro '$RequestedName' was not found. Available: $available"
        }

        return $match
    }

    $default = $Distributions | Where-Object { $_.IsDefault } | Select-Object -First 1

    if ($null -ne $default) {
        return $default
    }

    $ubuntu = $Distributions | Where-Object { $_.Name -like "Ubuntu*" } | Select-Object -First 1

    if ($null -ne $ubuntu) {
        return $ubuntu
    }

    return ($Distributions | Select-Object -First 1)
}

function Confirm-Action {
    param(
        [string]$Prompt,
        [switch]$DefaultNo
    )

    if ($Force) {
        return $true
    }

    $suffix = if ($DefaultNo) { "[y/N]" } else { "[Y/n]" }
    $answer = Read-Host "$Prompt $suffix"

    if ([string]::IsNullOrWhiteSpace($answer)) {
        return (-not $DefaultNo)
    }

    return ($answer.Trim().ToLowerInvariant() -in @("y", "yes", "j", "ja"))
}

function Set-WslConfSystemd {
    param([string]$Distro)

    $scriptText = @'
set -e

CONF="/etc/wsl.conf"
BACKUP="/etc/wsl.conf.tsw-backup-$(date +%Y%m%d%H%M%S)"

if [ -f "$CONF" ]; then
  cp "$CONF" "$BACKUP"
fi

if command -v python3 >/dev/null 2>&1; then
python3 - <<'PY'
from pathlib import Path

path = Path("/etc/wsl.conf")
old = path.read_text(encoding="utf-8") if path.exists() else ""
lines = old.splitlines()

out = []
in_boot = False
boot_seen = False
systemd_written = False

for line in lines:
    stripped = line.strip()
    lower = stripped.lower()

    if stripped.startswith("[") and stripped.endswith("]"):
        if in_boot and not systemd_written:
            out.append("systemd=true")
            systemd_written = True

        section_name = stripped[1:-1].strip().lower()
        in_boot = section_name == "boot"

        if in_boot:
            boot_seen = True

        out.append(line)
        continue

    if in_boot and lower.startswith("systemd"):
        out.append("systemd=true")
        systemd_written = True
        continue

    out.append(line)

if in_boot and not systemd_written:
    out.append("systemd=true")
    systemd_written = True

if not boot_seen:
    if out and out[-1].strip():
        out.append("")
    out.append("[boot]")
    out.append("systemd=true")

new = "\n".join(out).rstrip() + "\n"

if new != old:
    path.write_text(new, encoding="utf-8")
PY
else
  if [ ! -f "$CONF" ]; then
    printf '[boot]\nsystemd=true\n' > "$CONF"
  elif ! grep -qiE '^[[:space:]]*systemd[[:space:]]*=[[:space:]]*true[[:space:]]*$' "$CONF"; then
    printf '\n[boot]\nsystemd=true\n' >> "$CONF"
  fi
fi

echo "Current /etc/wsl.conf:"
cat "$CONF"
'@

    Invoke-WslBash -Distro $Distro -ScriptText $scriptText -AsRoot | Out-Null
}

function Test-WslSystemd {
    param([string]$Distro)

    $scriptText = @'
if [ -d /run/systemd/system ]; then
  systemctl is-system-running || true
else
  echo "systemd-runtime-not-detected"
fi
'@

    Invoke-WslBash -Distro $Distro -ScriptText $scriptText -IgnoreExitCode | Out-Null
}

function Set-IniValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Section,

        [Parameter(Mandatory = $true)]
        [string]$Key,

        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    $lines = @()

    if (Test-Path $Path) {
        $lines = Get-Content -Path $Path
    }

    $out = New-Object System.Collections.Generic.List[string]
    $inSection = $false
    $sectionFound = $false
    $keyWritten = $false
    $keyPattern = "^\s*" + [regex]::Escape($Key) + "\s*="

    foreach ($line in $lines) {
        $trim = $line.Trim()

        if ($trim -match "^\[(.+)\]\s*$") {
            if ($inSection -and -not $keyWritten) {
                $out.Add("$Key=$Value")
                $keyWritten = $true
            }

            $currentSection = $Matches[1].Trim()
            $inSection = ($currentSection.ToLowerInvariant() -eq $Section.ToLowerInvariant())

            if ($inSection) {
                $sectionFound = $true
            }

            $out.Add($line)
            continue
        }

        if ($inSection -and $trim -match $keyPattern) {
            $out.Add("$Key=$Value")
            $keyWritten = $true
            continue
        }

        $out.Add($line)
    }

    if ($inSection -and -not $keyWritten) {
        $out.Add("$Key=$Value")
        $keyWritten = $true
    }

    if (-not $sectionFound) {
        if ($out.Count -gt 0 -and -not [string]::IsNullOrWhiteSpace($out[$out.Count - 1])) {
            $out.Add("")
        }

        $out.Add("[$Section]")
        $out.Add("$Key=$Value")
    }

    $content = ($out -join [Environment]::NewLine) + [Environment]::NewLine
    Set-Content -Path $Path -Value $content -Encoding UTF8
}

function Configure-GlobalWslConfig {
    $path = Join-Path $env:USERPROFILE ".wslconfig"

    if (Test-Path $path) {
        $backup = "$path.tsw-backup-$(Get-Date -Format 'yyyyMMddHHmmss')"
        Copy-Item -Path $path -Destination $backup -Force
        Write-Ok "Backed up existing .wslconfig to $backup"
    }

    Set-IniValue -Path $path -Section "wsl2" -Key "nestedVirtualization" -Value "true"
    Set-IniValue -Path $path -Section "wsl2" -Key "localhostForwarding" -Value "true"
    Set-IniValue -Path $path -Section "wsl2" -Key "dnsTunneling" -Value "true"
    Set-IniValue -Path $path -Section "wsl2" -Key "autoProxy" -Value "true"

    Write-Ok "Updated $path with WSL2 baseline settings for Tiny Swarm World."
    $Script:ChangedWslConfiguration = $true
}

function Test-ProviderInsideWsl {
    param(
        [string]$Distro,
        [string]$SelectedProvider
    )

    if ($SelectedProvider -eq "none") {
        Write-Warn "No LXD/Incus provider was selected. Skipping provider validation."
        return
    }

    if ($SelectedProvider -eq "lxd") {
        $scriptText = @'
echo "Checking LXD/lxc availability..."
command -v lxc || true
command -v lxd || true
snap list lxd 2>/dev/null || true
systemctl is-active snap.lxd.daemon 2>/dev/null || true
systemctl is-active lxd 2>/dev/null || true
'@

        $result = Invoke-WslBash -Distro $Distro -ScriptText $scriptText -IgnoreExitCode

        if ($result.Output -notmatch "lxc") {
            Write-Warn "LXD/lxc was not detected inside the distro."
            Write-Host "Suggested WSL commands after systemd is active:" -ForegroundColor DarkGray
            Write-Host "  sudo snap install lxd" -ForegroundColor DarkGray
            Write-Host "  sudo lxd init" -ForegroundColor DarkGray
        }

        return
    }

    if ($SelectedProvider -eq "incus") {
        $scriptText = @'
echo "Checking Incus availability..."
command -v incus || true
systemctl is-active incus 2>/dev/null || true
'@

        $result = Invoke-WslBash -Distro $Distro -ScriptText $scriptText -IgnoreExitCode

        if ($result.Output -notmatch "incus") {
            Write-Warn "Incus was not detected inside the distro."
        }
    }
}

function Collect-WslEvidence {
    param([string]$Distro)

    $scriptText = @'
echo "kernel:"
cat /proc/sys/kernel/osrelease || true

echo "version:"
cat /proc/version || true

echo "WSL_INTEROP=$WSL_INTEROP"
echo "WSL_DISTRO_NAME=$WSL_DISTRO_NAME"

echo "default route:"
ip route show default || true

echo "resolv.conf:"
cat /etc/resolv.conf || true

echo "systemd:"
if [ -d /run/systemd/system ]; then
  systemctl is-system-running || true
else
  echo "systemd-runtime-not-detected"
fi

echo "dns:"
getent hosts archive.ubuntu.com || true
'@

    Invoke-WslBash -Distro $Distro -ScriptText $scriptText -IgnoreExitCode | Out-Null
}

function Write-Summary {
    param([string]$SelectedDistro)

    Write-Section "Summary"

    if ($Script:HadErrors) {
        Write-Fail "Preparation finished with errors."
    } elseif ($Script:HadWarnings) {
        Write-Warn "Preparation finished with warnings. Review the output before continuing."
    } else {
        Write-Ok "Preparation finished without detected errors."
    }

    Write-Host ""
    Write-Host "Selected distro: $SelectedDistro"
    Write-Host "Provider target: $Provider"
    Write-Host "CheckOnly: $CheckOnly"
    Write-Host "Changed WSL configuration: $Script:ChangedWslConfiguration"

    if ($Script:ChangedWslConfiguration -and $ShutdownAfterChange -and -not $CheckOnly) {
        Write-Host ""
        Write-Warn "WSL configuration was changed. The script can run 'wsl --shutdown' so changes take effect."
    } elseif ($Script:ChangedWslConfiguration -and -not $CheckOnly) {
        Write-Host ""
        Write-Warn "WSL configuration was changed. Run 'wsl --shutdown' manually before continuing."
    }

    Write-Host ""
    Write-Host "Next recommended checks after WSL restart:" -ForegroundColor Cyan
    Write-Host "  wsl -d $SelectedDistro -- systemctl is-system-running"
    Write-Host "  wsl -d $SelectedDistro -- bash -lc 'cat /proc/sys/kernel/osrelease; echo `$WSL_INTEROP; echo `$WSL_DISTRO_NAME'"

    if ($Provider -eq "lxd") {
        Write-Host "  wsl -d $SelectedDistro -- bash -lc 'command -v lxc && lxc version'"
    }

    if ($Provider -eq "incus") {
        Write-Host "  wsl -d $SelectedDistro -- bash -lc 'command -v incus && incus version'"
    }
}

try {
    New-Item -ItemType Directory -Path $EvidenceDirectory -Force | Out-Null
    $logFile = Join-Path $EvidenceDirectory ("prepare-wsl-lxc-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")

    try {
        Start-Transcript -Path $logFile -Force | Out-Null
    } catch {
        Write-Warn "Could not start PowerShell transcript: $($_.Exception.Message)"
    }

    Write-Section "Tiny Swarm World WSL/LXC prerequisite preparation"
    Write-Host "Evidence log: $logFile"
    Write-Host "Mode: $(if ($CheckOnly) { 'CHECK ONLY' } else { 'APPLY' })"

    Write-Section "Check WSL availability"
    Invoke-External -FilePath "wsl.exe" -Arguments @("--status") -IgnoreExitCode | Out-Null
    Invoke-External -FilePath "wsl.exe" -Arguments @("--version") -IgnoreExitCode | Out-Null

    if (-not $SkipWslUpdate) {
        if ($CheckOnly) {
            Write-Warn "CheckOnly is set. Skipping 'wsl --update'."
        } else {
            Write-Section "Update WSL"
            $update = Invoke-External -FilePath "wsl.exe" -Arguments @("--update") -IgnoreExitCode

            if ($update.ExitCode -ne 0) {
                Write-Warn "'wsl --update' failed. Continue only if WSL is already current enough for systemd support."
            }
        }
    }

    Write-Section "Select WSL distribution"
    $distros = @(Get-WslDistributions)
    $distros | Format-Table -AutoSize | Out-String | Write-Host

    $selected = Select-WslDistribution -Distributions $distros -RequestedName $DistroName
    $selectedName = $selected.Name

    Write-Ok "Selected WSL distro: $selectedName"

    Write-Section "Ensure WSL2"
    if ($selected.Version -eq 2) {
        Write-Ok "Distro '$selectedName' already runs as WSL2."
    } else {
        Write-Warn "Distro '$selectedName' currently runs as WSL$($selected.Version). Tiny Swarm World LXC path requires WSL2."

        if (-not $ConvertToWsl2) {
            throw "ConvertToWsl2 is disabled. Cannot continue with WSL$($selected.Version)."
        }

        if ($CheckOnly) {
            Write-Warn "CheckOnly is set. Would run: wsl --set-version '$selectedName' 2"
        } else {
            $confirmed = Confirm-Action -Prompt "Convert '$selectedName' to WSL2 now? Backup important data first." -DefaultNo

            if (-not $confirmed) {
                throw "User declined WSL2 conversion."
            }

            Invoke-External -FilePath "wsl.exe" -Arguments @("--set-version", $selectedName, "2") | Out-Null
            $Script:ChangedWslConfiguration = $true
            Write-Ok "WSL2 conversion command completed for '$selectedName'."
        }
    }

    if (-not $CheckOnly) {
        Invoke-External -FilePath "wsl.exe" -Arguments @("--set-default-version", "2") -IgnoreExitCode | Out-Null
    }

    if ($ConfigureWslConfig) {
        Write-Section "Configure global .wslconfig"

        if ($CheckOnly) {
            Write-Warn "CheckOnly is set. Would update %UserProfile%\.wslconfig."
        } else {
            Configure-GlobalWslConfig
        }
    } else {
        Write-Warn "Global .wslconfig was not modified. Use -ConfigureWslConfig to set nestedVirtualization, localhostForwarding, dnsTunneling and autoProxy."
    }

    if ($EnableSystemd) {
        Write-Section "Enable systemd in selected WSL distro"

        if ($CheckOnly) {
            Write-Warn "CheckOnly is set. Would ensure /etc/wsl.conf contains [boot] systemd=true."
        } else {
            Set-WslConfSystemd -Distro $selectedName
            $Script:ChangedWslConfiguration = $true
        }
    } else {
        Write-Warn "EnableSystemd is false. LXD/Incus daemon operation may not work."
    }

    Write-Section "Current systemd state"
    Test-WslSystemd -Distro $selectedName
    Write-Warn "If systemd was just enabled, this check may still show inactive until 'wsl --shutdown' has been executed."

    Write-Section "WSL host evidence"
    Collect-WslEvidence -Distro $selectedName

    Write-Section "Provider validation"
    Test-ProviderInsideWsl -Distro $selectedName -SelectedProvider $Provider

    Write-Summary -SelectedDistro $selectedName

    if ($Script:ChangedWslConfiguration -and $ShutdownAfterChange -and -not $CheckOnly) {
        $confirmedShutdown = Confirm-Action -Prompt "Run 'wsl --shutdown' now? This terminates all running WSL distributions." -DefaultNo

        if ($confirmedShutdown) {
            Invoke-External -FilePath "wsl.exe" -Arguments @("--shutdown") | Out-Null
            Write-Ok "WSL was shut down. Start the distro again and rerun this script with -CheckOnly to verify."
        } else {
            Write-Warn "WSL shutdown skipped. Run 'wsl --shutdown' manually before continuing."
        }
    }

    if ($Script:HadErrors) {
        exit 1
    }

    exit 0
}
catch {
    Write-Fail $_.Exception.Message
    Write-Host ""
    Write-Host "Rerun with -CheckOnly for diagnostics or with -Force to skip interactive confirmations where appropriate." -ForegroundColor Yellow
    exit 1
}
finally {
    try {
        Stop-Transcript | Out-Null
    } catch {
        # Transcript may not have been started.
    }
}
