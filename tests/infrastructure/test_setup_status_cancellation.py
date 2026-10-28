"""Cancellation must terminate the real empty-instance setup status worker."""
import asyncio
from contextlib import suppress
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tiny_swarm_world.application.ports.ui.port_ui import AGGREGATE_INSTANCE, STATUS_ERROR
from tiny_swarm_world.application.services.setup.workflow import SetupWorkflow, SetupWorkflowPhase
from tiny_swarm_world.domain.preflight import LiveConsent
from tiny_swarm_world.infrastructure import composition
from tiny_swarm_world.infrastructure.adapters.ui.linux_ui import LinuxUI


class SetupStatusCancellationTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancelled_real_workflow_joins_empty_linux_ui_and_propagates_cancellation(self):
        entered = asyncio.Event()
        finalized = asyncio.Event()

        async def waiting_phase():
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                finalized.set()

        consent = LiveConsent(True, confirmed=True)
        workflow = SetupWorkflow((SetupWorkflowPhase('deployment apply', waiting_phase),),
                                 live_consent=consent, heartbeat_interval_seconds=0.01)
        ui = LinuxUI(instances=(), test_mode=False)
        services = SimpleNamespace(workflows=SimpleNamespace(run=workflow))
        with (patch.object(composition, 'ensure_product_mutation_available'),
              patch.object(composition, 'build_setup_ui', return_value=ui),
              patch.object(composition, 'build_configuration_validation_service', return_value=Mock()),
              patch.object(composition, 'build_setup_services', return_value=services)):
            task = asyncio.create_task(composition.run_setup_with_terminal_status(consent, 'run'))
            try:
                await asyncio.wait_for(entered.wait(), timeout=2)
                original_ui_thread = ui.ui_thread
                self.assertIsNotNone(original_ui_thread)
                self.assertFalse(original_ui_thread.done())
                task.cancel()
                done, _ = await asyncio.wait({task}, timeout=2)
                self.assertIn(task, done, 'Cancelled setup still waits for a nonterminal UI worker.')
                with self.assertRaises(asyncio.CancelledError):
                    await task
                self.assertTrue(finalized.is_set())
                self.assertEqual(ui.aggregate_status['result'], STATUS_ERROR)
                self.assertEqual(ui.aggregate_status['current_step'], 'cancelled')
                self.assertIs(ui.ui_thread, original_ui_thread)
                self.assertTrue(original_ui_thread.done())
                self.assertFalse(original_ui_thread.cancelled())
            finally:
                # Release the real worker even when the old implementation fails
                # the bounded completion assertion; never strand its executor.
                ui.update_status(AGGREGATE_INSTANCE, 'test cleanup', 'terminal', STATUS_ERROR)
                if not task.done() and not task.cancelling():
                    task.cancel()
                futures = {task}
                if ui.ui_thread is not None:
                    futures.add(ui.ui_thread)
                done, pending = await asyncio.wait(futures, timeout=2)
                for future in done:
                    with suppress(asyncio.CancelledError):
                        future.result()
                self.assertFalse(pending, 'Test cleanup did not drain setup/status workers.')
