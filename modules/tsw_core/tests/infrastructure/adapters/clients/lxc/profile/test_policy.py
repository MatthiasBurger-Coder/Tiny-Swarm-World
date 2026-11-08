import unittest

from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.policy import (
    profile_output_safe,
)


class TestLxcProfilePolicy(unittest.TestCase):
    def test_profile_output_rejects_unsafe_raw_configuration(self):
        self.assertFalse(
            profile_output_safe(
                "name: default\nconfig:\n  raw.lxc: unsafe\n",
                "default",
            )
        )

    def test_profile_output_accepts_safe_profile(self):
        self.assertTrue(
            profile_output_safe(
                "name: default\nconfig: {}\ndevices: {}\n",
                "default",
            )
        )
