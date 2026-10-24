"""Product transport validation, preview isolation and consent regressions."""
from contextlib import redirect_stdout, redirect_stderr
import io
import unittest
from unittest.mock import AsyncMock, patch
from types import SimpleNamespace

from tiny_swarm_world.infrastructure.adapters.cli.dispatcher import main
from tiny_swarm_world.infrastructure.adapters.cli.parser import parse_args


class ProductCliTests(unittest.IsolatedAsyncioTestCase):
    def test_valid_preview_live_and_recovery_commands(self):
        for mode in (['--preview'], ['--live', '--approve-live'], ['--live', '--approve-live', '--recover']):
            args = parse_args(['product', 'upgrade', '--to', '0.5.0', *mode])
            self.assertTrue(args.product_upgrade_command)

    def test_invalid_targets_and_conflicting_options(self):
        invalid = [[], ['--to', '0.4.0', '--preview'], ['--to', '../0.5.0', '--preview'],
                   ['--to', '0.5.0'], ['--to', '0.5.0', '--preview', '--live'],
                   ['--to', '0.5.0', '--preview', '--approve-live'],
                   ['--to', '0.5.0', '--preview', '--services', 'jenkins'],
                   ['--to', '0.5.0', '--preview', '--stack', 'jenkins'],
                   ['--to', '0.5.0', '--preview', '--recover', '--adoption-manifest', 'inventory.json']]
        for options in invalid:
            with self.subTest(options=options), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                parse_args(['product', 'upgrade', *options])
            self.assertEqual(caught.exception.code, 2)

    def test_help_exposes_product_target_and_adoption_option(self):
        output = io.StringIO()
        with redirect_stdout(output), self.assertRaises(SystemExit) as caught:
            parse_args(['product', 'upgrade', '--help'])
        self.assertEqual(caught.exception.code, 0)
        self.assertIn('--adoption-manifest', output.getvalue())

    async def test_preview_only_invokes_read_only_application_path(self):
        with patch('tiny_swarm_world.infrastructure.composition.build_product_upgrade') as build, redirect_stdout(io.StringIO()):
            build.return_value.preview = AsyncMock(return_value={'status': 'preview'})
            build.return_value.run = AsyncMock()
            await main(['product', 'upgrade', '--to', '0.5.0', '--preview'])
            build.return_value.preview.assert_awaited_once_with('0.5.0', recovery=False)
            build.return_value.run.assert_not_awaited()

    async def test_declined_consent_never_builds_release_or_runtime_adapters(self):
        with patch('builtins.input', return_value='no'), patch('tiny_swarm_world.infrastructure.composition.build_product_upgrade') as build:
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as caught:
                await main(['product', 'upgrade', '--to', '0.5.0', '--live'])
            self.assertEqual(caught.exception.code, 2)
            build.assert_not_called()

    async def test_error_does_not_echo_sensitive_adapter_details(self):
        with patch('tiny_swarm_world.infrastructure.composition.build_product_upgrade', side_effect=ValueError('SECRET_SENTINEL')):
            output = io.StringIO()
            with redirect_stdout(output), self.assertRaises(SystemExit):
                await main(['product', 'upgrade', '--to', '0.5.0', '--preview'])
            self.assertNotIn('SECRET_SENTINEL', output.getvalue())

    async def test_failure_after_switch_reports_failed_stage_instead_of_pre_mutation_block(self):
        from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError

        with patch('tiny_swarm_world.infrastructure.composition.build_product_upgrade') as build:
            build.return_value.run = AsyncMock(side_effect=LifecycleStateError('Manifest persistence unavailable.'))
            build.return_value.journal.load.return_value = SimpleNamespace(stage='committing')
            output = io.StringIO()
            with redirect_stdout(output), self.assertRaises(SystemExit):
                await main(['product', 'upgrade', '--to', '0.5.0', '--live', '--approve-live'])
            self.assertIn('"status": "failed"', output.getvalue())
            self.assertIn('"stage": "committing"', output.getvalue())
