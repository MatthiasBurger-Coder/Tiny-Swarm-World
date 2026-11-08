# Compatibility entry point for the physical Windows/WSL module.
& (Join-Path $PSScriptRoot '../../../modules/tsw_windows_wsl/tools/windows/qualification/wsl_acceptance_guest_switch.ps1') @args
