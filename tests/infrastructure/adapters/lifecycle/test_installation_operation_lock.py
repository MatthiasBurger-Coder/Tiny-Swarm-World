"""Real descriptor/process ownership plus explicit recording ports for use-case tests."""
import asyncio
from contextlib import contextmanager
import multiprocessing
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import JsonInstallationOperationLock


class FakeInstallationLease:
    def __init__(self, events):
        self.events = events
        self.operation_id = 'a' * 32
        self.active = True
        self.holder = None

    def require_active(self):
        if not self.active:
            raise LifecycleStateError('Expired fake lease.')

    @contextmanager
    def journal(self, kind):
        self.require_active()
        if self.holder is not None:
            raise LifecycleStateError('Competing fake journal.')
        self.holder = kind
        self.events.append('journal:' + kind)
        try:
            yield
        finally:
            self.events.append('journal-release:' + kind)
            self.holder = None


class FakeInstallationLock:
    """Explicit injected port: records admission and has no production fallback role."""
    def __init__(self, root=None):
        self.root = Path.cwd() if root is None else Path(root)
        self.events = []
        self.held = False

    @contextmanager
    def exclusive(self, operation, *, lease=None):
        if lease is not None:
            lease.require_active()
            yield lease
            return
        if self.held:
            raise LifecycleStateError('Competing fake operation.')
        self.held = True
        admitted = FakeInstallationLease(self.events)
        self.events.append('operation:' + operation)
        try:
            yield admitted
        finally:
            admitted.active = False
            self.held = False
            self.events.append('operation-release:' + operation)


def _hold_operation(root, ready, release):
    with JsonInstallationOperationLock(Path(root)).exclusive('setup'):
        ready.set()
        release.wait(10)


class InstallationOperationLockTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.root.chmod(0o755)  # Trusted owned ancestors need not all be 0700.
        self.lock = JsonInstallationOperationLock(self.root)

    def test_private_state_and_explicit_borrow_without_unlocked_fallback(self):
        self.assertFalse(self.lock.path.parent.exists())
        with self.lock.exclusive('setup') as lease:
            self.assertEqual(self.lock.path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(self.lock.path.parent.stat().st_mode & 0o777, 0o700)
            with self.lock.exclusive('selection', lease=lease) as borrowed:
                self.assertIs(borrowed, lease)
            lease.require_active()
            with self.assertRaises(LifecycleStateError):
                with JsonInstallationOperationLock(self.root).exclusive('setup'):
                    self.fail('independent writer entered')
        with self.assertRaises(LifecycleStateError):
            with self.lock.exclusive('setup', lease=lease):
                self.fail('expired lease entered')
        with self.lock.exclusive('setup'):
            pass

    def test_second_process_cannot_enter_or_replace_held_operation(self):
        context = multiprocessing.get_context('fork')
        ready, release = context.Event(), context.Event()
        process = context.Process(target=_hold_operation, args=(str(self.root), ready, release))
        process.start()
        try:
            self.assertTrue(ready.wait(5))
            with self.assertRaises(LifecycleStateError):
                with self.lock.exclusive('product-upgrade'):
                    self.fail('second process ownership ignored')
        finally:
            release.set()
            process.join(5)
            if process.is_alive():
                process.terminate()
                process.join(5)
        self.assertEqual(process.exitcode, 0)

    async def test_tasks_and_threads_need_explicit_lease_and_one_journal_claim(self):
        with self.lock.exclusive('setup') as lease:
            async def independent():
                with self.assertRaises(LifecycleStateError):
                    with self.lock.exclusive('setup'):
                        self.fail('Task inherited implicit ownership')
            await asyncio.create_task(independent())
            failures = []
            def independent_thread():
                try:
                    with self.lock.exclusive('setup'):
                        failures.append('entered')
                except LifecycleStateError:
                    failures.append('blocked')
            thread = threading.Thread(target=independent_thread)
            thread.start()
            thread.join(5)
            self.assertEqual(failures, ['blocked'])
            async def competing_journal():
                with self.lock.exclusive('product-upgrade', lease=lease):
                    with self.assertRaises(LifecycleStateError):
                        with lease.journal('product'):
                            self.fail('second journal admitted')
            with lease.journal('component'):
                await asyncio.create_task(competing_journal())
            with lease.journal('product'):
                pass

    def test_unsafe_existing_state_is_preserved_without_mode_repair(self):
        for case in ('directory_mode', 'symlink', 'hardlink', 'file_mode', 'fifo'):
            with self.subTest(case=case), TemporaryDirectory() as temporary:
                root = Path(temporary)
                state = root / '.tiny-swarm-world'
                state.mkdir(mode=0o700)
                directory = state / 'installation'
                directory.mkdir(mode=0o700)
                path = directory / 'operation.lock'
                if case == 'directory_mode':
                    state.chmod(0o755)
                elif case == 'symlink':
                    path.symlink_to(root / 'outside')
                elif case == 'hardlink':
                    path.write_text('retained')
                    path.chmod(0o600)
                    os.link(path, root / 'second')
                elif case == 'file_mode':
                    path.write_text('retained')
                    path.chmod(0o644)
                else:
                    os.mkfifo(path, 0o600)
                with self.assertRaises(LifecycleStateError) as error:
                    with JsonInstallationOperationLock(root).exclusive('setup'):
                        self.fail('unsafe state admitted')
                self.assertNotIn(str(root), str(error.exception))
                if case in {'hardlink', 'file_mode'}:
                    self.assertEqual(path.read_text(), 'retained')
                if case == 'directory_mode':
                    self.assertEqual(state.stat().st_mode & 0o777, 0o755)

    def test_replaced_lock_or_state_and_foreign_lease_fail_closed(self):
        with self.lock.exclusive('setup') as lease:
            self.lock.path.unlink()
            self.lock.path.write_text('replacement')
            self.lock.path.chmod(0o600)
            with self.assertRaises(LifecycleStateError):
                lease.require_active()
        with TemporaryDirectory() as other, self.lock.exclusive('setup') as lease:
            with self.assertRaises(LifecycleStateError):
                with JsonInstallationOperationLock(Path(other)).exclusive('setup', lease=lease):
                    self.fail('foreign anchor accepted')

    async def test_cancellation_releases_journal_before_operation(self):
        started = asyncio.Event()
        async def operation():
            with self.lock.exclusive('component-update') as lease, lease.journal('component'):
                started.set()
                await asyncio.Event().wait()
        task = asyncio.create_task(operation())
        await started.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        with self.lock.exclusive('product-upgrade') as lease, lease.journal('product'):
            pass


def use_fake_composition_locks(test_case):
    """Explicitly inject recording ports when existing tests mock every host workflow."""
    from unittest.mock import patch

    for module in ('tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock',
                   'tiny_swarm_world.infrastructure.composition_operation',
                   'tiny_swarm_world.infrastructure.composition_lifecycle'):
        test_case.enterContext(patch(module + '.JsonInstallationOperationLock', FakeInstallationLock, create=True))


class ComposedOperationLockTests(unittest.IsolatedAsyncioTestCase):
    async def test_same_top_level_workflow_cannot_implicitly_borrow_another_tasks_lease(self):
        from dataclasses import dataclass
        from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import locked_workflows

        entered, release = asyncio.Event(), asyncio.Event()
        class Workflow:
            async def run(self):
                entered.set()
                await release.wait()
                return 'completed'
        @dataclass(frozen=True)
        class Group:
            init: object
            verify: object
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = Workflow()
            group = locked_workflows(Group(raw, raw), root, 'platform')
            self.assertIs(group.verify, raw)
            self.assertFalse((root / '.tiny-swarm-world').exists())
            first = asyncio.create_task(group.init.run())
            await entered.wait()
            try:
                with self.assertRaises(LifecycleStateError):
                    await group.init.run()
            finally:
                release.set()
                self.assertEqual(await first, 'completed')
            self.assertEqual(await group.init.run(), 'completed')

    async def test_setup_private_children_do_not_lend_authority_to_public_same_object(self):
        from dataclasses import dataclass
        from types import SimpleNamespace
        from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import (
            bind_operation_lease, locked_setup_services, locked_workflows,
        )

        entered, release = asyncio.Event(), asyncio.Event()
        effects = []
        class Writer:
            async def run(self):
                effects.append('init')
        @dataclass(frozen=True)
        class Platform:
            init: object
            destroy: object
        @dataclass(frozen=True)
        class Workflows:
            run: object
        @dataclass(frozen=True)
        class Services:
            workflows: object
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            public = locked_workflows(Platform(Writer(), Writer()), root, 'platform')
            def compose(lease):
                private = bind_operation_lease(public, lease)
                async def run():
                    await private.init.run()
                    entered.set()
                    await release.wait()
                    await private.init.run()
                    return 'completed'
                return Services(Workflows(SimpleNamespace(run=run)))
            setup = locked_setup_services(compose(None), root, compose)
            task = asyncio.create_task(setup.workflows.run.run())
            await entered.wait()
            try:
                self.assertIsNone(public.init.lease)
                self.assertIsNone(public.destroy.lease)
                with self.assertRaises(LifecycleStateError):
                    await public.destroy.run()
                with self.assertRaises(LifecycleStateError):
                    await setup.workflows.run.run()
                self.assertEqual(effects, ['init'])
            finally:
                release.set()
                self.assertEqual(await task, 'completed')
            self.assertEqual(effects, ['init', 'init'])
            await public.destroy.run()
            self.assertEqual(effects, ['init', 'init', 'init'])

    async def test_private_platform_lifecycle_aliases_do_not_mutate_public_orchestrator(self):
        from dataclasses import dataclass
        from tiny_swarm_world.application.services.platform.lifecycle import (
            PlatformLifecycleOrchestrator, PlatformLifecycleRequest, PlatformLifecycleWorkflows,
        )
        from tiny_swarm_world.application.services.platform.workflow.types import PlatformWorkflowKind
        from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import (
            bind_operation_lease, locked_workflows,
        )
        effects = []
        class Writer:
            async def run(self, *args):
                effects.append('write')
        @dataclass(frozen=True)
        class Services:
            workflows: object
            lifecycle: object
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            writer = Writer()
            workflows = locked_workflows(PlatformLifecycleWorkflows(
                writer, writer, writer, writer, writer, writer, writer), root, 'platform')
            public = Services(workflows, PlatformLifecycleOrchestrator(workflows))
            with JsonInstallationOperationLock(root).exclusive('setup') as lease:
                private = bind_operation_lease(public, lease)
                self.assertIsNot(private.lifecycle, public.lifecycle)
                await private.lifecycle.run(PlatformLifecycleRequest(PlatformWorkflowKind.INIT))
                with self.assertRaises(LifecycleStateError):
                    await public.lifecycle.run(PlatformLifecycleRequest(PlatformWorkflowKind.DESTROY))
                self.assertEqual(effects, ['write'])
                self.assertIsNone(public.workflows.init.lease)

    async def test_repeated_cancellation_retains_real_outer_lock_until_worker_settles(self):
        from tiny_swarm_world.application.services.product_upgrade import _blocking
        from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import InstallationLockedWorkflow

        started, release = threading.Event(), threading.Event()
        def write():
            started.set()
            if not release.wait(5):
                raise AssertionError('worker not released')
        class Workflow:
            async def run(self):
                await _blocking(write)
        with TemporaryDirectory() as temporary:
            lock = JsonInstallationOperationLock(Path(temporary))
            wrapped = InstallationLockedWorkflow(Workflow(), lock, 'setup')
            task = asyncio.create_task(wrapped.run())
            self.assertTrue(await asyncio.to_thread(started.wait, 2))
            task.cancel()
            await asyncio.sleep(0)
            task.cancel()
            await asyncio.sleep(0)
            try:
                self.assertFalse(task.done())
                with self.assertRaises(LifecycleStateError):
                    with lock.exclusive('setup'):
                        self.fail('outer ownership released early')
            finally:
                release.set()
                with self.assertRaises(asyncio.CancelledError):
                    await task
            with lock.exclusive('setup'):
                pass

    def test_dedicated_product_journal_and_lease_claim_do_not_create_component_lock(self):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_journal import JsonProductJournal

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            lock = JsonInstallationOperationLock(root)
            product = JsonProductJournal(lock.path.parent / 'product-upgrade.json')
            with lock.exclusive('product-upgrade') as lease, lease.journal('product'), product.exclusive():
                self.assertTrue((lock.path.parent / 'product-upgrade.lock').is_file())
                self.assertFalse((lock.path.parent / 'component-update.lock').exists())
                with self.assertRaises(LifecycleStateError):
                    with lease.journal('component'):
                        self.fail('nested journal admitted')

    def test_windows_or_unknown_mount_and_fsync_failure_never_enter_workflow(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from tiny_swarm_world.domain.project_filesystem import ProjectFilesystemKind

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            lock = JsonInstallationOperationLock(root)
            for kind in (ProjectFilesystemKind.WINDOWS_MOUNTED, ProjectFilesystemKind.UNKNOWN):
                with patch('tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock.ProjectFilesystemInspector') as inspector:
                    inspector.return_value.inspect.return_value = SimpleNamespace(kind=kind)
                    with self.assertRaises(LifecycleStateError):
                        with lock.exclusive('setup'):
                            self.fail('unsupported filesystem admitted')
                    self.assertFalse((root / '.tiny-swarm-world').exists())
            with patch('tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock.os.fsync', side_effect=OSError('private-fsync-canary')):
                with self.assertRaises(LifecycleStateError) as error:
                    with lock.exclusive('setup'):
                        self.fail('uncertain durability admitted')
            self.assertNotIn('private-fsync-canary', str(error.exception))
