import unittest
from unittest.mock import patch

from tiny_swarm_world.infrastructure.os_types import OsTypes, _has_wsl_signal


class TestOsTypes(unittest.TestCase):
    def test_maps_wsl_values_to_wsl_linux(self):
        for value in ("wsl", "wsl2", "wsl_linux", "WSL_LINUX"):
            with self.subTest(value=value):
                self.assertEqual(OsTypes.WSL_LINUX, OsTypes.get_enum_from_value(value))

    def test_keeps_existing_linux_and_windows_mappings(self):
        self.assertEqual(OsTypes.LINUX, OsTypes.get_enum_from_value("Linux"))
        self.assertEqual(OsTypes.WINDOWS, OsTypes.get_enum_from_value("Windows"))

    def test_detects_windows(self):
        with patch("platform.system", return_value="Windows"):
            self.assertEqual(OsTypes.WINDOWS, OsTypes.detect_current())

    def test_detects_native_linux_without_wsl_signal(self):
        with patch("platform.system", return_value="Linux"):
            with patch.dict("os.environ", {}, clear=True):
                with patch("pathlib.Path.read_text", return_value="6.8.0-generic"):
                    self.assertEqual(OsTypes.LINUX, OsTypes.detect_current())

    def test_detects_wsl_linux_from_kernel_release(self):
        with patch("platform.system", return_value="Linux"):
            with patch.dict("os.environ", {}, clear=True):
                with patch(
                    "pathlib.Path.read_text",
                    return_value="5.15.167.4-microsoft-standard-WSL2",
                ):
                    self.assertEqual(OsTypes.WSL_LINUX, OsTypes.detect_current())

    def test_detects_wsl_linux_from_environment(self):
        with patch("platform.system", return_value="Linux"):
            with patch.dict("os.environ", {"WSL_DISTRO_NAME": "Ubuntu"}, clear=True):
                self.assertEqual(OsTypes.WSL_LINUX, OsTypes.detect_current())

    def test_wsl_signal_fails_closed_when_kernel_release_is_unreadable(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("pathlib.Path.read_text", side_effect=OSError):
                self.assertFalse(_has_wsl_signal())


if __name__ == "__main__":
    unittest.main()
