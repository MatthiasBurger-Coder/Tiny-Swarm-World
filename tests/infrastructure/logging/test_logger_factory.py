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
