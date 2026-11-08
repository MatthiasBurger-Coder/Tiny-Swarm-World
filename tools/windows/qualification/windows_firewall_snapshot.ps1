# Compatibility entry point for the physical Windows/WSL module.
$tswImplementationPath=Join-Path $PSScriptRoot '../../../modules/tsw_windows_wsl/tools/windows/qualification/windows_firewall_snapshot.ps1'
if($MyInvocation.InvocationName -eq '.') { . $tswImplementationPath @args } else { & $tswImplementationPath @args }
