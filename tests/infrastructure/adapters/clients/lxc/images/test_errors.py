import subprocess
import unittest

from tiny_swarm_world.infrastructure.adapters.clients.lxc.images.errors import (
    REGISTRY_RATE_LIMITED_OPERATOR_ACTION,
    ImagePublisherOperationRejected,
    PublicImagePullRejected,
    docker_hub_rate_limited,
    image_operation_failure_diagnostic,
    image_operation_operator_action,
)


def completed(*, stdout: str = "", stderr: str = "", returncode: int = 1):
    return subprocess.CompletedProcess([], returncode, stdout=stdout, stderr=stderr)


class TestImagePublisherErrors(unittest.TestCase):
    def test_error_types_keep_diagnostics_without_secrets_in_messages(self):
        public_error = PublicImagePullRejected(
            "redis:7",
            diagnostic="registry_rate_limited",
            operator_action="authenticate",
        )
        operation_error = ImagePublisherOperationRejected(
            operation="push_image",
            diagnostic="registry_unreachable",
            operator_action="check registry",
            exit_code=17,
        )

        self.assertEqual(str(public_error), "Public container image pull failed for redis:7.")
        self.assertEqual(public_error.diagnostic, "registry_rate_limited")
        self.assertEqual(operation_error.exit_code, 17)
        self.assertIn("Exit code: 17", str(operation_error))

    def test_rate_limit_detection_handles_stdout_and_negative_case(self):
        self.assertTrue(docker_hub_rate_limited(completed(stdout="Too Many Requests")))
        self.assertTrue(docker_hub_rate_limited(completed(stderr="pull rate limit reached")))
        self.assertFalse(docker_hub_rate_limited(completed(stderr="connection refused")))

    def test_failure_diagnostic_classifies_all_operation_failures(self):
        cases = (
            ("pull_public_image", "pull rate limit", "registry_rate_limited"),
            ("registry_login", "connection refused", "registry_unreachable"),
            ("push_image", "no route to host", "registry_unreachable"),
            ("pull_public_image", "connection refused", "network_unreachable"),
            ("pull_public_image", "authentication required", "registry_authentication_failed"),
            ("pull_public_image", "no space left on device", "manager_storage_exhausted"),
            ("build_image", "generic failure", "image_build_failed"),
            ("push_image", "generic failure", "registry_push_failed"),
            ("registry_login", "generic failure", "registry_login_failed"),
            ("verify_image_pull", "generic failure", "manager_image_operation_failed"),
        )

        for operation, output, expected in cases:
            with self.subTest(operation=operation, output=output):
                self.assertEqual(
                    image_operation_failure_diagnostic(
                        operation,
                        completed(stderr=output),
                    ),
                    expected,
                )

    def test_operator_action_covers_diagnostics_and_operation_fallbacks(self):
        self.assertEqual(
            image_operation_operator_action(
                "pull_public_image", completed(stderr="pull rate limit")
            ),
            REGISTRY_RATE_LIMITED_OPERATOR_ACTION,
        )
        self.assertIn(
            "127.0.0.1:13500",
            image_operation_operator_action(
                "push_image", completed(stderr="connection refused")
            ),
        )
        self.assertIn(
            "TSW_NEXUS_ADMIN_PASSWORD",
            image_operation_operator_action(
                "registry_login", completed(stderr="unauthorized")
            ),
        )
        self.assertIn(
            "Free storage",
            image_operation_operator_action(
                "pull_public_image", completed(stderr="no space left on device")
            ),
        )
        self.assertIn(
            "build prerequisites",
            image_operation_operator_action(
                "build_image", completed(stderr="generic failure")
            ),
        )
        self.assertIn(
            "local registry service",
            image_operation_operator_action(
                "push_image", completed(stderr="generic failure")
            ),
        )
        self.assertIn(
            "Docker daemon",
            image_operation_operator_action(
                "verify_image_pull", completed(stderr="generic failure")
            ),
        )
