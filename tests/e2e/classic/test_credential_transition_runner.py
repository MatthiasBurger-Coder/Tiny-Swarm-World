"""Safety checks for the explicitly opt-in credential transition runner."""
import copy
import json
import unittest
from typing import Any
from unittest.mock import Mock

import requests

from tests.e2e.classic.run_credential_transition_live import (
    comparable,
    deployment_source,
    login_cookie_session,
    require_persistent_jenkins_home,
)


class CredentialTransitionRunnerTest(unittest.TestCase):
    def test_cookie_login_submits_same_session_crumb_and_explicit_credentials(self) -> None:
        session = Mock(spec=requests.Session)
        session.get.return_value.text = """
            <form action="/unrelated"><input type="hidden" name="Jenkins-Crumb" value="wrong"></form>
            <form action="j_spring_security_check" method="post">
              <input name="Jenkins-Crumb" value="crumb&amp;&quot;&#39;" type="hidden">
              <input type="hidden" name="from" value="/untrusted">
              <input type="hidden" name="j_username" value="page-user">
              <input type="hidden" name="j_password" value="page-password">
              <input type="text" name="other" value="ignored">
            </form>
            <input type="hidden" name="Jenkins-Crumb" value="outside">
        """

        def accept_login(url: str, *, data: dict[str, str], timeout: int) -> Mock:
            self.assertEqual(data.get("Jenkins-Crumb"), 'crumb&"\'')
            self.assertEqual(data.get("j_username"), "admin")
            self.assertEqual(data.get("j_password"), "provided<&password>")
            self.assertEqual(data.get("from"), "/")
            self.assertEqual(data.get("Submit"), "Sign in")
            self.assertNotIn("other", data)
            return Mock()

        session.post.side_effect = accept_login
        login_cookie_session(session, "provided<&password>")
        session.get.assert_called_once_with("http://localhost:11080/login", timeout=15)
        session.get.return_value.raise_for_status.assert_called_once_with()
        self.assertEqual(session.post.call_count, 1)
        self.assertEqual(session.post.call_args.args, ("http://localhost:11080/j_spring_security_check",))
        self.assertEqual(session.post.call_args.kwargs["timeout"], 20)

    def test_cookie_login_rejects_missing_local_login_form_without_posting(self) -> None:
        for page in ("<html>unavailable</html>",
                     '<form action="https://other.invalid/j_spring_security_check">'
                     '<input type="hidden" name="Jenkins-Crumb" value="foreign"></form>'):
            with self.subTest(page=page):
                session = Mock(spec=requests.Session)
                session.get.return_value.text = page
                with self.assertRaisesRegex(RuntimeError, "login_form_missing"):
                    login_cookie_session(session, "provided-password")
                session.post.assert_not_called()

    def test_source_evidence_requires_verified_unique_jenkins_result(self) -> None:
        entry = {"target_id": "deployment:jenkins-stack", "status": "verified",
                 "evidence": {"resolved_sources": "vault"}}
        self.assertEqual(deployment_source(json.dumps({"verification_results": [entry]}).encode()), "vault")
        for entries in ([{**entry, "status": "failed"}], [entry, entry],
                        [{**entry, "target_id": "deployment:other-stack"}],
                        [{**entry, "evidence": {"resolved_sources": "untrusted-value"}}]):
            with self.subTest(entries=entries):
                self.assertIsNone(deployment_source(json.dumps({"verification_results": entries}).encode()))
        self.assertIsNone(deployment_source(b"not-json"))

    def test_unmigrated_jenkins_home_is_rejected(self) -> None:
        snapshot: dict[str, Any] = {"jenkins_jenkins": {"TaskTemplate": {"ContainerSpec": {"Mounts": [
            {"Type": "volume", "Source": "jenkins_jenkins_home", "Target": "/var/lib/jenkins"},
        ]}}}}
        with self.assertRaisesRegex(RuntimeError, "jenkins_home_migration_required"):
            require_persistent_jenkins_home(snapshot)

    def test_named_volume_at_actual_home_is_accepted(self) -> None:
        require_persistent_jenkins_home({"jenkins_jenkins": {"TaskTemplate": {"ContainerSpec": {"Mounts": [
            {"Type": "volume", "Source": "jenkins_jenkins_home", "Target": "/var/jenkins_home"},
        ]}}}})

    def test_restart_comparison_preserves_unrelated_drift_and_input(self) -> None:
        snapshot: dict[str, Any] = {
            "jenkins_jenkins": {"TaskTemplate": {"ForceUpdate": 1, "ContainerSpec": {"Env": ["NAME=value"]}}},
            "other": {"TaskTemplate": {"ForceUpdate": 2}},
        }
        original = copy.deepcopy(snapshot)
        result = comparable(snapshot)
        self.assertEqual(snapshot, original)
        self.assertNotIn("ForceUpdate", result["jenkins_jenkins"]["TaskTemplate"])
        self.assertEqual(result["other"], original["other"])
        self.assertEqual(result["jenkins_jenkins"]["TaskTemplate"]["ContainerSpec"],
                         original["jenkins_jenkins"]["TaskTemplate"]["ContainerSpec"])
