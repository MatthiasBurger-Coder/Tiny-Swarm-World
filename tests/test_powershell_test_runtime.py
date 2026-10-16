"""Keep test launches deterministic without changing machine execution policy."""
import base64
import unittest

from tests.powershell_test_runtime import powershell_command, powershell_script_command


def decoded(command):
    return base64.b64decode(command[-1]).decode("utf-16-le")


class PowerShellTestRuntimeTests(unittest.TestCase):
    def test_windows_uses_own_modules_utf8_and_process_only_policy(self):
        command = powershell_command("powershell.exe", "Get-FileHash 'fixture'")
        self.assertEqual(command[1:-1], ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-EncodedCommand"])
        script = decoded(command)
        self.assertIn("(Join-Path $PSHOME 'Modules')", script)
        self.assertIn("UTF8Encoding($false)", script)
        self.assertNotIn("Set-ExecutionPolicy", script)
        self.assertTrue(script.endswith("Get-FileHash 'fixture'"))

    def test_linux_runtime_keeps_its_module_search_path(self):
        self.assertNotIn("PSModulePath", decoded(powershell_command("/usr/bin/pwsh", "Get-Date")))

    def test_paths_and_arguments_remain_literals(self):
        command = powershell_script_command("powershell.exe", "C:/O'Brien/test.ps1", {"RepositoryRoot": "C:/a; $(Get-Date)"})
        self.assertTrue(decoded(command).endswith("& 'C:/O''Brien/test.ps1' -RepositoryRoot 'C:/a; $(Get-Date)'"))

    def test_parameter_names_cannot_inject_commands(self):
        with self.assertRaises(ValueError):
            powershell_script_command("powershell.exe", "test.ps1", {"Root; exit": "value"})
