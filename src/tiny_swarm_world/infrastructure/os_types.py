
import os
import platform
from enum import Enum
from pathlib import Path


class OsTypes(str, Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    WSL_LINUX = "wsl_linux"

    @staticmethod
    def get_enum_from_value(value: str) -> "OsTypes":
        normalized_value = value.lower()
        if normalized_value in {"wsl", "wsl2", "wsl_linux"}:
            return OsTypes.WSL_LINUX
        for enum_member in OsTypes:
            if enum_member.value.lower() == normalized_value:
                return enum_member
        raise ValueError(f"Value '{value}' does not match any OsType.")

    @staticmethod
    def detect_current() -> "OsTypes":
        system = platform.system().lower()
        if system == "windows":
            return OsTypes.WINDOWS
        if system == "linux":
            if _has_wsl_signal():
                return OsTypes.WSL_LINUX
            return OsTypes.LINUX
        return OsTypes.get_enum_from_value(system)


def _has_wsl_signal() -> bool:
    if os.environ.get("WSL_INTEROP") or os.environ.get("WSL_DISTRO_NAME"):
        return True
    try:
        kernel_release = Path("/proc/sys/kernel/osrelease").read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except OSError:
        return False
    return "microsoft" in kernel_release.lower() or "wsl" in kernel_release.lower()
