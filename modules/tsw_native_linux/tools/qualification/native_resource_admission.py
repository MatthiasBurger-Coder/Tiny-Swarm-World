"""Compatibility entry point for the physical tsw_core module."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.tsw_core.tools.linux.qualification.native_resource_admission import (
        Any as Any,
        CONFIG as CONFIG,
        GIB as GIB,
        NativePreparationInspector as NativePreparationInspector,
        Path as Path,
        ROOT as ROOT,
        SELECTION as SELECTION,
        argparse as argparse,
        asdict as asdict,
        capture as capture,
        datetime as datetime,
        hashlib as hashlib,
        importlib as importlib,
        json as json,
        main as main,
        os as os,
        platform as platform,
        qualification_failures as qualification_failures,
        read_config as read_config,
        selection as selection,
        stat as stat,
        sys as sys,
        timezone as timezone,
    )

from pathlib import Path
_impl = Path(__file__).resolve().parents[4] / 'modules/tsw_core/tools/linux/qualification/native_resource_admission.py'
__file__ = str(_impl)
exec(compile(_impl.read_bytes(), str(_impl), "exec"), globals(), globals())
