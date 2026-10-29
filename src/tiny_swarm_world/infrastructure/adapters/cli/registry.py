"""Declared workflow names and command metadata."""

from argparse import Namespace
from collections.abc import Sequence
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

    def run_early(self, args: Namespace) -> bool:
        if (self.namespace, self.action) == ("services", "migration-preview"):
            from tiny_swarm_world.infrastructure.adapters.cli.migration_preview import run_migration_preview

            run_migration_preview()
            return True
        if (self.namespace, self.action) == ("services", "migration-check"):
            from tiny_swarm_world.infrastructure.adapters.cli.migration_admission import run_migration_check

            run_migration_check(args.migration_admission_request)
            return True
        if args.selection_preview:
            from tiny_swarm_world.infrastructure.adapters.cli.selection import run_selection_preview

            run_selection_preview(args)
            return True
        return False

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
            "product",
            "services",
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
    CliWorkflow(namespace="product", action="version", mutating=False, destructive=False),
    CliWorkflow(namespace="product", action="upgrade", mutating=True, destructive=False),
    CliWorkflow(namespace="services", action="migration-check", mutating=False, destructive=False),
    CliWorkflow(namespace="services", action="migration-preview", mutating=False, destructive=False),
    CliWorkflow(namespace="services", action="list", mutating=False, destructive=False),
    CliWorkflow(namespace="services", action="updates", mutating=False, destructive=False),
    CliWorkflow(namespace="services", action="update", mutating=True, destructive=False),
    CliWorkflow(namespace="services", action="add", mutating=True, destructive=False),
    CliWorkflow(namespace="services", action="remove", mutating=False, destructive=False),
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



def prepare_migration_preview_args(argv: Sequence[str] | None) -> list[str]:
    from tiny_swarm_world.infrastructure.adapters.cli.migration_preview import prepare_arguments

    return prepare_arguments(argv)



def prepare_migration_check_args(argv: Sequence[str] | None):
    from tiny_swarm_world.infrastructure.adapters.cli.migration_admission import prepare_arguments

    return prepare_arguments(argv)
