# Bounded child process boundary for Windows registry/volume/ACL/file operations.
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot 'Preparation.psm1') -Force -DisableNameChecking
$module=Get-Module Preparation
try {
    $request=[Console]::In.ReadToEnd() | ConvertFrom-Json
    if($request.mode -eq 'inventory'){$result=& $module {param($o,$f) Get-PreparationResourceInventoryCore $o $f} $request.options $request.facts}
    elseif($request.mode -eq 'apply'){$result=& $module {param($r) Set-PreparationResourceConfigCore $r.path $r.approved $r.allocation $r.store $r.timeout} $request}
    else{throw 'invalid_mode'}
    $result | ConvertTo-Json -Depth 30 -Compress
    exit 0
} catch {
    @{confirmed=$false;uncertain=$true;exit_code=1;cause='resource_host_failed'} | ConvertTo-Json -Compress
    exit 1
}
