"""Explicit preflight coverage and expected summary-persistence outcomes."""
from __future__ import annotations

from dataclasses import replace

from tiny_swarm_world.application.services.shared.operation_results import failure_from_exception, failures_to_evidence
from tiny_swarm_world.domain.preflight import (
    PreflightCategory, PreflightCheck, PreflightConfiguration, PreflightResult,
    PreflightSeverity, PreflightStatus,
)
from tiny_swarm_world.domain.preflight.completeness import (
    PreflightCompleteness, PreflightConstruction, SummaryPersistence,
)


def assess_completeness(
    checks: tuple[PreflightCheck, ...],
    construction: PreflightConstruction,
    resource_inspector: object | None,
    filesystem_evaluator: object | None,
    project_path: str | None,
    filesystem_authorizer: object | None,
    secret_storage_probe: object | None,
    secret_storage_path: str | None,
    artifact_source: object | None,
    evidence_writer: object | None,
) -> PreflightCompleteness:
    collaborators = {
        "resource_inspector": all(callable(getattr(resource_inspector, name, None))
                                  for name in ("inspect", "memory_pressure")),
        "project_filesystem": filesystem_evaluator is not None and project_path is not None,
        "filesystem_authorizer": filesystem_authorizer is not None,
        "secret_storage": secret_storage_probe is not None and secret_storage_path is not None,
        "artifact_source": artifact_source is not None,
        "evidence_writer": callable(getattr(evidence_writer, "write", None)),
    }
    live = any(check.check_id == "LIVE-CONSENT" and check.passed for check in checks)
    wsl = any(check.check_id == "HOST" and check.evidence.get("environment") == "wsl2"
              for check in checks)
    applicable = ["project_filesystem"]
    if wsl:
        applicable.append("resource_inspector")
    if live:
        applicable.extend(("filesystem_authorizer", "secret_storage", "artifact_source"))
    return PreflightCompleteness(
        construction=construction,
        collaborators=collaborators,
        applicable_collaborators=tuple(applicable),
        invalid_checks=tuple(check.check_id for check in checks
                             if check.evidence.get("classification") == "malformed_inspector_output"),
        scope="LIVE" if live else "STATIC",
    )


def persist_summary(
    checks: tuple[PreflightCheck, ...],
    configuration: PreflightConfiguration,
    completeness: PreflightCompleteness,
    evidence_writer: object | None,
    *,
    write_evidence: bool,
) -> PreflightResult:
    if (completeness.construction is PreflightConstruction.STANDARD_SETUP
            and not completeness.collaborators_complete):
        checks = (*checks, _failure(
            "PREFLIGHT-COLLABORATORS", PreflightCategory.CONFIGURATION,
            "Standard setup preflight wiring is incomplete.",
            "Restore the standard setup collaborators before live setup.",
            {"missing": ",".join(completeness.missing_collaborators)},
        ))
    result = PreflightResult(
        checks, setup_profile=configuration.setup_profile,
        manifest_summary=configuration.setup_manifest.summary(), completeness=completeness,
    )
    if not write_evidence:
        return result
    write = getattr(evidence_writer, "write", None)
    if not callable(write):
        return replace(result, completeness=replace(
            completeness, summary_persistence=SummaryPersistence.MISSING_WRITER,
        ))
    stored = replace(result, completeness=replace(
        completeness, summary_persistence=SummaryPersistence.STORED,
    ))
    try:
        write(stored.to_evidence(), f"{configuration.setup_manifest.evidence_root}/preflight.json")
    except (OSError, ValueError) as error:
        failure = failure_from_exception(error, "platform.preflight.evidence", "platform")
        return replace(result, checks=(*checks, _failure(
            "PREFLIGHT-EVIDENCE", PreflightCategory.FILESYSTEM,
            "Preflight evidence could not be stored.", failure.recommended_action,
            failures_to_evidence((failure,)),
        )), completeness=replace(completeness, summary_persistence=SummaryPersistence.FAILED))
    return stored


def missing_override_authorizer_check(
    live: bool, override: bool, authorizer: object | None,
) -> PreflightCheck | None:
    if not (live and override and authorizer is None):
        return None
    return _failure(
        "HOST-FILESYSTEM-AUTHORIZER", PreflightCategory.FILESYSTEM,
        "A live filesystem override requires protected authorization.",
        "Wire the filesystem authorizer before requesting a live override.",
        {"classification": "missing_authorizer"},
    )


def _failure(
    check_id: str, category: PreflightCategory, message: str,
    remediation: str, evidence: dict[str, str],
) -> PreflightCheck:
    return PreflightCheck(check_id, category, PreflightStatus.FAILED,
                          PreflightSeverity.MANDATORY, message, remediation, evidence)
