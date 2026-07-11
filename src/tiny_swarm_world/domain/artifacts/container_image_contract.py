from __future__ import annotations

import re
from dataclasses import dataclass


IMAGE_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9/:._-]*[a-z0-9]$")
IMAGE_TAG_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
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
        if not IMAGE_TAG_PATTERN.fullmatch(self.tag):
            raise ValueError("container image tag contains invalid characters")
        if not BUILD_CONTEXT_PATTERN.fullmatch(self.build_context):
            raise ValueError("container image build context contains invalid characters")
        if not IMAGE_SOURCE_PATTERN.fullmatch(self.source):
            raise ValueError("container image source must be build or pull")

    @property
    def image_ref(self) -> str:
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
)
