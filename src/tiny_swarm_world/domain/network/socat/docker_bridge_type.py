from enum import Enum


class DockerBridgeType(str, Enum):
    BRIDGE = "bridge"
    DOCKER_GWBRIDGE = "docker_gwbridge"
    NONE = "none"

    @staticmethod
    def get_enum_from_value(value: str) -> "DockerBridgeType":
        for enum_member in DockerBridgeType:
            if enum_member.value == value:
                return enum_member
        raise ValueError(f"Value '{value}' does not match any DockerBridgeType.")