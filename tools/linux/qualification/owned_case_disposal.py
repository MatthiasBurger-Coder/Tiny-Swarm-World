"""Compatibility entry point for the physical tsw_core module."""
from pathlib import Path
_impl = Path(__file__).resolve().parents[3] / 'modules/tsw_core/tools/linux/qualification/owned_case_disposal.py'
__file__ = str(_impl)
exec(compile(_impl.read_bytes(), str(_impl), "exec"), globals(), globals())
