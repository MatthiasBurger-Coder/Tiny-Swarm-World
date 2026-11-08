"""Compatibility import for the core-owned secure runtime path adapter."""
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tiny_swarm_world.infrastructure.adapters.secure_runtime_paths import (
        Callable as Callable,
        NATIVE_LINUX as NATIVE_LINUX,
        Path as Path,
        RuntimePathAssessment as RuntimePathAssessment,
        UNKNOWN as UNKNOWN,
        WINDOWS_MOUNTED as WINDOWS_MOUNTED,
        WSL_NATIVE as WSL_NATIVE,
        _LINUX_FILESYSTEMS as _LINUX_FILESYSTEMS,
        _WINDOWS_9P_FILESYSTEMS as _WINDOWS_9P_FILESYSTEMS,
        _assess as _assess,
        _bool_text as _bool_text,
        _decode as _decode,
        _mount_kind as _mount_kind,
        _parse_mountinfo as _parse_mountinfo,
        _read_mountinfo as _read_mountinfo,
        _resolve as _resolve,
        _safe_stat as _safe_stat,
        _within as _within,
        assess_evidence_directory as assess_evidence_directory,
        assess_secret_file as assess_secret_file,
        classify_path as classify_path,
        dataclass as dataclass,
        ensure_secure_directory as ensure_secure_directory,
        field as field,
        host_classification as host_classification,
        os as os,
        platform as platform,
        stat as stat,
    )
import sys
from tiny_swarm_world.infrastructure.adapters import secure_runtime_paths as _implementation
sys.modules[__name__] = _implementation
