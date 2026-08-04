import hashlib
import json
import socket
import tempfile
import unittest
import urllib.error
from pathlib import Path

from tiny_swarm_world.domain.preflight import ArtifactSourceStatus
from tiny_swarm_world.infrastructure.adapters.preflight import HttpArtifactSourceReadiness


class _Response:
    def __init__(self, status: int = 200) -> None:
        self.status = status

    def close(self) -> None:
        pass


class TestArtifactSourceReadiness(unittest.TestCase):
    def test_rejects_invalid_mode_and_timeout(self):
        with self.assertRaises(ValueError):
            HttpArtifactSourceReadiness(environment={"TSW_ARTIFACT_SOURCE_MODE": "unknown"})
        with self.assertRaises(ValueError):
            HttpArtifactSourceReadiness(
                environment={"TSW_ARTIFACT_SOURCE_MODE": "direct-internet"},
                timeout_seconds=0,
            )

    def test_direct_mode_requires_registry_apt_and_gpg_sources(self):
        calls: list[str] = []

        def opener(url: str, *, timeout: float):
            calls.append(url)
            return _Response()

        result = HttpArtifactSourceReadiness(
            environment={"TSW_ARTIFACT_SOURCE_MODE": "direct-internet"},
            opener=opener,
            timeout_seconds=2,
        ).check()

        self.assertTrue(result.ready)
        self.assertEqual("direct-internet", result.selected_source)
        self.assertEqual(4, len(calls))
        self.assertEqual(
            {"docker-registry", "ubuntu-apt", "docker-apt", "docker-apt-gpg"},
            {attempt.kind for attempt in result.attempts},
        )

    def test_timeout_is_structured_and_does_not_fall_through_as_success(self):
        def opener(url: str, *, timeout: float):
            raise socket.timeout()

        result = HttpArtifactSourceReadiness(
            environment={"TSW_ARTIFACT_SOURCE_MODE": "direct-internet"},
            opener=opener,
            timeout_seconds=1,
        ).check()

        self.assertFalse(result.ready)
        self.assertTrue(result.timed_out)
        self.assertTrue(all(attempt.status is ArtifactSourceStatus.TIMED_OUT for attempt in result.attempts))

    def test_offline_mode_requires_a_manifest(self):
        result = HttpArtifactSourceReadiness(
            environment={"TSW_ARTIFACT_SOURCE_MODE": "offline"},
        ).check()

        self.assertFalse(result.ready)
        self.assertIsNone(result.selected_source)
        self.assertEqual("FAILED", result.to_dict()["status"])
        self.assertIn("manifest", result.attempts[0].detail)

    def test_offline_mode_verifies_manifest_artifact_checksum(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "docker-images.tar"
            artifact.write_bytes(b"prepared-image-cache")
            manifest = root / "offline.json"
            manifest.write_text(
                json.dumps(
                    {
                        "contract_version": 1,
                        "artifacts": [
                            {
                                "id": "docker-images",
                                "path": artifact.name,
                                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = HttpArtifactSourceReadiness(
                environment={
                    "TSW_ARTIFACT_SOURCE_MODE": "offline",
                    "TSW_OFFLINE_ARTIFACT_MANIFEST": str(manifest),
                },
            ).check()

        self.assertTrue(result.ready)
        self.assertEqual("offline", result.selected_source)
        self.assertEqual("READY", result.to_dict()["status"])

    def test_offline_mode_rejects_checksum_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "package-cache.tar"
            artifact.write_bytes(b"actual")
            manifest = root / "offline.json"
            manifest.write_text(
                json.dumps(
                    {
                        "contract_version": 1,
                        "artifacts": [
                            {
                                "id": "package-cache",
                                "path": artifact.name,
                                "sha256": "0" * 64,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = HttpArtifactSourceReadiness(
                environment={
                    "TSW_ARTIFACT_SOURCE_MODE": "offline",
                    "TSW_OFFLINE_ARTIFACT_MANIFEST": str(manifest),
                },
            ).check()

        self.assertFalse(result.ready)
        self.assertIn("checksum mismatch", result.attempts[0].detail)

    def test_fallback_uses_direct_sources_when_nexus_group_fails(self):
        def opener(url: str, *, timeout: float):
            if "registry.internal" in url:
                return _Response(503)
            return _Response(200)

        result = HttpArtifactSourceReadiness(
            environment={
                "TSW_ARTIFACT_SOURCE_MODE": "fallback",
                "TSW_LXC_DOCKER_REGISTRY_MIRROR": "https://registry.internal:5001",
            },
            opener=opener,
            timeout_seconds=1,
        ).check()

        self.assertTrue(result.ready)
        self.assertEqual("direct-internet", result.selected_source)
        self.assertEqual(4, len(result.attempts))

    def test_probe_supports_getcode_and_classifies_http_errors(self):
        class CodeResponse:
            def getcode(self):
                return 204

            def close(self):
                pass

        calls = iter(
            (
                urllib.error.HTTPError("url", 401, "challenge", {}, None),
                CodeResponse(),
                urllib.error.HTTPError("url", 500, "server", {}, None),
                OSError("unreachable"),
            )
        )

        def opener(url: str, *, timeout: float):
            response = next(calls)
            if isinstance(response, BaseException):
                raise response
            return response

        result = HttpArtifactSourceReadiness(
            environment={
                "TSW_ARTIFACT_SOURCE_MODE": "nexus",
                "TSW_LXC_DOCKER_REGISTRY_MIRROR": "https://registry.internal:5001",
            },
            opener=opener,
            timeout_seconds=1,
        ).check()

        self.assertFalse(result.ready)
        self.assertEqual(
            [ArtifactSourceStatus.READY, ArtifactSourceStatus.READY,
             ArtifactSourceStatus.FAILED, ArtifactSourceStatus.FAILED],
            [attempt.status for attempt in result.attempts],
        )

    def test_offline_mode_rejects_invalid_manifests_and_artifacts(self):
        cases = (
            {"contract_version": 2, "artifacts": []},
            {"contract_version": 1, "artifacts": []},
            {"contract_version": 1, "artifacts": ["invalid"]},
            {"contract_version": 1, "artifacts": [{"id": "x", "path": "x", "sha256": "bad"}]},
            {"contract_version": 1, "artifacts": [{"id": "x", "path": "missing", "sha256": "0" * 64}]},
        )
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "offline.json"
            for payload in cases:
                manifest.write_text(json.dumps(payload), encoding="utf-8")
                result = HttpArtifactSourceReadiness(
                    environment={
                        "TSW_ARTIFACT_SOURCE_MODE": "offline",
                        "TSW_OFFLINE_ARTIFACT_MANIFEST": str(manifest),
                    },
                ).check()
                self.assertFalse(result.ready)
