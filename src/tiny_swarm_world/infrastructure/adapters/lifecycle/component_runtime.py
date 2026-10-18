"""Map component identities onto the existing #297 Classic update boundary."""
import asyncio

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.operation_result import OperationError
from tiny_swarm_world.application.services.platform.workflow.update import ClassicUpdateWorkflow
from tiny_swarm_world.domain.lifecycle.models import VersionIdentity
from tiny_swarm_world.domain.lifecycle.update_execution import UpdateStage
from tiny_swarm_world.domain.preflight import LiveConsent
from tiny_swarm_world.domain.update import ClassicUpdatePlan
from tiny_swarm_world.domain.update.classic_update import IMAGE_OVERRIDE_ENVIRONMENT_BY_STACK_SERVICE


def image_reference(version: VersionIdentity) -> str:
    if not version.image_repository or not version.image_digest:
        raise LifecycleStateError('Execution requires immutable image identities.')
    return version.image_repository + '@' + version.image_digest


def compose_service(stage: UpdateStage) -> str:
    name = 'infisical-db' if stage.component_id == 'infisical-postgres' else stage.component_id
    if f'{stage.service_id}:{name}' not in IMAGE_OVERRIDE_ENVIRONMENT_BY_STACK_SERVICE:
        raise LifecycleStateError('Component has no supported Classic image-transition adapter; no mutation started.')
    return name


class ClassicComponentRuntime:
    def __init__(self, workflow: ClassicUpdateWorkflow):
        self.workflow = workflow

    def validate(self, stages: tuple[UpdateStage, ...]) -> None:
        for stage in stages:
            compose_service(stage)
            image_reference(stage.source)
            image_reference(stage.target)

    async def transition(self, stage: UpdateStage, consent: LiveConsent, *, recovery: bool) -> bool:
        name = compose_service(stage)
        source, target = image_reference(stage.source), image_reference(stage.target)
        try:
            # Recovery also handles stages never reached in a failed batch without
            # requiring rollback state for an update that never ran.
            if recovery or source == target:
                observer = self.workflow.runtime_observer
                if observer is None:
                    return False
                observed = await asyncio.wait_for(observer.observe(stage.service_id, name),
                                                  timeout=self.workflow.observation_timeout_seconds)
                wanted = source if recovery else target
                if (observed.stack_name == stage.service_id and observed.service_name == name
                        and observed.service_id and observed.converged(wanted, allow_completed_rollback=recovery)):
                    return True
                if source == target:
                    return False
            plan = ClassicUpdatePlan(stage.service_id, name, source, target)
            state = self.workflow.state_store.load(stage.service_id, name)
            if recovery and state is not None and state.plan != plan:
                raise LifecycleStateError('Classic recovery metadata conflicts with this component transition.')
            if recovery:
                result = await self.workflow.recover(stage.service_id, name, preview=False, live_consent=consent)
            else:
                result = await self.workflow.run(plan, preview=False, live_consent=consent)
            if result.status.value != 'completed':
                return False
            # Classic returns early when runtime is already at the target. Retain
            # the journal's original transition even on this converged no-op.
            if not recovery:
                retained = self.workflow.state_store.load(stage.service_id, name)
                if retained is None or retained.plan != plan:
                    self.workflow.state_store.save(plan)
            return True
        except (OperationError, OSError, TimeoutError, ValueError):
            return False
