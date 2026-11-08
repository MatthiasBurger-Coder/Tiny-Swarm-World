"""Sequential selected-batch coordination around the existing Classic executor."""
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError, ManifestRepository
from tiny_swarm_world.application.ports.lifecycle.component_execution import ComponentRuntime, UpdateJournal
from tiny_swarm_world.application.services.component_updates import ComponentUpdateService
from tiny_swarm_world.domain.lifecycle.models import ConfigurationReference
from tiny_swarm_world.domain.lifecycle.update_execution import UpdateBatch, UpdateStage
from tiny_swarm_world.domain.preflight import LiveConsent


class ComponentUpdateExecution:
    def __init__(self, planning: ComponentUpdateService, manifests: ManifestRepository,
                 journal: UpdateJournal, runtime: ComponentRuntime):
        self.planning, self.manifests = planning, manifests
        self.journal, self.runtime = journal, runtime

    async def run(self, requested: tuple[str, ...], target_id: str | None = None, *,
                  consent: LiveConsent | None, recovery: bool = False) -> dict[str, object]:
        if consent is None or not consent.accepted:
            return {'status': 'refused', 'diagnostics': ['Explicit live consent required.']}
        with self.journal.exclusive():
            batch = self._admit(requested, target_id, recovery)
            self.runtime.validate(batch.stages)
            batch = batch.model_copy(update={'direction': 'recover' if recovery else 'apply'})
            self.journal.save(batch)
            return await _execute(self, batch, consent, recovery)

    def _admit(self, requested: tuple[str, ...], target_id: str | None, recovery: bool) -> UpdateBatch:
        snapshot = self.manifests.load()
        previous = self.journal.load()
        if snapshot.manifest is None or snapshot.diagnostics:
            raise LifecycleStateError('Valid installation state required before execution.')
        if previous is not None:
            matching = (tuple(sorted(requested)) == previous.plan.requested_services
                        and (target_id is None or all(item.target and item.target.target_id == target_id
                                                     for item in previous.plan.services)))
            terminal = previous.settled
            if matching:
                if previous.original.installation_id != snapshot.manifest.installation_id:
                    raise LifecycleStateError('Update journal belongs to another installation.')
                if previous.direction == 'recover' and not recovery:
                    raise LifecycleStateError('This transition was recovered; inspect and preview a new transition explicitly.')
                _validate_manifest(previous, snapshot.manifest)
                if not recovery:
                    current_catalog = self.planning.catalog.load()
                    current_targets = {
                        service.service_id: {target.target_id: target for target in service.update_targets}
                        for service in current_catalog.services
                    }
                    for planned in previous.plan.services:
                        target = current_targets.get(planned.service_id, {}).get(
                            planned.target.target_id if planned.target else ""
                        )
                        if target is None or target.qualification != "qualified-transition":
                            raise LifecycleStateError(
                                'Forward resume is blocked because the current catalog no longer qualifies this target.'
                            )
                return previous
            if not terminal or recovery:
                raise LifecycleStateError('Another transition requires resume/recovery with its original service selection.')
        if recovery:
            raise LifecycleStateError('No original component transition is available for recovery.')
        plan = self.planning.preview(requested, target_id)
        if plan.status == 'blocked' or plan.manifest_token != snapshot.token:
            raise LifecycleStateError('Update plan blocked or stale; inspect supported targets and preview again.')
        if any((item.backup_required or item.migrations) and item.status != "no_op" for item in plan.services):
            raise LifecycleStateError('Backup/migration execution is unqualified; no mutation started. Image rollback is not data restore.')
        stages = tuple(UpdateStage(service_id=item.service_id, component_id=change.component_id,
                                   source=change.desired, target=change.target)
                       for item in plan.services for change in item.components if change.target is not None)
        return UpdateBatch(original=snapshot.manifest, plan=plan, stages=stages)


