from __future__ import annotations

import re
from dataclasses import dataclass


IMAGE_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9/:._-]*[a-z0-9]$")
IMAGE_TAG_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
IMAGE_DIGEST_PATTERN = re.compile(r"^@sha256:[0-9a-f]{64}$")
BUILD_CONTEXT_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
IMAGE_SOURCE_PATTERN = re.compile(r"^(build|pull)$")


@dataclass(frozen=True)
class ContainerImageContract:
    image_name: str
    tag: str
    build_context: str
    source: str = "build"

    def __post_init__(self) -> None:
        if not IMAGE_NAME_PATTERN.fullmatch(self.image_name):
            raise ValueError("container image name contains invalid characters")
        if not (
            IMAGE_TAG_PATTERN.fullmatch(self.tag)
            or IMAGE_DIGEST_PATTERN.fullmatch(self.tag)
        ):
            raise ValueError("container image tag contains invalid characters")
        if not BUILD_CONTEXT_PATTERN.fullmatch(self.build_context):
            raise ValueError("container image build context contains invalid characters")
        if not IMAGE_SOURCE_PATTERN.fullmatch(self.source):
            raise ValueError("container image source must be build or pull")

    @property
    def image_ref(self) -> str:
        if self.tag.startswith("@"):
            return f"{self.image_name}{self.tag}"
        return f"{self.image_name}:{self.tag}"

    @property
    def artifact_target_id(self) -> str:
        return f"artifacts:{self.build_context}-image"

    @property
    def verification_target_id(self) -> str:
        return self.artifact_target_id

    def to_dict(self) -> dict[str, str]:
        return {
            "artifact_target_id": self.artifact_target_id,
            "build_context": self.build_context,
            "image_ref": self.image_ref,
            "source": self.source,
        }

    def validation_issues(self) -> tuple["ArtifactContractIssue", ...]:
        """Return safe preflight issues without performing external I/O."""

        if self.tag.lower() == "latest":
            return (
                ArtifactContractIssue(
                    code="implicit_latest_not_allowed",
                    target_id=self.artifact_target_id,
                    message="Container image references must use an immutable tag or digest.",
                    remediation="Set an approved version tag or sha256 digest.",
                ),
            )
        if self.tag.startswith("@") and not IMAGE_DIGEST_PATTERN.fullmatch(self.tag):
            return (
                ArtifactContractIssue(
                    code="invalid_image_digest",
                    target_id=self.artifact_target_id,
                    message="Container image digest must use a full sha256 digest.",
                    remediation="Use an approved version tag or a full sha256 digest.",
                ),
            )
        return ()


@dataclass(frozen=True)
class ArtifactContractIssue:
    """Safe, deterministic validation output for an artifact preflight."""

    code: str
    target_id: str
    message: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "remediation": self.remediation,
            "target_id": self.target_id,
        }


@dataclass(frozen=True)
class ArtifactImageRequirement:
    """One image required by a selected, already-resolved service profile."""

    service_name: str
    image_ref: str
    build_context: str | None = None
    source: str | None = None

    def __post_init__(self) -> None:
        if not self.service_name.strip():
            raise ValueError("artifact image requirement needs a service name")
        if not self.image_ref.strip():
            raise ValueError("artifact image requirement needs an image reference")
        if self.source is not None and self.source not in {"build", "pull"}:
            raise ValueError("artifact image requirement source must be build or pull")


