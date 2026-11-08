# Compatibility entry point for the physical Windows/WSL module.
& (Join-Path $PSScriptRoot '../../../modules/tsw_windows_wsl/tools/windows/qualification/windows_firewall_snapshot.ps1') @args
