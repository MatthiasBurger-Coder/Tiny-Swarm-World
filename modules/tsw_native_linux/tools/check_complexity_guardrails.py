"""Compatibility entry point for the physical tsw_core module."""
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from modules.tsw_core.tools.linux.check_complexity_guardrails import (
        Any as Any,
        BASELINE as BASELINE,
        EXCEPTIONS as EXCEPTIONS,
        Path as Path,
        ROOT as ROOT,
        SOURCE as SOURCE,
        _complexity as _complexity,
        _fingerprint as _fingerprint,
        _functions as _functions,
        argparse as argparse,
        ast as ast,
        check as check,
        copy as copy,
        covered_paths as covered_paths,
        findings as findings,
        hashlib as hashlib,
        json as json,
        main as main,
        snapshot as snapshot,
    )
from pathlib import Path
_impl = Path(__file__).resolve().parents[3] / 'modules/tsw_core/tools/linux/check_complexity_guardrails.py'
__file__ = str(_impl)
exec(compile(_impl.read_bytes(), str(_impl), "exec"), globals(), globals())
