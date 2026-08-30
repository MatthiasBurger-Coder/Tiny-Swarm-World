import os
import unittest
from unittest.mock import patch

from tiny_swarm_world.infrastructure.composition_configuration import (
    DEFAULT_SWARM_REGISTRY_ENDPOINT,
    _secret_mode,
    _lxc_proxy_listen_address,
    _operator_config_float,
    _operator_config_int,
    _operator_secret_value,
    _required_operator_secret_value,
    _swarm_registry_endpoint,
)


class TestCompositionConfiguration(unittest.TestCase):
    def test_numeric_configuration_uses_defaults_and_rejects_invalid_values(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(2, _operator_config_int("TSW_TEST_INT", 2, minimum=1))
            self.assertEqual(1.5, _operator_config_float("TSW_TEST_FLOAT", 1.5, minimum=0.0))

        with patch.dict(os.environ, {"TSW_TEST_INT": "0"}, clear=True):
            with self.assertRaisesRegex(ValueError, "at least 1"):
                _operator_config_int("TSW_TEST_INT", 2, minimum=1)

        with patch.dict(os.environ, {"TSW_TEST_FLOAT": "not-a-number"}, clear=True):
            with self.assertRaisesRegex(ValueError, "must be a number"):
                _operator_config_float("TSW_TEST_FLOAT", 1.5, minimum=0.0)

    def test_secret_access_preserves_placeholder_and_required_secret_guard(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                "<operator-supplied:TSW_EXAMPLE_SECRET>",
                _operator_secret_value("TSW_EXAMPLE_SECRET"),
            )
            with self.assertRaisesRegex(ValueError, "TSW_EXAMPLE_SECRET"):
                _required_operator_secret_value("TSW_EXAMPLE_SECRET")

        with patch.dict(os.environ, {"TSW_EXAMPLE_SECRET": "value"}, clear=True):
            self.assertEqual("value", _required_operator_secret_value("TSW_EXAMPLE_SECRET"))

    def test_registry_and_proxy_values_are_validated_in_configuration_module(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(DEFAULT_SWARM_REGISTRY_ENDPOINT, _swarm_registry_endpoint())
            self.assertEqual("0.0.0.0", _lxc_proxy_listen_address())

        with patch.dict(os.environ, {"TSW_SWARM_REGISTRY_ENDPOINT": "https://unsafe"}, clear=True):
            with self.assertRaisesRegex(ValueError, r"host\[:port\]"):
                _swarm_registry_endpoint()

        with patch.dict(os.environ, {"TSW_LXC_PROXY_LISTEN_ADDRESS": "localhost"}, clear=True):
            with self.assertRaisesRegex(ValueError, "listen address"):
                _lxc_proxy_listen_address()

    def test_secret_mode_prefers_internal_test_with_no_file_dependency(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual("generated", _secret_mode())

        with patch.dict(os.environ, {"TSW_SECRETS_MODE": "internal-test"}, clear=True):
            self.assertEqual("internal-test", _secret_mode())

        with patch.dict(os.environ, {"TSW_SECRETS_MODE": "bad-mode"}, clear=True):
            with self.assertRaisesRegex(ValueError, "internal-test"):
                _secret_mode()


if __name__ == "__main__":
    unittest.main()
