"""Declared workflow names and command metadata."""

from dataclasses import dataclass

from tiny_swarm_world.application.services.platform.workflow.semantics import (
    PLATFORM_WORKFLOW_TAXONOMY,
)
from tiny_swarm_world.application.services.platform.workflow.types import (
    PlatformWorkflowKind,
)


@dataclass(frozen=True)
class CliWorkflow:
    namespace: str
    action: str
    mutating: bool
    destructive: bool
    platform_kind: PlatformWorkflowKind | None = None
    confirmation_phrase: str | None = None

    @property
    def name(self) -> str:
        return f"{self.namespace} {self.action}"

    @property
    def implemented(self) -> bool:
        return self.platform_kind is not None or self.namespace in {
            "artifacts",
            "deployment",
            "host",
            "setup",
        }


PLATFORM_WORKFLOW_ORDER = (
    PlatformWorkflowKind.INIT,
    PlatformWorkflowKind.RECONCILE,
    PlatformWorkflowKind.UPDATE,
    PlatformWorkflowKind.EXPOSE,
    PlatformWorkflowKind.REPAIR_LXC_PROXY_DRIFT,
    PlatformWorkflowKind.VERIFY,
    PlatformWorkflowKind.RESET,
    PlatformWorkflowKind.DESTROY,
)


CLI_WORKFLOWS = (
    CliWorkflow(namespace="host", action="detect", mutating=False, destructive=False),
    CliWorkflow(namespace="host", action="preflight", mutating=False, destructive=False),
    CliWorkflow(namespace="host", action="prepare", mutating=True, destructive=False),
    CliWorkflow(namespace="host", action="verify", mutating=False, destructive=False),
    CliWorkflow(namespace="host", action="cleanup", mutating=True, destructive=True),
    *(
        CliWorkflow(
            namespace="platform",
            action=kind.value,
            mutating=PLATFORM_WORKFLOW_TAXONOMY[kind].mutating,
            destructive=PLATFORM_WORKFLOW_TAXONOMY[kind].destructive,
            platform_kind=kind,
            confirmation_phrase=PLATFORM_WORKFLOW_TAXONOMY[kind].confirmation_phrase,
        )
        for kind in PLATFORM_WORKFLOW_ORDER
    ),
    CliWorkflow(namespace="artifacts", action="prepare", mutating=True, destructive=False),
    CliWorkflow(namespace="artifacts", action="verify", mutating=False, destructive=False),
    CliWorkflow(namespace="deployment", action="bootstrap", mutating=True, destructive=False),
    CliWorkflow(namespace="deployment", action="apply", mutating=True, destructive=False),
    CliWorkflow(namespace="deployment", action="verify", mutating=False, destructive=False),
    CliWorkflow(namespace="setup", action="run", mutating=True, destructive=False),
)


CLI_WORKFLOWS_BY_KEY = {(workflow.namespace, workflow.action): workflow for workflow in CLI_WORKFLOWS}
