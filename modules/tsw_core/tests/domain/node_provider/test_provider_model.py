import unittest

from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    ManagedLxcBackendSelection,
    ManagedLxcBackendSelectionStatus,
    NodeProviderKind,
    NodeRole,
    NodeSpec,
    ProviderReadiness,
    ProviderReadinessStatus,
    ProviderSelection,
    ProviderSelectionStatus,
)


class TestProviderModel(unittest.TestCase):
    def test_provider_kind_values_match_provider_adr(self):
        self.assertEqual(NodeProviderKind.LXC_NATIVE.value, "lxc_native")
        self.assertEqual(NodeProviderKind.UNSUPPORTED.value, "unsupported")

    def test_readiness_status_values_cover_provider_preflight_failures(self):
        self.assertEqual(ProviderReadinessStatus.READY.value, "ready")
        self.assertEqual(ProviderReadinessStatus.BACKEND_MISSING.value, "backend_missing")
        self.assertEqual(ProviderReadinessStatus.BACKEND_AMBIGUOUS.value, "backend_ambiguous")
        self.assertEqual(ProviderReadinessStatus.EXECUTABLE_MISSING.value, "executable_missing")
        self.assertEqual(ProviderReadinessStatus.DAEMON_UNAVAILABLE.value, "daemon_unavailable")
        self.assertEqual(ProviderReadinessStatus.SYSTEMD_UNAVAILABLE.value, "systemd_unavailable")
        self.assertEqual(ProviderReadinessStatus.WSL_UNSUPPORTED.value, "wsl_unsupported")
        self.assertEqual(ProviderReadinessStatus.PROFILE_MISSING.value, "profile_missing")
        self.assertEqual(ProviderReadinessStatus.TIMEOUT.value, "timeout")
        self.assertEqual(ProviderReadinessStatus.UNSUPPORTED.value, "unsupported")

    def test_managed_lxc_backend_selection_distinguishes_incus_and_lxd(self):
        incus = ManagedLxcBackendSelection.for_backend(ManagedLxcBackend.INCUS)
        lxd = ManagedLxcBackendSelection.for_backend(ManagedLxcBackend.LXD)

        self.assertTrue(incus.selected)
        self.assertFalse(incus.blocks_mutation)
        self.assertEqual(ManagedLxcBackend.INCUS, incus.backend)
        self.assertEqual(incus.to_dict()["backend"], "incus")
        self.assertEqual(ManagedLxcBackend.LXD, lxd.backend)

    def test_backend_selection_blocks_missing_ambiguous_and_unsupported_states(self):
        missing = ManagedLxcBackendSelection.missing(
            remediation=("Install and initialize LXD or Incus.",),
        )
        ambiguous = ManagedLxcBackendSelection.ambiguous(
            candidates=(ManagedLxcBackend.INCUS, ManagedLxcBackend.LXD),
            remediation=("Configure the preferred managed LXC backend.",),
        )
        unsupported = ManagedLxcBackendSelection.unsupported(
            remediation=("Use native Linux or a WSL2 host with provider support.",),
        )

        for selection in (missing, ambiguous, unsupported):
            with self.subTest(status=selection.status):
                self.assertFalse(selection.selected)
                self.assertTrue(selection.blocks_mutation)
                self.assertIsNone(selection.backend)

        self.assertEqual(ManagedLxcBackendSelectionStatus.MISSING, missing.status)
        self.assertEqual(
            ManagedLxcBackendSelectionStatus.AMBIGUOUS,
            ambiguous.status,
        )
        self.assertEqual(
            list(ambiguous.candidates),
            [ManagedLxcBackend.INCUS, ManagedLxcBackend.LXD],
        )
        self.assertEqual(
            ManagedLxcBackendSelectionStatus.UNSUPPORTED,
            unsupported.status,
        )

    def test_backend_selection_rejects_inconsistent_states(self):
        with self.assertRaises(ValueError):
            ManagedLxcBackendSelection(
                status=ManagedLxcBackendSelectionStatus.SELECTED,
            )

        with self.assertRaises(ValueError):
            ManagedLxcBackendSelection(
                status=ManagedLxcBackendSelectionStatus.AMBIGUOUS,
                candidates=(ManagedLxcBackend.INCUS,),
            )

        with self.assertRaises(ValueError):
            ManagedLxcBackendSelection(
                status=ManagedLxcBackendSelectionStatus.MISSING,
                backend=ManagedLxcBackend.LXD,
            )

    def test_lxc_native_readiness_requires_selected_backend(self):
        readiness = ProviderReadiness(
            provider=NodeProviderKind.LXC_NATIVE,
            status=ProviderReadinessStatus.READY,
            backend_selection=ManagedLxcBackendSelection.for_backend(
                ManagedLxcBackend.INCUS,
            ),
            evidence={"classification": "usable"},
        )

        self.assertTrue(readiness.ready)
        self.assertFalse(readiness.blocks_mutation)
        self.assertEqual(readiness.to_dict()["provider"], "lxc_native")
        self.assertEqual(readiness.to_dict()["backend_selection"]["backend"], "incus")

        with self.assertRaises(ValueError):
            ProviderReadiness(
                provider=NodeProviderKind.LXC_NATIVE,
                status=ProviderReadinessStatus.READY,
                backend_selection=ManagedLxcBackendSelection.missing(),
            )

    def test_lxc_native_readiness_rejects_contradictory_backend_state(self):
        with self.assertRaises(ValueError):
            ProviderReadiness(
                provider=NodeProviderKind.LXC_NATIVE,
                status=ProviderReadinessStatus.BACKEND_MISSING,
                backend_selection=ManagedLxcBackendSelection.for_backend(
                    ManagedLxcBackend.INCUS,
                ),
            )

        readiness = ProviderReadiness(
            provider=NodeProviderKind.LXC_NATIVE,
            status=ProviderReadinessStatus.PERMISSION_DENIED,
            backend_selection=ManagedLxcBackendSelection.for_backend(
                ManagedLxcBackend.LXD,
            ),
            remediation=("Review local LXD permissions.",),
        )

        self.assertTrue(readiness.blocks_mutation)

    def test_lxc_native_readiness_classifies_backend_failures(self):
        cases = (
            (
                ProviderReadinessStatus.BACKEND_MISSING,
                ManagedLxcBackendSelection.missing(
                    remediation=("Install LXD or Incus.",),
                ),
            ),
            (
                ProviderReadinessStatus.BACKEND_AMBIGUOUS,
                ManagedLxcBackendSelection.ambiguous(
                    candidates=(ManagedLxcBackend.INCUS, ManagedLxcBackend.LXD),
                    remediation=("Choose one backend.",),
                ),
            ),
            (
                ProviderReadinessStatus.BACKEND_UNSUPPORTED,
                ManagedLxcBackendSelection.unsupported(
                    remediation=("Use native Linux or supported WSL2.",),
                ),
            ),
        )

        for status, backend_selection in cases:
            with self.subTest(status=status):
                readiness = ProviderReadiness(
                    provider=NodeProviderKind.LXC_NATIVE,
                    status=status,
                    backend_selection=backend_selection,
                )

                self.assertFalse(readiness.ready)
                self.assertTrue(readiness.blocks_mutation)

    def test_lxc_native_failure_classification_blocks_without_fallback(self):
        selection = ProviderSelection.from_lxc_backend_selection(
            ManagedLxcBackendSelection.ambiguous(
                candidates=(ManagedLxcBackend.INCUS, ManagedLxcBackend.LXD),
                remediation=("Set node provider backend explicitly.",),
            ),
        )

        self.assertEqual(NodeProviderKind.LXC_NATIVE, selection.requested_provider)
        self.assertEqual(NodeProviderKind.LXC_NATIVE, selection.selected_provider)
        self.assertEqual(ProviderSelectionStatus.BLOCKED, selection.status)
        self.assertTrue(selection.blocks_mutation)
        self.assertFalse(selection.selected)

        with self.assertRaises(ValueError):
            ProviderSelection(
                requested_provider=NodeProviderKind.LXC_NATIVE,
                selected_provider=NodeProviderKind.LXC_NATIVE,
                status=ProviderSelectionStatus.SELECTED,
                backend_selection=ManagedLxcBackendSelection.missing(),
            )

    def test_unsupported_provider_selection_blocks_mutation(self):
        selection = ProviderSelection(
            requested_provider=NodeProviderKind.UNSUPPORTED,
            selected_provider=NodeProviderKind.UNSUPPORTED,
            status=ProviderSelectionStatus.UNSUPPORTED,
            remediation=("No supported provider is available.",),
        )

        self.assertFalse(selection.selected)
        self.assertTrue(selection.blocks_mutation)
        self.assertEqual(selection.to_dict()["status"], "unsupported")

    def test_provider_selection_rejects_requested_selected_mismatch(self):
        cases = (
            (
                NodeProviderKind.UNSUPPORTED,
                NodeProviderKind.LXC_NATIVE,
                ProviderSelectionStatus.UNSUPPORTED,
            ),
        )

        for requested_provider, selected_provider, status in cases:
            with self.subTest(requested_provider=requested_provider):
                with self.assertRaises(ValueError):
                    ProviderSelection(
                        requested_provider=requested_provider,
                        selected_provider=selected_provider,
                        status=status,
                    )

    def test_node_spec_captures_role_provider_and_optional_backend(self):
        spec = NodeSpec(
            name="tsw-manager-1",
            role=NodeRole.MANAGER,
            provider=NodeProviderKind.LXC_NATIVE,
            backend=ManagedLxcBackend.LXD,
        )

        self.assertEqual(spec.to_dict()["role"], "manager")
        self.assertEqual(spec.to_dict()["provider"], "lxc_native")
        self.assertEqual(spec.to_dict()["backend"], "lxd")

    def test_node_spec_rejects_invalid_names_and_unsupported_backend_pairings(self):
        with self.assertRaises(ValueError):
            NodeSpec(
                name="Manager One",
                role=NodeRole.MANAGER,
                provider=NodeProviderKind.LXC_NATIVE,
            )

        with self.assertRaises(ValueError):
            NodeSpec(
                name="unsupported-node",
                role=NodeRole.WORKER,
                provider=NodeProviderKind.UNSUPPORTED,
            )

    def test_provider_readiness_rejects_unsafe_evidence(self):
        with self.assertRaises(ValueError):
            ProviderReadiness(
                provider=NodeProviderKind.UNSUPPORTED,
                status=ProviderReadinessStatus.HOST_UNSUPPORTED,
                evidence={"raw_stdout": "lxc list"},
            )


if __name__ == "__main__":
    unittest.main()
