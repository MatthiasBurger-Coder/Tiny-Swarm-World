from __future__ import annotations

import json
import os
import stat
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tiny_swarm_world.application.ports.repositories.port_routing_evidence_repository import (
    EffectiveAccessModelEvidence,
)
from tiny_swarm_world.infrastructure.adapters.repositories import (
    routing_evidence_local_repository as repository_module,
)
from tiny_swarm_world.infrastructure.adapters.repositories.routing_evidence_local_repository import (
    RoutingEvidenceLocalRepository,
)


class TestRoutingEvidenceLocalRepository(unittest.TestCase):
    def test_creates_parent_and_atomically_writes_private_json(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            repository = RoutingEvidenceLocalRepository(root=root)

            repository.write_effective_access_model(_evidence())

            expected_path = (
                root
                / ".tiny-swarm-world"
                / "evidence"
                / "solid-typed-evidence"
                / "routing"
                / "effective-access-model.json"
            )
            self.assertEqual(expected_path.resolve(), repository.path)
            self.assertEqual(
                json.loads(expected_path.read_text(encoding="utf-8"))["evidence_kind"],
                "effective_access_model",
            )
            self.assertTrue(expected_path.read_text(encoding="utf-8").endswith("\n"))
            if os.name != "nt":
                self.assertEqual(stat.S_IMODE(expected_path.stat().st_mode), 0o600)
            self.assertEqual(list(expected_path.parent.glob(".*.tmp")), [])

    def test_replace_failure_preserves_old_target_and_cleans_temporary_file(self):
        with TemporaryDirectory() as temporary_directory:
            repository = RoutingEvidenceLocalRepository(root=Path(temporary_directory))
            repository.path.parent.mkdir(parents=True)
            repository.path.write_text("previous-complete-evidence\n", encoding="utf-8")
            replace_arguments: list[tuple[Path, Path]] = []

            def fail_replace(source: Path, destination: Path) -> None:
                replace_arguments.append((Path(source), Path(destination)))
                raise OSError("replacement failed")

            with patch.object(repository_module.os, "replace", side_effect=fail_replace):
                with self.assertRaisesRegex(OSError, "replacement failed"):
                    repository.write_effective_access_model(_evidence())

            self.assertEqual(
                repository.path.read_text(encoding="utf-8"),
                "previous-complete-evidence\n",
            )
            self.assertEqual(len(replace_arguments), 1)
            source, destination = replace_arguments[0]
            self.assertEqual(repository.path.parent, source.parent)
            self.assertEqual(repository.path, destination)
            self.assertFalse(source.exists())
            self.assertEqual(list(repository.path.parent.glob(".*.tmp")), [])

    def test_default_product_evidence_tree_is_git_ignored(self):
        repository_root = Path(__file__).resolve().parents[4]
        ignored_patterns = {
            line.strip()
            for line in (repository_root / ".gitignore").read_text(encoding="utf-8").splitlines()
        }
        repository = RoutingEvidenceLocalRepository(root=repository_root)

        self.assertEqual(repository.path.relative_to(repository_root).parts[0], ".tiny-swarm-world")
        self.assertIn("/.tiny-swarm-world/", ignored_patterns)


def _evidence() -> EffectiveAccessModelEvidence:
    return EffectiveAccessModelEvidence(
        evidence_kind="effective_access_model",
        generated_at="2026-07-11T12:30:45Z",
        service_profile="service-access",
        public_ports=(80, 443),
        gateway_public_ingress_ports=(80, 443),
        diagnostic_fallback_ports=(),
        service_access_preferred_url_source="traefik_host_route",
        routes=(),
        health_check_targets=(),
        service_access_links=(),
        skipped_routes=(),
        result="generated",
    )
