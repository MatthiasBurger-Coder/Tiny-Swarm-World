"""Compatibility entry point for the physical tsw_core module."""
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from modules.tsw_core.tools.linux.security_gate import (
        DEFAULT_SBOM as DEFAULT_SBOM,
        PYTHON as PYTHON,
        Path as Path,
        REPOSITORY_ROOT as REPOSITORY_ROOT,
        RUNTIME_LOCK as RUNTIME_LOCK,
        _container_config_command as _container_config_command,
        _dependency_audit_command as _dependency_audit_command,
        _require_ignored_local_output as _require_ignored_local_output,
        _run as _run,
        _sbom_command as _sbom_command,
        argparse as argparse,
        main as main,
        shutil as shutil,
        subprocess as subprocess,
        sys as sys,
    )
from pathlib import Path
_impl = Path(__file__).resolve().parents[2] / 'modules/tsw_core/tools/linux/security_gate.py'
__file__ = str(_impl)
exec(compile(_impl.read_bytes(), str(_impl), "exec"), globals(), globals())
