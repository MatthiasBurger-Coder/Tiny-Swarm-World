import importlib
import inspect
import unittest
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MethodTraceManifestEntry:
    owner: str
    method: str
    status: str
    reason: str


COVERED = "covered"
EXEMPT = "exempt"
ALLOWED_STATUSES = {COVERED, EXEMPT}
ALLOWED_EXEMPTION_REASONS = {
    "protocol declaration",
    "result serialization outside installation runtime flow",
    "trace sink internals",
    "terminal render loop",
    "method outside installation runtime path",
}

TRACE_RUNTIME_OWNERS = (
    "tiny_swarm_world.application.services.setup.workflow.SetupWorkflowPhase",
    "tiny_swarm_world.application.services.setup.workflow.SetupWorkflowResult",
    "tiny_swarm_world.application.services.setup.workflow.SetupPhaseResult",
    "tiny_swarm_world.application.services.setup.workflow.SetupWorkflow",
    "tiny_swarm_world.application.services.platform.workflows.PlatformInitWorkflow",
    "tiny_swarm_world.application.services.platform.workflows.PlatformReconcileWorkflow",
    "tiny_swarm_world.application.services.platform.workflows.PlatformResetWorkflow",
    "tiny_swarm_world.application.services.platform.workflows.PlatformDestroyWorkflow",
    "tiny_swarm_world.application.services.platform.workflows.PlatformVerifyWorkflow",
    "tiny_swarm_world.application.services.commands.command_executer.command_executer.CommandExecuter",
)

TRACE_COVERAGE_MANIFEST = (
    MethodTraceManifestEntry(
        owner="tiny_swarm_world.application.services.setup.workflow.SetupWorkflowPhase",
        method="run",
        status=COVERED,
        reason="setup phase execution is part of installation runtime flow",
    ),
    MethodTraceManifestEntry(
        owner="tiny_swarm_world.application.services.setup.workflow.SetupWorkflowResult",
        method="to_dict",
        status=EXEMPT,
        reason="result serialization outside installation runtime flow",
    ),
    MethodTraceManifestEntry(
        owner="tiny_swarm_world.application.services.setup.workflow.SetupPhaseResult",
        method="to_dict",
        status=EXEMPT,
        reason="result serialization outside installation runtime flow",
    ),
    MethodTraceManifestEntry(
        owner="tiny_swarm_world.application.services.setup.workflow.SetupWorkflow",
        method="run",
        status=COVERED,
        reason="setup orchestration is part of installation runtime flow",
    ),
    MethodTraceManifestEntry(
        owner="tiny_swarm_world.application.services.platform.workflows.PlatformInitWorkflow",
        method="run",
        status=COVERED,
        reason="platform init is part of installation runtime flow",
    ),
    MethodTraceManifestEntry(
        owner="tiny_swarm_world.application.services.platform.workflows.PlatformReconcileWorkflow",
        method="run",
        status=COVERED,
        reason="platform reconcile is part of installation runtime flow",
    ),
    MethodTraceManifestEntry(
        owner="tiny_swarm_world.application.services.platform.workflows.PlatformResetWorkflow",
        method="run",
        status=COVERED,
        reason="platform reset is a guarded platform runtime flow",
    ),
    MethodTraceManifestEntry(
        owner="tiny_swarm_world.application.services.platform.workflows.PlatformDestroyWorkflow",
        method="run",
        status=COVERED,
        reason="platform destroy is a guarded platform runtime flow",
    ),
    MethodTraceManifestEntry(
        owner="tiny_swarm_world.application.services.platform.workflows.PlatformVerifyWorkflow",
        method="run",
        status=COVERED,
        reason="platform verify is part of installation runtime flow",
    ),
    MethodTraceManifestEntry(
        owner=(
            "tiny_swarm_world.application.services.commands.command_executer."
            "command_executer.CommandExecuter"
        ),
        method="execute",
        status=COVERED,
        reason="command execution is part of installation runtime flow",
    ),
)


class TestInstallationMethodTraceCoverage(unittest.TestCase):
    def test_manifest_covers_all_public_runtime_methods(self):
        missing_entries = sorted(_public_runtime_methods() - _manifest_methods())

        self.assertEqual([], missing_entries)

    def test_manifest_entries_reference_existing_methods(self):
        unknown_entries = sorted(_manifest_methods() - _public_runtime_methods())

        self.assertEqual([], unknown_entries)

    def test_manifest_entries_have_valid_status(self):
        invalid_entries = [
            f"{entry.owner}.{entry.method}: {entry.status}"
            for entry in TRACE_COVERAGE_MANIFEST
            if entry.status not in ALLOWED_STATUSES
        ]

        self.assertEqual([], invalid_entries)

    def test_exemptions_use_explicit_allowed_reasons(self):
        invalid_exemptions = [
            f"{entry.owner}.{entry.method}: {entry.reason}"
            for entry in TRACE_COVERAGE_MANIFEST
            if entry.status == EXEMPT and entry.reason not in ALLOWED_EXEMPTION_REASONS
        ]

        self.assertEqual([], invalid_exemptions)

    def test_covered_entries_are_not_using_exemption_reasons(self):
        invalid_covered_entries = [
            f"{entry.owner}.{entry.method}: {entry.reason}"
            for entry in TRACE_COVERAGE_MANIFEST
            if entry.status == COVERED and entry.reason in ALLOWED_EXEMPTION_REASONS
        ]

        self.assertEqual([], invalid_covered_entries)


def _manifest_methods() -> set[str]:
    return {f"{entry.owner}.{entry.method}" for entry in TRACE_COVERAGE_MANIFEST}


def _public_runtime_methods() -> set[str]:
    methods: set[str] = set()
    for owner in TRACE_RUNTIME_OWNERS:
        owner_type = _resolve_owner(owner)
        methods.update(
            f"{owner}.{method_name}"
            for method_name, method in inspect.getmembers(owner_type, inspect.isfunction)
            if _is_public_runtime_method(method_name, method)
        )
    return methods


def _resolve_owner(owner: str) -> Any:
    module_name, class_name = owner.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def _is_public_runtime_method(method_name: str, method: Any) -> bool:
    if method_name.startswith("_"):
        return False
    if method_name == "__init__":
        return False
    return not getattr(method, "__isabstractmethod__", False)
