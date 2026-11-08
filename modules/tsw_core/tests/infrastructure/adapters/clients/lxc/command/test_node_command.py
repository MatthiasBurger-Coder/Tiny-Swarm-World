import unittest

from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.node_command import (
    LxcNodeCommandResult,
    safe_process_text,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import (
    LxcNodeCommandResult as LegacyResult,
)


class TestLxcNodeCommand(unittest.TestCase):
    def test_command_result_is_owned_by_command_boundary_and_legacy_import_is_stable(self):
        self.assertIs(LxcNodeCommandResult, LegacyResult)
        self.assertEqual(
            "tiny_swarm_world.infrastructure.adapters.clients.lxc.command.node_command",
            LxcNodeCommandResult.__module__,
        )

    def test_process_text_handles_none_and_invalid_utf8_without_raw_bytes(self):
        self.assertEqual("", safe_process_text(None))
        self.assertEqual("ready", safe_process_text(b"ready\xff"))
