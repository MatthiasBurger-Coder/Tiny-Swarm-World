"""Tests for the closed, host-independent Incus capability contract."""
from __future__ import annotations

import ast
from enum import Enum
import inspect
import unittest
from unittest.mock import patch

from tiny_swarm_world.domain.lifecycle import incus_capability as capability


class ForeignIntent(Enum):
    LEGACY_CLASSIC = "legacy_classic"
    INSTALLATION_SCOPED = "installation_scoped"


class BrokenString(str):
    def __len__(self) -> int:
        raise ValueError("private")


class SpoofedLength(str):
    def __len__(self) -> int:
        return 1


class IncusCapabilityTests(unittest.TestCase):
    def test_only_explicit_legacy_without_version_has_legacy_classification(self) -> None:
        classify = capability.classify_incus_capability
        self.assertIs(classify(capability.IntentKind.LEGACY_CLASSIC), capability.CapabilityResult.LEGACY_CLASSIC)
        for version in ("6.0.5", "", 0, False, object()):
            with self.subTest(version=version):
                self.assertIs(classify(capability.IntentKind.LEGACY_CLASSIC, version),
                              capability.CapabilityResult.INVALID_INTENT)

    def test_intent_requires_actual_enum_member_without_coercion(self) -> None:
        classify = capability.classify_incus_capability
        for intent in (None, "LEGACY_CLASSIC", "legacy_classic", "INSTALLATION_SCOPED",
                       ForeignIntent.LEGACY_CLASSIC, ForeignIntent.INSTALLATION_SCOPED,
                       True, False, 0, object()):
            with self.subTest(intent=intent):
                self.assertIs(classify(intent), capability.CapabilityResult.INVALID_INTENT)
                self.assertIs(classify(intent, "6.0.5"), capability.CapabilityResult.INVALID_INTENT)

    def test_scoped_invalid_versions_are_rejected_without_parsing_leak(self) -> None:
        classify = capability.classify_incus_capability
        intent = capability.IntentKind.INSTALLATION_SCOPED
        for value in (None, 1, True, object(), "", " ", " 6.0.5", "6.0.5 ", "6.0.5\n",
                      "+6.0.5", "-6.0.5", "06.0.5", "6.00.5", "6.0.05", "6.0",
                      "6.0.5.1", "6.0.5-rc1", "６.0.5", "6.٠.5",
                      "1" * 29 + ".0.0", BrokenString("6.0.5"),
                      SpoofedLength("6.0.5"), SpoofedLength("1" * 29 + ".0.0")):
            with self.subTest(value=value):
                self.assertIs(classify(intent, value), capability.CapabilityResult.INVALID_VERSION)

    def test_scoped_canonical_versions_are_always_unsupported(self) -> None:
        classify = capability.classify_incus_capability
        intent = capability.IntentKind.INSTALLATION_SCOPED
        for value in ("0.0.0", "6.0.5", "1" * 28 + ".0.0"):
            with self.subTest(value=value):
                for _ in range(3):
                    self.assertIs(classify(intent, value), capability.CapabilityResult.UNSUPPORTED)
        self.assertEqual(type(capability.SUPPORTED_VERSIONS), frozenset)
        self.assertEqual(capability.SUPPORTED_VERSIONS, frozenset())
        self.assertFalse(hasattr(capability.SUPPORTED_VERSIONS, "add"))
        self.assertFalse(hasattr(capability, "register"))
        self.assertFalse(hasattr(capability, "register_version"))

    def test_rebinding_registry_cannot_grant_support(self) -> None:
        with patch.object(capability, "SUPPORTED_VERSIONS", frozenset({"6.0.5"})):
            self.assertIs(capability.classify_incus_capability(capability.IntentKind.INSTALLATION_SCOPED, "6.0.5"),
                          capability.CapabilityResult.UNSUPPORTED)

    def test_domain_imports_are_standard_library_only(self) -> None:
        tree = ast.parse(inspect.getsource(capability))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module != "__future__":
                imports.add(node.module or "")
        self.assertEqual(imports, {"enum", "re"})

    def test_classification_performs_no_io_or_host_command(self) -> None:
        with patch("builtins.open", side_effect=AssertionError("filesystem")), \
                patch("os.system", side_effect=AssertionError("command")), \
                patch("subprocess.Popen", side_effect=AssertionError("process")), \
                patch("socket.socket", side_effect=AssertionError("network")):
            self.assertIs(capability.classify_incus_capability(capability.IntentKind.LEGACY_CLASSIC),
                          capability.CapabilityResult.LEGACY_CLASSIC)
            self.assertIs(capability.classify_incus_capability(capability.IntentKind.INSTALLATION_SCOPED, "6.0.5"),
                          capability.CapabilityResult.UNSUPPORTED)


if __name__ == "__main__":
    unittest.main()
