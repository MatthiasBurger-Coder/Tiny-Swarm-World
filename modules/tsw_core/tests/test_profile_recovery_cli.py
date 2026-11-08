"""Actual CLI parser boundaries for explicit scoped setup/add recovery."""
import contextlib
import io
import unittest
from unittest.mock import patch

from tiny_swarm_world.infrastructure.adapters.cli.parser import parse_args


class ProfileRecoveryCliTests(unittest.TestCase):
    def test_setup_selected_minimal_and_add_recovery_reach_transport_with_live_only(self):
        commands = (
            ('setup', 'run', '--minimal', '--recover', '--live', '--approve-live'),
            ('setup', 'run', '--services', 'swagger', '--recover', '--live', '--approve-live'),
            ('setup', 'run', '--recover', '--live', '--approve-live'),
            ('services', 'add', '--services', 'swagger', '--recover', '--live', '--approve-live'),
        )
        with patch('tiny_swarm_world.infrastructure.adapters.cli.selection.build_installation_lifecycle_service') as compose:
            for command in commands:
                with self.subTest(command=command):
                    args = parse_args(command)
                    self.assertTrue(args.recover)
                    self.assertTrue(args.live)
                    self.assertFalse(args.selection_preview)
                    self.assertEqual((args.workflow.namespace, args.workflow.action), command[:2])
                    self.assertEqual(args.selected_services, ('swagger',) if '--services' in command else None)
            compose.assert_not_called()

    def test_recovery_rejects_preview_missing_live_preflight_and_every_platform_update_option(self):
        commands = [
            ['setup', 'run', '--minimal', '--recover'],
            ['setup', 'run', '--recover', '--approve-live'],
            ['setup', 'run', '--minimal', '--recover', '--preview'],
            ['setup', 'run', '--minimal', '--recover', '--preview', '--live'],
            ['setup', 'run', '--recover', '--preflight', '--live'],
            ['services', 'add', '--services', 'swagger', '--recover'],
            ['services', 'add', '--services', 'swagger', '--recover', '--preview'],
            ['services', 'remove', '--services', 'swagger', '--recover', '--preview'],
            ['services', 'add', '--recover', '--live'],
        ]
        for option in ('--stack', '--service', '--from-image', '--to-image'):
            commands.append(['setup', 'run', '--minimal', '--recover', '--live', option, 'fixture'])
            commands.append(['services', 'add', '--services', 'swagger', '--recover', '--live', option, 'fixture'])
        with patch('tiny_swarm_world.infrastructure.adapters.cli.selection.build_installation_lifecycle_service') as compose:
            for command in commands:
                with self.subTest(command=command), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    parse_args(command)
                self.assertEqual(error.exception.code, 2)
            compose.assert_not_called()

    def test_existing_platform_recovery_keeps_its_separate_required_identity_guards(self):
        accepted = parse_args(['platform', 'update', '--recover', '--stack', 'swagger', '--service', 'nginx', '--live'])
        self.assertTrue(accepted.recover)
        for extra in ([], ['--from-image', 'fixture'], ['--to-image', 'fixture']):
            command = ['platform', 'update', '--recover', '--live']
            if extra:
                command.extend(['--stack', 'swagger', '--service', 'nginx', *extra])
            with self.subTest(extra=extra), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                parse_args(command)
            self.assertEqual(error.exception.code, 2)
