"""Compatibility entry point for the physical tsw_windows_wsl module."""
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from modules.tsw_windows_wsl.tools.windows.build_wsl_resource_projection import (
        HostEnvironmentKind as HostEnvironmentKind,
        OUTPUT as OUTPUT,
        Path as Path,
        SOURCES as SOURCES,
        YAML as YAML,
        _amount as _amount,
        argparse as argparse,
        build as build,
        default_resource_profiles as default_resource_profiles,
        hashlib as hashlib,
        host_environment as host_environment,
        json as json,
        main as main,
        re as re,
        resource_module as resource_module,
    )
from pathlib import Path
_impl = Path(__file__).resolve().parents[2] / 'modules/tsw_windows_wsl/tools/windows/build_wsl_resource_projection.py'
__file__ = str(_impl)
exec(compile(_impl.read_bytes(), str(_impl), "exec"), globals(), globals())
