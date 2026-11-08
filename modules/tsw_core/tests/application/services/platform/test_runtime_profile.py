import unittest

from tiny_swarm_world.application.services.platform import (
    NodeProviderSelectionRequest,
    ResolvedRuntimeProfile,
    RuntimeProfileResolutionRequest,
    RuntimeProfileResolutionStatus,
    RuntimeProfileResolver,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    NodeProviderKind,
)


class TestRuntimeProfileResolver(unittest.TestCase):
    def setUp(self):
        self.resolver = RuntimeProfileResolver()

    def test_resolves_classic_incus_profile_from_ordered_capabilities(self):
        result = self.resolver.resolve(
            RuntimeProfileResolutionRequest(
                service_profile=ServiceStackProfile.DEFAULT,
                provider_request=NodeProviderSelectionRequest(
                    backend_candidates=(ManagedLxcBackend.LXD, ManagedLxcBackend.INCUS)
                ),
                host_environment=HostEnvironmentKind.WSL2,
                available_backends=(ManagedLxcBackend.INCUS,),
                supported_backends=(ManagedLxcBackend.INCUS,),
            )
        )

        self.assertIsInstance(result, ResolvedRuntimeProfile)
        self.assertEqual(ServiceStackProfile.DEFAULT, result.service_profile)
        self.assertEqual(ManagedLxcBackend.INCUS, result.backend)
        self.assertEqual(HostEnvironmentKind.WSL2, result.host_environment)
        self.assertEqual(RuntimeProfileResolutionStatus.RESOLVED, result.status)

    def test_explicit_unsupported_provider_is_reported_without_backend_fallback(self):
        result = self.resolver.resolve(
            RuntimeProfileResolutionRequest(
                service_profile="service-access",
                provider_request=NodeProviderSelectionRequest(
                    requested_provider=NodeProviderKind.UNSUPPORTED
                ),
            )
        )

        self.assertEqual(RuntimeProfileResolutionStatus.UNSUPPORTED, result.status)
        self.assertIsNone(result.backend)
        self.assertEqual(("Select lxc_native.",), result.remediation)

    def test_missing_capability_is_reported_deterministically(self):
        request = RuntimeProfileResolutionRequest(
            service_profile="default",
            provider_request=NodeProviderSelectionRequest(
                backend_candidates=(ManagedLxcBackend.INCUS,)
            ),
            available_backends=(),
            supported_backends=(ManagedLxcBackend.INCUS,),
        )

        first = self.resolver.resolve(request)
        second = self.resolver.resolve(request)

        self.assertEqual(first, second)
        self.assertEqual(RuntimeProfileResolutionStatus.UNAVAILABLE, first.status)
        self.assertIsNone(first.backend)

    def test_preferred_backend_is_canonical_when_product_supports_it(self):
        result = self.resolver.resolve(
            RuntimeProfileResolutionRequest(
                service_profile=ServiceStackProfile.DEFAULT,
                provider_request=NodeProviderSelectionRequest(
                    preferred_backend=ManagedLxcBackend.INCUS
                ),
                supported_backends=(ManagedLxcBackend.INCUS,),
            )
        )

        self.assertEqual(RuntimeProfileResolutionStatus.RESOLVED, result.status)
        self.assertEqual(ManagedLxcBackend.INCUS, result.backend)


if __name__ == "__main__":
    unittest.main()
