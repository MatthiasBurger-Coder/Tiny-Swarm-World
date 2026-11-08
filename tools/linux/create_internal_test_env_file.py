"""Compatibility entry point for the physical tsw_core module."""
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from modules.tsw_core.tools.linux.create_internal_test_env_file import (
        Path as Path,
        argparse as argparse,
        create_internal_test_env_file as create_internal_test_env_file,
        internal_test_catalog as internal_test_catalog,
        main as main,
        os as os,
        shlex as shlex,
        stat as stat,
        sys as sys,
        validate_internal_test_catalog as validate_internal_test_catalog,
    )
from pathlib import Path
_impl = Path(__file__).resolve().parents[2] / 'modules/tsw_core/tools/linux/create_internal_test_env_file.py'
__file__ = str(_impl)
exec(compile(_impl.read_bytes(), str(_impl), "exec"), globals(), globals())