@dataclass(frozen=True)
class ArtifactImageInventory:
    """Profile-scoped image requirements and their matching contracts."""

    profile: str
    requirements: tuple[ArtifactImageRequirement, ...]
    contracts: tuple[ContainerImageContract, ...]

    def __post_init__(self) -> None:
        if not self.profile.strip():
            raise ValueError("artifact image inventory needs a profile")
        object.__setattr__(self, "requirements", tuple(self.requirements))
        object.__setattr__(self, "contracts", tuple(self.contracts))

    def validate(self) -> tuple[ArtifactContractIssue, ...]:
        issues: list[ArtifactContractIssue] = []
        issues.extend(
            issue
            for contract in self.contracts
            for issue in contract.validation_issues()
        )

        contracts_by_context: dict[str, list[ContainerImageContract]] = {}
        contracts_by_ref: dict[str, list[ContainerImageContract]] = {}
        for contract in self.contracts:
            contracts_by_context.setdefault(contract.build_context, []).append(contract)
            contracts_by_ref.setdefault(contract.image_ref, []).append(contract)

        for context, contracts in sorted(contracts_by_context.items()):
            if len(contracts) > 1:
                issues.append(
                    ArtifactContractIssue(
                        code="duplicate_logical_build_context",
                        target_id=f"artifacts:{context}-image",
                        message="Multiple image contracts use the same logical build context.",
                        remediation="Keep exactly one contract for each logical build context.",
                    )
                )
        for image_ref, contracts in sorted(contracts_by_ref.items()):
            if len(contracts) > 1:
                issues.append(
                    ArtifactContractIssue(
                        code="conflicting_image_reference",
                        target_id=f"artifacts:image:{image_ref}",
                        message="Multiple image contracts resolve to the same image reference.",
                        remediation="Assign one unambiguous contract to each image reference.",
                    )
                )

        consumed_contexts: set[str] = set()
        for requirement in self.requirements:
            matching = contracts_by_ref.get(requirement.image_ref, [])
            if not matching:
                issues.append(
                    ArtifactContractIssue(
                        code="missing_image_contract",
                        target_id=f"profile:{self.profile}:service:{requirement.service_name}",
                        message="A deployed image has no matching image contract.",
                        remediation="Add or align the image contract before artifact mutation.",
                    )
                )
                continue
            contract = matching[0]
            consumed_contexts.add(contract.build_context)
            if (
                requirement.build_context is not None
                and requirement.build_context != contract.build_context
            ):
                issues.append(
                    ArtifactContractIssue(
                        code="image_contract_mismatch",
                        target_id=contract.artifact_target_id,
                        message="The deployed image and image contract use different build contexts.",
                        remediation="Align Compose metadata and the artifact contract.",
                    )
                )
            if requirement.source is not None and requirement.source != contract.source:
                issues.append(
                    ArtifactContractIssue(
                        code="image_source_mismatch",
                        target_id=contract.artifact_target_id,
                        message="The deployed image and image contract use different source semantics.",
                        remediation="Align build/pull source semantics before mutation.",
                    )
                )

        for contract in self.contracts:
            if contract.build_context not in consumed_contexts:
                issues.append(
                    ArtifactContractIssue(
                        code="unused_image_contract",
                        target_id=contract.artifact_target_id,
                        message="An image contract is not consumed by the selected profile.",
                        remediation="Remove it from the selected inventory or add its deployment target.",
                    )
                )
        return tuple(issues)

    @property
    def valid(self) -> bool:
        return not self.validate()

    def to_dict(self) -> dict[str, object]:
        return {
            "contracts": [contract.to_dict() for contract in self.contracts],
            "issues": [issue.to_dict() for issue in self.validate()],
            "profile": self.profile,
            "requirements": [
                {
                    "build_context": requirement.build_context,
                    "image_ref": requirement.image_ref,
                    "service_name": requirement.service_name,
                    "source": requirement.source,
                }
                for requirement in self.requirements
            ],
        }


DEFAULT_CONTAINER_IMAGE_CONTRACTS = (
    ContainerImageContract(
        image_name="127.0.0.1:13500/jenkins",
        tag="0.2.0",
        build_context="jenkins",
    ),
    ContainerImageContract(
        image_name="127.0.0.1:13500/service-access-dashboard",
        tag="0.2.0",
        build_context="service-access-dashboard",
    ),
    ContainerImageContract(
        image_name="127.0.0.1:13500/service-access-nginx",
        tag="0.2.0",
        build_context="service-access-nginx",
    ),
    ContainerImageContract(
        image_name="infisical/infisical",
        tag="v0.159.1",
        build_context="infisical",
        source="pull",
    ),
    ContainerImageContract(
        image_name="postgres",
        tag="14.23-alpine3.23",
        build_context="infisical-postgres",
        source="pull",
    ),
    ContainerImageContract(
        image_name="redis",
        tag="7.4.9-alpine3.21",
        build_context="infisical-redis",
        source="pull",
    ),
    ContainerImageContract(
        image_name="traefik",
        tag="v3.7.4",
        build_context="traefik",
        source="pull",
    ),
    ContainerImageContract(
        image_name="sonarqube",
        tag="26.6.0.123539-community",
        build_context="sonarqube",
        source="pull",
    ),
    ContainerImageContract(
        image_name="postgres",
        tag="13.23",
        build_context="sonarqube-postgres",
        source="pull",
    ),
    ContainerImageContract(
        image_name="swaggerapi/swagger-editor",
        tag="v5.6.2-unprivileged",
        build_context="swagger-editor",
        source="pull",
    ),
    ContainerImageContract(
        image_name="swaggerapi/swagger-ui",
        tag="v5.32.6",
        build_context="swagger-ui",
        source="pull",
    ),
    ContainerImageContract(
        image_name="apachepulsar/pulsar",
        tag="3.0.17",
        build_context="pulsar",
        source="pull",
    ),
    ContainerImageContract(
        image_name="apachepulsar/pulsar-manager",
        tag="v0.4.0",
        build_context="pulsar-manager",
        source="pull",
    ),
    ContainerImageContract(
        image_name="python",
        tag="3.12.13-alpine3.23",
        build_context="pulsar-manager-bootstrap",
        source="pull",
    ),
    ContainerImageContract(
        image_name="nginx",
        tag="1.29.8-alpine",
        build_context="swagger-nginx",
        source="pull",
    ),
    ContainerImageContract(
        image_name="portainer/portainer-ce",
        tag="2.45.0",
        build_context="portainer",
        source="pull",
    ),
    ContainerImageContract(
        image_name="portainer/agent",
        tag="2.45.0",
        build_context="portainer-agent",
        source="pull",
    ),
    ContainerImageContract(
        image_name="sonatype/nexus3",
        tag="3.75.1",
        build_context="nexus",
        source="pull",
    ),
    ContainerImageContract(
        image_name="danielgtaylor/apisprout",
        tag="@sha256:6c07143937e57095d8478efc8ab7eab52b44e67c7673285f8c0a2bf4a7b137ad",
        build_context="swagger-api",
        source="pull",
    ),
)
