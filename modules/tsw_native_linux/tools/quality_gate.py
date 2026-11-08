"""Compatibility entry point for the physical tsw_core module."""
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from modules.tsw_core.tools.linux.quality_gate import (
        COMMANDS as COMMANDS,
        LINT_IMPORTS as LINT_IMPORTS,
        PACKAGE_ROOT as PACKAGE_ROOT,
        PYTHON as PYTHON,
        Path as Path,
        QUALITY_GATE_ORDER as QUALITY_GATE_ORDER,
        REPOSITORY_ROOT as REPOSITORY_ROOT,
        SOURCE_ROOT as SOURCE_ROOT,
        SOURCE_TARGETS as SOURCE_TARGETS,
        TEST_ROOT as TEST_ROOT,
        _command_for_name as _command_for_name,
        _lint_imports_command as _lint_imports_command,
        _local_lint_imports_path as _local_lint_imports_path,
        _prepend_environment_path as _prepend_environment_path,
        _python_environment as _python_environment,
        _run_named_command as _run_named_command,
        argparse as argparse,
        main as main,
        os as os,
        shutil as shutil,
        subprocess as subprocess,
        sys as sys,
    )
from pathlib import Path
_impl = Path(__file__).resolve().parents[3] / 'modules/tsw_core/tools/linux/quality_gate.py'
__file__ = str(_impl)
exec(compile(_impl.read_bytes(), str(_impl), "exec"), globals(), globals())
