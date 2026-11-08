"""Compatibility entry point for the physical tsw_core module."""
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from modules.tsw_core.tools.linux.skill_audit import (
        Path as Path,
        REGISTRY as REGISTRY,
        ROOT as ROOT,
        SKILLS as SKILLS,
        _frontmatter as _frontmatter,
        audit as audit,
        audit_activation as audit_activation,
        classify_skill as classify_skill,
        json as json,
        re as re,
        sys as sys,
    )
from pathlib import Path
_impl = Path(__file__).resolve().parents[3] / 'modules/tsw_core/tools/linux/skill_audit.py'
__file__ = str(_impl)
exec(compile(_impl.read_bytes(), str(_impl), "exec"), globals(), globals())
