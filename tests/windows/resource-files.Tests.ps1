param([Parameter(Mandatory=$true)][string]$RepositoryRoot)
$ErrorActionPreference='Stop'
Import-Module (Join-Path $RepositoryRoot 'tools/windows/preparation/Preparation.psm1') -Force -DisableNameChecking
$m=Get-Module Preparation
if([Environment]::OSVersion.Platform -ne 'Win32NT'){throw 'Windows disposable ACL fixture required'}
$count=0
function Assert($v,$n){if(!$v){throw "FAIL: $n"};$script:count++}
$directory=Join-Path ([Environment]::GetFolderPath('UserProfile')) ('tsw-resource-tests-'+[guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($directory)
try {
    $path=Join-Path $directory '.wslconfig'
    $store=Join-Path $directory 'evidence';[void][IO.Directory]::CreateDirectory($store)
    $allocation=@{memory_gib=21;processors=8;swap_gib=6}
    [IO.File]::WriteAllText($path,"# retain`r`n[wsl2]`r`nmemory=8GB`r`nnetworkingMode=mirrored`r`n",(New-Object Text.UTF8Encoding($true)))
    & $m {param($p) Set-PreparationPrivateAcl $p} $path
    $approved=& $m {param($p) Get-PreparationConfigSnapshot $p} $path
    $original=[IO.File]::ReadAllBytes($path)
    $effect=& $m {param($p,$a,$allocation,$s) Set-PreparationResourceConfigCore $p $a $allocation $s 15} $path $approved $allocation $store
    Assert ($effect.confirmed -and !$effect.uncertain) ('atomic concrete merge: '+$effect.cause)
    Assert ([IO.File]::ReadAllText($path).Contains('networkingMode=mirrored')) 'unrelated setting preserved'
    Assert ([Convert]::ToBase64String([IO.File]::ReadAllBytes($effect.observations.backup_path)) -ceq [Convert]::ToBase64String($original)) 'protected original backup'
    Assert ([Convert]::ToBase64String([IO.File]::ReadAllBytes($effect.observations.displaced_backup)) -ceq [Convert]::ToBase64String($original)) 'atomic displaced bytes preserved'
    & $m {param($p) Assert-PreparationResourcePath $p} $effect.observations.backup_path
    $before=[IO.File]::ReadAllText($path)
    $stale=& $m {param($p,$a,$allocation,$s) Set-PreparationResourceConfigCore $p $a $allocation $s 15} $path $approved $allocation $store
    Assert (!$stale.confirmed -and !$stale.uncertain -and $stale.cause -eq 'global_config_drift') 'stale approval blocks writes'
    Assert ([IO.File]::ReadAllText($path) -ceq $before) 'drift preserves file'
    $approved=& $m {param($p) Get-PreparationConfigSnapshot $p} $path
    $lock=Join-Path $directory '.tsw-wslconfig.lock';[IO.File]::WriteAllText($lock,'foreign lock')
    $locked=& $m {param($p,$a,$allocation,$s) Set-PreparationResourceConfigCore $p $a $allocation $s 15} $path $approved $allocation $store
    Assert (!$locked.confirmed -and [IO.File]::ReadAllText($lock) -eq 'foreign lock') 'existing lock never overwritten'
    Remove-Item -LiteralPath $lock
    Remove-Item -LiteralPath $path
    $absent=& $m {param($p) Get-PreparationConfigSnapshot $p} $path
    $created=& $m {param($p,$a,$allocation,$s) Set-PreparationResourceConfigCore $p $a $allocation $s 15} $path $absent $allocation $store
    Assert ($created.confirmed -and [IO.File]::ReadAllText($path).Contains('memory=21GB')) 'absent configuration safely created'
    Assert (!(Test-Path -LiteralPath $lock)) 'owned lock cleaned'
    $approved=& $m {param($p) Get-PreparationConfigSnapshot $p} $path
    $bounded=& $m {param($p,$a,$allocation,$s,$root) Set-PreparationResourceConfig $p $a $allocation $s 15 @{RepositoryRoot=$root}} $path $approved $allocation $store $RepositoryRoot
    Assert ($bounded.confirmed -and !$bounded.uncertain) 'bounded child performs and verifies disposable resource action'
    # Real bounded helper timeout, never an actual host target.
    $fixtureRoot=Join-Path $directory 'bounded-helper'
    $helperDirectory=Join-Path $fixtureRoot 'tools/windows/preparation';[void][IO.Directory]::CreateDirectory($helperDirectory)
    [IO.File]::WriteAllText((Join-Path $helperDirectory 'ResourceHost.ps1'),"$([char]36)request=[Console]::In.ReadToEnd();Start-Sleep -Seconds 10")
    $approved=& $m {param($p) Get-PreparationConfigSnapshot $p} $path
    $before=[IO.File]::ReadAllBytes($path)
    $timeout=& $m {param($p,$a,$allocation,$s,$root) Set-PreparationResourceConfig $p $a $allocation $s 1 @{RepositoryRoot=$root}} $path $approved $allocation $store $fixtureRoot
    Assert ($timeout.exit_code -eq 124 -and $timeout.uncertain -and !$timeout.confirmed) 'real W05 helper timeout typed uncertain'
    Assert ([Convert]::ToBase64String([IO.File]::ReadAllBytes($path)) -ceq [Convert]::ToBase64String($before)) 'timed out helper never retried or altered fixture'
    [IO.File]::WriteAllText((Join-Path $helperDirectory 'ResourceHost.ps1'),"$([char]36)r=[Console]::In.ReadToEnd()|ConvertFrom-Json;[IO.File]::WriteAllText($([char]36)r.path,'changed fixture');Start-Sleep -Seconds 10")
    $changedTimeout=& $m {param($p,$a,$allocation,$s,$root) Set-PreparationResourceConfig $p $a $allocation $s 2 @{RepositoryRoot=$root}} $path $approved $allocation $store $fixtureRoot
    Assert ($changedTimeout.exit_code -eq 124 -and $changedTimeout.uncertain -and [IO.File]::ReadAllText($path) -eq 'changed fixture') 'real timed out effect remains visible and uncertain'
    [IO.File]::WriteAllBytes($path,$before)
    # Byte equality never excuses metadata drift.
    $approved=& $m {param($p) Get-PreparationConfigSnapshot $p} $path
    [IO.File]::SetLastWriteTimeUtc($path,[DateTime]::UtcNow.AddSeconds(2))
    $metadata=& $m {param($p,$a,$allocation,$s) Set-PreparationResourceConfigCore $p $a $allocation $s 15} $path $approved $allocation $store
    Assert (!$metadata.confirmed -and $metadata.cause -eq 'global_config_drift') 'metadata drift blocks'
    # Actual foreign edit between final snapshot and atomic Replace stays recoverable.
    $approved=& $m {param($p) Get-PreparationConfigSnapshot $p} $path
    $replacement=& $m {${function:Invoke-PreparationConfigReplacement}}
    & $m {function script:Invoke-PreparationConfigReplacement($t,$p,$d){[IO.File]::WriteAllText($p,"[wsl2]`nmemory=23GB`n# concurrent editor");[IO.File]::Replace($t,$p,$d)}}
    $race=& $m {param($p,$a,$allocation,$s) Set-PreparationResourceConfigCore $p $a $allocation $s 15} $path $approved $allocation $store
    Assert (!$race.confirmed -and $race.uncertain -and $race.cause -eq 'global_config_displaced_drift') 'concurrent edit detected as uncertain'
    Assert ([IO.File]::ReadAllText($race.observations.displaced_backup).Contains('# concurrent editor')) 'actual foreign bytes retained'
    & $m {param($body) Set-Item function:script:Invoke-PreparationConfigReplacement $body} $replacement
    $approved=& $m {param($p) Get-PreparationConfigSnapshot $p} $path
    & $m {function script:Invoke-PreparationConfigReplacement($t,$p,$d){throw 'disposable replacement failure'}}
    $before=[IO.File]::ReadAllBytes($path)
    $failure=& $m {param($p,$a,$allocation,$s) Set-PreparationResourceConfigCore $p $a $allocation $s 15} $path $approved $allocation $store
    Assert (!$failure.confirmed -and !$failure.uncertain -and [Convert]::ToBase64String([IO.File]::ReadAllBytes($path)) -ceq [Convert]::ToBase64String($before)) 'failed replacement preserves original'
    & $m {param($body) Set-Item function:script:Invoke-PreparationConfigReplacement $body} $replacement
    $approved=& $m {param($p) Get-PreparationConfigSnapshot $p} $path
    & $m {function script:Invoke-PreparationConfigReplacement($t,$p,$d){[IO.File]::SetLastWriteTimeUtc($p,[DateTime]::UtcNow.AddSeconds(5));[IO.File]::Replace($t,$p,$d)}}
    $metadataRace=& $m {param($p,$a,$allocation,$s) Set-PreparationResourceConfigCore $p $a $allocation $s 15} $path $approved $allocation $store
    Assert (!$metadataRace.confirmed -and $metadataRace.uncertain -and $metadataRace.cause -eq 'global_config_displaced_drift') 'late metadata race detected from actual displaced snapshot'
    & $m {param($body) Set-Item function:script:Invoke-PreparationConfigReplacement $body} $replacement
    $approved=& $m {param($p) Get-PreparationConfigSnapshot $p} $path
    & $m {function script:Invoke-PreparationConfigReplacement($t,$p,$d){[IO.File]::Replace($t,$p,$d);throw 'after replacement failed'}}
    $lateFailure=& $m {param($p,$a,$allocation,$s) Set-PreparationResourceConfigCore $p $a $allocation $s 15} $path $approved $allocation $store
    Assert (!$lateFailure.confirmed -and $lateFailure.uncertain -and (Test-Path -LiteralPath $lateFailure.observations.displaced_backup)) 'changed target then thrown exception remains uncertain'
    & $m {param($body) Set-Item function:script:Invoke-PreparationConfigReplacement $body} $replacement
    # An absent leaf still validates all existing ancestor ACLs.
    $unsafe=Join-Path $directory 'unsafe';[void][IO.Directory]::CreateDirectory($unsafe)
    $acl=Get-Acl -LiteralPath $unsafe
    $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule((New-Object Security.Principal.SecurityIdentifier('S-1-1-0')),'Modify','Allow')))
    [IO.Directory]::SetAccessControl($unsafe,$acl)
    $blocked=$false;try{& $m {param($p) Get-PreparationConfigSnapshot $p} (Join-Path $unsafe '.wslconfig') | Out-Null}catch{$blocked=$true}
    Assert $blocked 'unsafe ancestor rejects absent leaf'
    Write-Output "PASS: $count disposable Windows resource file assertions"
}finally{Remove-Item -LiteralPath $directory -Recurse -Force}
