"""Explicit admission of an application phase with no selected stack work."""


def has_apply_contract(steps, foundation_checks, *, application_phase: bool) -> bool:
    """Keep generic empty/bootstrap calls blocked unless foundation checks exist."""
    return bool(steps) or (application_phase and bool(foundation_checks))
