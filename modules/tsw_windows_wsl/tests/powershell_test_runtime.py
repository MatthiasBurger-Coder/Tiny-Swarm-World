"""Start isolated PowerShell test processes across the WSL interop boundary."""
from __future__ import annotations

import base64
from collections.abc import Mapping


def powershell_command(executable: str, command: str) -> list[str]:
    # WSL interop can inherit a PowerShell 7 parent's Windows module path.
    # Windows PowerShell 5.1 must resolve its own built-in modules first.
    bootstrap = "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue'; "
    if executable.lower().endswith(".exe"):
        bootstrap += "$env:PSModulePath = (Join-Path $PSHOME 'Modules') + [IO.Path]::PathSeparator + $env:PSModulePath; "
    bootstrap += "[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false); "
    encoded = base64.b64encode((bootstrap + command).encode("utf-16-le")).decode("ascii")
    return [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded]


def powershell_script_command(executable: str, path: str, arguments: Mapping[str, str]) -> list[str]:
    def literal(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    command = "& " + literal(path)
    for name, value in arguments.items():
        if not name.replace("_", "").isalnum():
            raise ValueError("Invalid PowerShell test parameter name")
        command += " -" + name + " " + literal(value)
    return powershell_command(executable, command)
