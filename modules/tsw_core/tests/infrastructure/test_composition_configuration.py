import os
import unittest
from unittest.mock import patch

from tiny_swarm_world.infrastructure.composition_configuration import (
    DEFAULT_SWARM_REGISTRY_ENDPOINT,
    _lxc_proxy_listen_address,
    _operator_config_float,
    _operator_config_int,
    _operator_secret_value,
    _infisical_provider_mode,
    _self_hosted_infisical_url,
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

    def test_infisical_provider_mode_rejects_unsupported_external_mixing(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual("self_hosted", _infisical_provider_mode())

        with patch.dict(os.environ, {"TSW_INFISICAL_PROVIDER_MODE": "external"}, clear=True):
            with self.assertRaisesRegex(ValueError, "not supported"):
                _infisical_provider_mode()

        with patch.dict(os.environ, {"TSW_INFISICAL_PROVIDER_MODE": "invalid"}, clear=True):
            with self.assertRaisesRegex(ValueError, "self_hosted or external"):
                _infisical_provider_mode()

    def test_self_hosted_infisical_url_rejects_unclassified_remote_endpoint(self):
        with patch.dict(
            os.environ,
            {"TSW_INFISICAL_URL": "https://infisical.example.test"},
            clear=True,
        ):
            with self.assertRaisesRegex(ValueError, "must target localhost"):
                _self_hosted_infisical_url()

    def test_self_hosted_infisical_url_uses_local_default(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual("http://localhost:17080", _self_hosted_infisical_url())


if __name__ == "__main__":
    unittest.main()
