"""Compatibility entry point for the physical tsw_windows_wsl module."""
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from modules.tsw_windows_wsl.tools.windows.build_windows_preparation_manifest import (
        ASSETS as ASSETS,
        MAX_TREE_OBJECTS as MAX_TREE_OBJECTS,
        Path as Path,
        argparse as argparse,
        base64 as base64,
        build as build,
        git as git,
        json as json,
        main as main,
        subprocess as subprocess,
    )
from pathlib import Path
_impl = Path(__file__).resolve().parents[2] / 'modules/tsw_windows_wsl/tools/windows/build_windows_preparation_manifest.py'
__file__ = str(_impl)
exec(compile(_impl.read_bytes(), str(_impl), "exec"), globals(), globals())
