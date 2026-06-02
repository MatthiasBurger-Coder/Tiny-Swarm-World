from enum import Enum
import re
from typing import List

from pydantic import BaseModel, Field, field_validator, model_validator

from tiny_swarm_world.domain.command.command_runner_type_enum import CommandRunnerType
from tiny_swarm_world.domain.command.command_type_enum import CommandType
from tiny_swarm_world.domain.command.vm_type import VmType


class CommandCatalogValidationError(ValueError):
    """Raised when command catalog metadata is unsafe or malformed."""


class CommandExecutionMode(str, Enum):
    SHELL = "shell"


class CommandSafetyClass(str, Enum):
    SAFE_READ = "safe_read"
    SAFE_MUTATION = "safe_mutation"
    DESTRUCTIVE = "destructive"
    CREDENTIAL_MUTATION = "credential_mutation"
    NETWORK_MUTATION = "network_mutation"


class CommandScope(str, Enum):
    HOST = "host"
    VM = "vm"
    DOCKER = "docker"
    SWARM = "swarm"
    NETWORK = "network"


class CommandEffect(str, Enum):
    READ = "read"
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    PACKAGE_INSTALL = "package_install"
    PERMISSION_CHANGE = "permission_change"
    NETWORK_CHANGE = "network_change"
    CREDENTIAL_CHANGE = "credential_change"
    RUNTIME_CHANGE = "runtime_change"
    CREDENTIAL_OUTPUT = "credential_output"


class CommandVerifyType(str, Enum):
    NONE = "none"
    COMMAND = "command"
    MANUAL = "manual"


class CommandWorkflowId(str, Enum):
    PLATFORM_INIT = "platform:init"
    PLATFORM_RECONCILE = "platform:reconcile"
    PLATFORM_RESET = "platform:reset"
    PLATFORM_DESTROY = "platform:destroy"
    PLATFORM_VERIFY = "platform:verify"
    ARTIFACTS_PREPARE = "artifacts:prepare"
    ARTIFACTS_VERIFY = "artifacts:verify"
    DEPLOYMENT_APPLY = "deployment:apply"
    DEPLOYMENT_VERIFY = "deployment:verify"


DESTRUCTIVE_WORKFLOWS = frozenset(
    {
        CommandWorkflowId.PLATFORM_RESET.value,
        CommandWorkflowId.PLATFORM_DESTROY.value,
    }
)

DESTRUCTIVE_COMMAND_PATTERNS = (
    re.compile(r"\bdocker\s+system\s+prune\b", re.IGNORECASE),
    re.compile(r"\bdocker\s+volume\s+rm\b", re.IGNORECASE),
    re.compile(r"\bdocker\s+stack\s+rm\b", re.IGNORECASE),
    re.compile(r"\brm\s+-rf\b", re.IGNORECASE),
)


class CommandVerifySpec(BaseModel):
    type: CommandVerifyType
    description: str = Field(min_length=1)
    command: str | None = None

    model_config = {
        "extra": "forbid",
    }

    @model_validator(mode="after")
    def validate_command_verify(self) -> "CommandVerifySpec":
        if self.type == CommandVerifyType.COMMAND and not self.command:
            raise ValueError("command verify specs require a command")
        return self

    @property
    def is_command_backed(self) -> bool:
        return self.type == CommandVerifyType.COMMAND

    @property
    def is_manual_only(self) -> bool:
        return self.type == CommandVerifyType.MANUAL


class CommandEvidencePolicy(BaseModel):
    redact_output: bool = False
    store_raw_output: bool = False

    model_config = {
        "extra": "forbid",
    }


