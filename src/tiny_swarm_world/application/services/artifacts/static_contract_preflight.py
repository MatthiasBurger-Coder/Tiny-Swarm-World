from __future__ import annotations

from tiny_swarm_world.application.ports.file_management.port_local_file_storage import (
    PortLocalFileStorage,
)
from tiny_swarm_world.application.ports.preflight import (
    PortArtifactContractInventory,
)
from tiny_swarm_world.domain.artifacts import ArtifactContractIssue
from tiny_swarm_world.domain.preflight import (
    PreflightCategory,
    PreflightCheck,
    PreflightResult,
    PreflightSeverity,
    PreflightStatus,
)


class StaticArtifactContractPreflight:
    """Validate selected image contracts without any external side effect."""

    def __init__(
        self,
        compose_repository: PortArtifactContractInventory,
        storage: PortLocalFileStorage,
    ) -> None:
        self.compose_repository = compose_repository
        self.storage = storage

    def run(self) -> PreflightResult:
        inventory = self.compose_repository.get_image_inventory()
        issues = list(inventory.validate())
        for requirement in inventory.requirements:
            if requirement.source != "build":
                continue
            if requirement.build_context is None:
                issues.append(
                    ArtifactContractIssue(
                        code="build_context_missing",
                        target_id=(
                            f"profile:{inventory.profile}:service:{requirement.service_name}"
                        ),
                        message="A build image does not declare a logical build context.",
                        remediation="Declare an approved repository-local build context.",
                    )
                )
                continue
            try:
                context_path = self.compose_repository.get_build_context_path(
                    requirement.build_context
                )
            except ValueError:
                issues.append(
                    ArtifactContractIssue(
                        code="build_context_unapproved",
                        target_id=f"artifacts:{requirement.build_context}-image",
                        message="The build context is not approved by the Compose repository.",
                        remediation="Use one of the repository-local build contexts.",
                    )
                )
                continue
            if not self.storage.directory_exists(context_path):
                issues.append(
                    ArtifactContractIssue(
                        code="build_context_missing",
                        target_id=f"artifacts:{requirement.build_context}-image",
                        message="The repository-local build context directory is missing.",
                        remediation="Restore the build context before artifact mutation.",
                    )
                )

        evidence = {
            "profile": inventory.profile,
            "contract_count": str(len(inventory.contracts)),
            "required_image_count": str(len(inventory.requirements)),
            "issue_count": str(len(issues)),
            "issue_codes": ",".join(issue.code for issue in issues) or "none",
            "evidence_scope": "static",
        }
        check = PreflightCheck(
            check_id="ARTIFACT-CONTRACTS",
            category=PreflightCategory.CONFIGURATION,
            status=PreflightStatus.PASSED if not issues else PreflightStatus.FAILED,
            severity=PreflightSeverity.MANDATORY,
            message=(
                "Static artifact contract preflight passed."
                if not issues
                else "Static artifact contract preflight failed."
            ),
            remediation=(
                "No remediation required."
                if not issues
                else "; ".join(dict.fromkeys(issue.remediation for issue in issues))
            ),
            evidence=evidence,
        )
        return PreflightResult((check,))
