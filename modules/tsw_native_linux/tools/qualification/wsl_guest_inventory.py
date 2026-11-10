"""Compatibility entry point for the physical tsw_core module."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.tsw_core.tools.linux.qualification.wsl_guest_inventory import (
        Any as Any,
        COLLECTOR_SHA as COLLECTOR_SHA,
        DETAIL_KINDS as DETAIL_KINDS,
        DetailObserver as DetailObserver,
        PROVENANCE_SHA as PROVENANCE_SHA,
        Path as Path,
        argparse as argparse,
        assert_restart_safe as assert_restart_safe,
        assert_source as assert_source,
        capture as capture,
        digest as digest,
        hashlib as hashlib,
        importlib as importlib,
        json as json,
        main as main,
        native as native,
        os as os,
        project as project,
        re as re,
        stat as stat,
        sys as sys,
    )

from pathlib import Path
_impl = Path(__file__).resolve().parents[4] / 'modules/tsw_core/tools/linux/qualification/wsl_guest_inventory.py'
__file__ = str(_impl)
exec(compile(_impl.read_bytes(), str(_impl), "exec"), globals(), globals())
