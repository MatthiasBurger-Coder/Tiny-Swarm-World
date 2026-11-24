from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from tiny_swarm_world.application.ports.lifecycle import ManifestSnapshot
from tiny_swarm_world.domain.ingress.desired_state import DesiredHttpsRoute, DesiredHttpsIngress
from tiny_swarm_world.infrastructure.adapters.installation import guided_report


class GuidedServiceReportTests(unittest.TestCase):
    def test_reports_observed_health_and_access_for_committed_selection_only(self) -> None:
        manifest = Mock(host="native-linux", service_preset="service-access",
                        resolved_services=("incus", "portainer", "jenkins", "pulsar"))
        manifest.effective_exposure.return_value = {}
        routes = (
            DesiredHttpsRoute("portainer", "portainer.tsw.local", "portainer", 9000,
                              health_check_url="https://portainer.tsw.local/api/status"),
            DesiredHttpsRoute("jenkins", "jenkins.tsw.local", "jenkins", 8080),
            DesiredHttpsRoute("pulsar-manager", "pulsar.tsw.local", "pulsar-manager", 80),
        )
        model = Mock(spec=DesiredHttpsIngress, routes=routes, direct_endpoints=(), skipped_routes=(),
                     diagnostic_fallback_ports=(), public_ports=(443,),
                     service_access_preferred_url_source="configured")
        store = Mock(**{"manifests.load.return_value": ManifestSnapshot(manifest, "fixture")})
        with (
            patch.object(guided_report, "build_installation_lifecycle_service", return_value=store),
            patch.object(guided_report, "ComposeFileRepositoryYaml") as repository,
            patch.object(guided_report, "_http_status", side_effect=(403, 200, 204, None)) as probe,
            redirect_stdout(io.StringIO()) as output,
        ):
            repository.return_value.get_effective_access_model.return_value = model
            self.assertTrue(guided_report.report_service_access("service-access", {}))
        self.assertEqual(repository.call_args.kwargs["resolved_services"], manifest.resolved_services)
        self.assertFalse(repository.call_args.kwargs["write_logs"])
        self.assertEqual(probe.call_args_list, [
            call("https://jenkins.tsw.local"),
            call("https://portainer.tsw.local"),
            call("https://portainer.tsw.local/api/status"),
            call("https://pulsar.tsw.local"),
        ])
        report = output.getvalue()
        self.assertIn("incus: no published URL", report)
        self.assertIn("jenkins: health probe unverified (HTTP 403)", report)
        self.assertIn("authentication or authorization required at https://jenkins.tsw.local", report)
        self.assertIn("portainer: health probe passed (HTTP 204)", report)
        self.assertIn("verified URL https://portainer.tsw.local (HTTP 200)", report)
        self.assertIn("pulsar-manager: health probe unverified (no HTTP response)", report)
        self.assertNotIn("pulsar: no published URL", report)

    def test_profile_mismatch_does_not_probe_or_print_urls(self) -> None:
        manifest = Mock(host="native-linux", service_preset="default")
        store = Mock(**{"manifests.load.return_value": ManifestSnapshot(manifest, "fixture")})
        with (
            patch.object(guided_report, "build_installation_lifecycle_service", return_value=store),
            patch.object(guided_report, "_http_status") as probe,
            redirect_stdout(io.StringIO()) as output,
        ):
            self.assertFalse(guided_report.report_service_access("service-access", {}))
        probe.assert_not_called()
        self.assertIn("committed selection or access model is unavailable", output.getvalue())

    def test_probe_observes_first_response_without_following_redirects(self) -> None:
        with patch.object(guided_report, "HTTPSConnection") as factory:
            connection = factory.return_value
            response = connection.getresponse.return_value
            response.__enter__.return_value = SimpleNamespace(status=302)
            self.assertEqual(guided_report._http_status("https://portainer.tsw.local/api/status"), 302)
            factory.assert_called_once_with("portainer.tsw.local", None, timeout=3)
            connection.request.assert_called_once_with("GET", "/api/status")
            connection.close.assert_called_once()
        self.assertEqual(guided_report._access_label(302), "redirect observed at")

    def test_connection_failure_is_unverified(self) -> None:
        with patch.object(guided_report, "HTTPSConnection") as factory:
            factory.return_value.request.side_effect = OSError("private diagnostic")
            self.assertIsNone(guided_report._http_status("https://portainer.tsw.local"))
            factory.return_value.close.assert_called_once()
