"""Compatibility entry point for the physical tsw_core module."""
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from modules.tsw_core.tools.linux.check_verification_policy_consistency import (
        ALLOWED_STATES as ALLOWED_STATES,
        APPLICABILITY_STATES as APPLICABILITY_STATES,
        DEFAULT_LOCAL_GATE as DEFAULT_LOCAL_GATE,
        EXTERNAL_GATE_STATES as EXTERNAL_GATE_STATES,
        Finding as Finding,
        LIVE_INSTALL_COMMAND as LIVE_INSTALL_COMMAND,
        LIVE_STATES as LIVE_STATES,
        POLICY_RELATIVE_PATH as POLICY_RELATIVE_PATH,
        Path as Path,
        _CONSENT_WORD as _CONSENT_WORD,
        _FORBIDDEN_PHRASES as _FORBIDDEN_PHRASES,
        _NEGATIVE_WORD as _NEGATIVE_WORD,
        _STATE_TOKEN as _STATE_TOKEN,
        _SUCCESS_WORD as _SUCCESS_WORD,
        _UNAVAILABLE_WORD as _UNAVAILABLE_WORD,
        _find_forbidden_wording as _find_forbidden_wording,
        _find_unknown_states as _find_unknown_states,
        _governance_documents as _governance_documents,
        _has_consent_context as _has_consent_context,
        _is_explicitly_negative as _is_explicitly_negative,
        _validate_canonical_policy as _validate_canonical_policy,
        check_repository as check_repository,
        dataclass as dataclass,
        main as main,
        re as re,
    )
from pathlib import Path
_impl = Path(__file__).resolve().parents[2] / 'modules/tsw_core/tools/linux/check_verification_policy_consistency.py'
__file__ = str(_impl)
exec(compile(_impl.read_bytes(), str(_impl), "exec"), globals(), globals())
