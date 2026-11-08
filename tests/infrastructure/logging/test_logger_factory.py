from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory


class TestLoggerFactory(unittest.TestCase):
    def test_read_only_preflight_does_not_create_log_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.dict(os.environ, {"TSW_REPOSITORY_ROOT": str(root), "TSW_READ_ONLY_PREFLIGHT": "1"}):
                logger = LoggerFactory.get_logger("preflight-probe")
                logger.info("probe")
            self.assertFalse((root / ".tiny-swarm-world").exists())

    def test_real_logger_creates_private_state_before_real_installation_lease(self) -> None:
        from tiny_swarm_world.infrastructure.project_paths import ProjectPaths
        from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import JsonInstallationOperationLock

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = os.umask(0o022)
            try:
                logger = LoggerFactory.get_logger('fresh-private-logger', project_paths=ProjectPaths.from_roots(root))
            finally:
                os.umask(previous)
            try:
                logger.info('actual local log event')
                self.assertEqual((root / '.tiny-swarm-world').stat().st_mode & 0o777, 0o700)
                with JsonInstallationOperationLock(root).exclusive('setup') as lease:
                    lease.require_active()
                self.assertIn('actual local log event', (root / '.tiny-swarm-world/logs/fresh-private-logger.log').read_text())
            finally:
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)

    def test_unsafe_existing_state_roots_and_log_links_are_retained_without_repair(self) -> None:
        from tiny_swarm_world.infrastructure.project_paths import ProjectPaths

        for kind in ('mode', 'symlink', 'file', 'log_symlink'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                state = root / '.tiny-swarm-world'
                outside = root / 'original'
                outside.mkdir()
                marker = outside / 'preserved.log'
                marker.write_text('preserve original bytes')
                if kind == 'mode':
                    state.mkdir(mode=0o755)
                    state.chmod(0o755)
                elif kind == 'symlink':
                    state.symlink_to(outside, target_is_directory=True)
                elif kind == 'file':
                    state.write_text('preserve non-directory')
                else:
                    state.mkdir(mode=0o700)
                    (state / 'logs').mkdir(mode=0o700)
                    (state / 'logs/unsafe-existing.log').symlink_to(marker)
                with self.assertRaises(OSError):
                    LoggerFactory.get_logger('unsafe-existing', project_paths=ProjectPaths.from_roots(root))
                self.assertEqual(marker.read_text(), 'preserve original bytes')
                if kind == 'mode':
                    self.assertEqual(state.stat().st_mode & 0o777, 0o755)
                    self.assertEqual(list(state.iterdir()), [])
                if kind == 'symlink':
                    self.assertTrue(state.is_symlink())
                if kind == 'file':
                    self.assertEqual(state.read_text(), 'preserve non-directory')
