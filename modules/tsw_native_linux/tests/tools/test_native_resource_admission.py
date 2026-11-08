"""The native qualification scenario requires the actual approved override."""
from __future__ import annotations

from dataclasses import replace
import unittest

from modules.tsw_native_linux.tools.qualification import native_resource_admission as admission
from tiny_swarm_world.domain.native_preparation import NativeHostFacts, qualification_failures


class NativeResourceAdmissionTests(unittest.TestCase):
    @staticmethod
    def document() -> bytes:
        return b'''nodes:
  - name: swarm-manager
    resources: {cpu: "2", memory: 10GiB, disk: 20GiB}
  - name: swarm-worker-1
    resources: {cpu: "2", memory: 6GiB, disk: 50GiB}
  - name: swarm-worker-2
    resources: {cpu: "4", memory: 1GiB, disk: 10GiB}
'''

    def test_actual_yaml_selection_is_seventeen_gib_without_default_clamping(self) -> None:
        self.assertEqual(admission.selection(self.document()), admission.SELECTION)
        invalid = (self.document().replace(b'6GiB', b'8GiB'),
                   self.document().replace(b'cpu: "4"', b'cpu: 4'),
                   self.document().replace(b'swarm-worker-2', b'foreign'),
                   self.document() + b'nodes: []\n', b'nodes: []\n')
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                admission.selection(raw)
        self.assertEqual(sum(row['memory_bytes'] for row in admission.SELECTION.values()), 17 * admission.GIB)

    def test_product_preflight_still_rejects_active_runtime_and_ports_after_numeric_floors(self) -> None:
        facts = NativeHostFacts(platform='Linux', is_wsl=False, distribution_id='ubuntu', version_id='26.04',
            architecture='x86_64', cpu_count=8, memory_bytes=19 * admission.GIB,
            free_disk_bytes=160 * admission.GIB, can_install_packages=True, repository_writable=True,
            kernel_ready=True, ports_ready=True, conflicting_runtime=False, network_ready=True)
        self.assertEqual(qualification_failures(facts, needs_network=False, needs_ports=True,
                                               needs_privilege=True, service_profile='service-access'), ())
        for changed in (replace(facts, conflicting_runtime=True), replace(facts, ports_ready=False),
                        replace(facts, kernel_ready=False), replace(facts, architecture='unknown')):
            self.assertTrue(qualification_failures(changed, needs_network=False, needs_ports=True,
                                                   needs_privilege=True, service_profile='service-access'))