def _validate_manifest(batch, current):
    # Only this batch's verified component fields and managed pin references may differ.
    allowed = {stage.component_id: (stage.source, stage.target) for stage in batch.stages}
    original = {item.component_id: item for item in batch.original.components}
    for item in current.components:
        prior = original.get(item.component_id)
        if prior is None or item.service_id != prior.service_id or (item.component_id not in allowed and item != prior):
            raise LifecycleStateError('Installation changed outside this update; inspect before resuming.')
        if item.component_id in allowed and item.desired not in allowed[item.component_id]:
            raise LifecycleStateError('Desired image conflicts with the original transition.')
    if len(current.components) != len(batch.original.components):
        raise LifecycleStateError('Installation component inventory changed.')
    managed_keys = {'component-update.' + name for name in allowed}
    retained = tuple(item for item in current.configuration_references if item.key not in managed_keys)
    original_refs = tuple(item for item in batch.original.configuration_references if item.key not in managed_keys)
    if retained != original_refs:
        raise LifecycleStateError('Unrelated configuration changed during update.')
    ignored = {'components', 'configuration_references'}
    if current.model_dump(exclude=ignored) != batch.original.model_dump(exclude=ignored):
        raise LifecycleStateError('Installation selection or credentials changed; inspect before resuming.')


async def _execute(execution, batch, consent, recovery):
    indexes = range(len(batch.stages) - 1, -1, -1) if recovery else range(len(batch.stages))
    for index in indexes:
        stage = batch.stages[index]
        batch = _record(execution, batch, index, 'recovering' if recovery else 'applying')
        if not await execution.runtime.transition(stage, consent, recovery=recovery):
            batch = _record(execution, batch, index, 'failed')
            status = 'partial' if any(s.outcome in {'committed', 'recovered'} for s in batch.stages) else 'failed'
            return _result(batch, status)
        batch = _record(execution, batch, index, 'runtime_verified')
        _commit(execution, batch, stage, recovery)
        batch = _record(execution, batch, index, 'recovered' if recovery else 'committed')
    return _result(batch, 'recovered' if recovery else 'completed')


def _record(execution, batch, index, outcome):
    stages = list(batch.stages)
    stages[index] = stages[index].model_copy(update={'outcome': outcome})
    updated = batch.model_copy(update={'stages': tuple(stages)})
    execution.journal.save(updated)
    return updated


def _commit(execution, batch, stage, recovery):
    snapshot = execution.manifests.load()
    if snapshot.manifest is None or snapshot.diagnostics:
        raise LifecycleStateError('Runtime verified but configuration commit unavailable; resume the original operation.')
    _validate_manifest(batch, snapshot.manifest)
    version = stage.source if recovery else stage.target
    components = tuple(item.model_copy(update={'desired': version, 'observed': version})
                       if item.component_id == stage.component_id else item for item in snapshot.manifest.components)
    references = tuple(item for item in snapshot.manifest.configuration_references
                       if item.key != 'component-update.' + stage.component_id)
    reference = ConfigurationReference(key='component-update.' + stage.component_id,
                                       source='managed_default', reference=stage.component_id)
    updated = snapshot.manifest.model_copy(update={'components': components, 'configuration_references': (*references, reference)})
    execution.manifests.save(updated, expected_token=snapshot.token)


def _result(batch, status):
    return {'status': status, 'direction': batch.direction,
            'stages': [{'service_id': s.service_id, 'component_id': s.component_id, 'outcome': s.outcome}
                       for s in batch.stages], 'recovery_limit': 'Image rollback is not persistent-data restore.'}


def component_recovery_preview(journal: UpdateJournal, requested: tuple[str, ...]) -> dict[str, object]:
    """Describe the original reverse image transition without runtime initialization."""
    batch = journal.load()
    if batch is None or tuple(sorted(requested)) != batch.plan.requested_services:
        raise LifecycleStateError('Recovery requires the original recorded service selection.')
    return {'status': 'preview', 'direction': 'recover', 'execution': 'not performed (read-only preview)',
            'stages': [{'service_id': stage.service_id, 'component_id': stage.component_id,
                        'from': stage.target.model_dump(mode='json'), 'to': stage.source.model_dump(mode='json'),
                        'outcome': stage.outcome} for stage in reversed(batch.stages)],
            'recovery_limit': 'Image rollback is not persistent-data restore.'}