class CommandEntity(BaseModel):
    """
    Typed command catalog entry.

    :param index: order of execution (1, 2, 3, ...)
    :param id: stable command identity
    :param description: Description of the command
    :param intent: Human-readable command intent
    :param execution_mode: How the command is interpreted by the runner
    :param safety_class: Safety class for workflow policy checks
    :param scope: Owned product area affected by the command
    :param allowed_workflows: Workflows that may select this command
    :param parameters: Template parameters required by the command
    :param effects: Declared side effects or read effects
    :param verify: Verification specification for the command
    :param command: The actual command template
    :param runner: CommandRunner type (async, rest, ansible, ...)
    :param command_type: Command type (HOSTOS, VM, ...)
    :param vm_type: VM types (worker, manager, ...)
    """
    id: str = Field(min_length=1)
    index: int = Field(default=0)
    description: str = Field(default="")
    intent: str = Field(min_length=1)
    execution_mode: CommandExecutionMode
    safety_class: CommandSafetyClass
    scope: CommandScope
    allowed_workflows: List[str]
    parameters: List[str]
    effects: List[str]
    verify: CommandVerifySpec
    evidence_policy: CommandEvidencePolicy | None = None
    command: str = Field(default="")
    runner: str = Field(default="")
    command_type: CommandType = Field(default=CommandType.HOSTOS)
    vm_type: List[VmType] = Field(default_factory=lambda: [VmType.NONE])

    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "forbid",
    }

    @field_validator("runner")
    @classmethod
    def validate_runner(cls, value: str) -> str:
        CommandRunnerType.get_enum_from_value(value)
        return value

    @field_validator("allowed_workflows", "effects")
    @classmethod
    def validate_non_empty_lists(cls, value: list[object]) -> list[object]:
        if not value:
            raise ValueError("command metadata lists must not be empty")
        return value

    @field_validator("allowed_workflows")
    @classmethod
    def validate_allowed_workflows(cls, value: list[str]) -> list[str]:
        known_workflows = {workflow.value for workflow in CommandWorkflowId}
        unknown_workflows = [workflow for workflow in value if workflow not in known_workflows]
        if unknown_workflows:
            raise ValueError(f"unknown command workflow ids: {unknown_workflows}")
        return value

    @field_validator("effects")
    @classmethod
    def validate_effects(cls, value: list[str]) -> list[str]:
        known_effects = {effect.value for effect in CommandEffect}
        unknown_effects = [effect for effect in value if effect not in known_effects]
        if unknown_effects:
            raise ValueError(f"unknown command effects: {unknown_effects}")
        return value

    @field_validator("parameters")
    @classmethod
    def validate_parameters(cls, value: list[str]) -> list[str]:
        invalid = [parameter for parameter in value if not parameter or not isinstance(parameter, str)]
        if invalid:
            raise ValueError(f"invalid command parameters: {invalid}")
        return value

    @model_validator(mode="after")
    def validate_safety_contract(self) -> "CommandEntity":
        self._validate_destructive_pattern_policy()
        self._validate_verification_policy()
        self._validate_evidence_policy()
        self._validate_effect_policy()
        self._validate_sensitive_output_policy()
        self._validate_destructive_workflow_policy()
        return self

    def _validate_destructive_pattern_policy(self) -> None:
        if self.uses_destructive_shell_pattern() and self.safety_class != CommandSafetyClass.DESTRUCTIVE:
            raise ValueError("destructive shell patterns require safety_class=destructive")

    def _validate_verification_policy(self) -> None:
        if self.safety_class != CommandSafetyClass.SAFE_READ and self.verify.type == CommandVerifyType.NONE:
            raise ValueError("mutating commands require a verify specification")

    def _validate_evidence_policy(self) -> None:
        if self.evidence_policy and self.evidence_policy.store_raw_output:
            raise ValueError("command evidence policy must not store raw output")

    def _validate_effect_policy(self) -> None:
        if CommandEffect.RUNTIME_CHANGE.value in self.effects and self.safety_class == CommandSafetyClass.SAFE_READ:
            raise ValueError("runtime_change commands must not use safety_class=safe_read")

    def _validate_sensitive_output_policy(self) -> None:
        if not self.produces_sensitive_output:
            return
        if self.safety_class != CommandSafetyClass.CREDENTIAL_MUTATION:
            raise ValueError(
                "credential_output commands require safety_class=credential_mutation"
            )
        if not self.evidence_policy or not self.evidence_policy.redact_output:
            raise ValueError(
                "credential_output commands require a redacted evidence policy"
            )

    def _validate_destructive_workflow_policy(self) -> None:
        if self.safety_class != CommandSafetyClass.DESTRUCTIVE:
            return
        disallowed = [
            workflow
            for workflow in self.allowed_workflows
            if workflow not in DESTRUCTIVE_WORKFLOWS
        ]
        if disallowed:
            raise ValueError(
                f"destructive commands may only be allowed in reset/destroy workflows: {disallowed}"
            )

    def uses_destructive_shell_pattern(self) -> bool:
        return any(pattern.search(self.command) for pattern in DESTRUCTIVE_COMMAND_PATTERNS)

    @property
    def produces_sensitive_output(self) -> bool:
        return CommandEffect.CREDENTIAL_OUTPUT.value in self.effects

    @property
    def is_command_backed_verification(self) -> bool:
        return self.verify.is_command_backed

    @property
    def is_manual_only_verification(self) -> bool:
        return self.verify.is_manual_only

    def ensure_allowed_for_workflow(self, workflow_id: str) -> None:
        if not workflow_id:
            raise CommandCatalogValidationError(
                f"Command '{self.id}' requires an explicit workflow context"
            )
        if workflow_id not in self.allowed_workflows:
            raise CommandCatalogValidationError(
                f"Command '{self.id}' is not allowed for workflow '{workflow_id}'"
            )
        if self.safety_class == CommandSafetyClass.DESTRUCTIVE and workflow_id not in DESTRUCTIVE_WORKFLOWS:
            raise CommandCatalogValidationError(
                f"Command '{self.id}' is destructive and cannot run in workflow '{workflow_id}'"
            )
