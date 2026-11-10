"""Compatibility entry point for the physical tsw_core module."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.tsw_core.tools.linux.qualification.owned_case_disposal import (
        Any as Any,
        DisposalIntent as DisposalIntent,
        DisposalPort as DisposalPort,
        INSTALLATION as INSTALLATION,
        IncusDisposalPort as IncusDisposalPort,
        NAMES as NAMES,
        OPERATION as OPERATION,
        OwnedNode as OwnedNode,
        Protocol as Protocol,
        SuiteDisposalPort as SuiteDisposalPort,
        UUID as UUID,
        dataclass as dataclass,
        default_manager_consumers as default_manager_consumers,
        dispose as dispose,
        importlib as importlib,
        native as native,
        own_reference as own_reference,
        profile_identity as profile_identity,
        query_uri as query_uri,
        quote as quote,
        re as re,
        read_creation as read_creation,
        specification as specification,
        time as time,
        validate_case_graph as validate_case_graph,
    )

from pathlib import Path
_impl = Path(__file__).resolve().parents[4] / 'modules/tsw_core/tools/linux/qualification/owned_case_disposal.py'
__file__ = str(_impl)
exec(compile(_impl.read_bytes(), str(_impl), "exec"), globals(), globals())
