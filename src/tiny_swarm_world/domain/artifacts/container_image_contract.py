from __future__ import annotations

import re
from dataclasses import dataclass


IMAGE_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9/:._-]*[a-z0-9]$")
IMAGE_TAG_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
BUILD_CONTEXT_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


@dataclass(frozen=True)
class ContainerImageContract:
    image_name: str
    tag: str
    build_context: str

    def __post_init__(self) -> None:
        if not IMAGE_NAME_PATTERN.fullmatch(self.image_name):
            raise ValueError("container image name contains invalid characters")
        if not IMAGE_TAG_PATTERN.fullmatch(self.tag):
            raise ValueError("container image tag contains invalid characters")
        if not BUILD_CONTEXT_PATTERN.fullmatch(self.build_context):
            raise ValueError("container image build context contains invalid characters")

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
        }


DEFAULT_CONTAINER_IMAGE_CONTRACTS = (
    ContainerImageContract(
        image_name="127.0.0.1:5000/jenkins",
        tag="latest",
        build_context="jenkins",
    ),
    ContainerImageContract(
        image_name="127.0.0.1:5000/service-access-dashboard",
        tag="latest",
        build_context="service-access-dashboard",
    ),
    ContainerImageContract(
        image_name="127.0.0.1:5000/service-access-nginx",
        tag="latest",
        build_context="service-access-nginx",
    ),
)
