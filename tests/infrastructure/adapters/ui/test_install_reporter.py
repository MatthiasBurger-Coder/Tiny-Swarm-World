import unittest
from pathlib import Path

from tiny_swarm_world.domain.install import InstallEvent, InstallStatus
from tiny_swarm_world.infrastructure.adapters.ui.install_reporter import (
    render_install_event,
)


class TestInstallReporter(unittest.TestCase):
    def test_failure_renderer_keeps_evidence_and_hides_structured_reason_dump(self):
        event = InstallEvent(
            event_type="STEP_FAILED",
            status=InstallStatus.FAILED,
            step="live setup",
            reason='{"secret":"must remain in the log"}',
            evidence_path=Path(".tiny-swarm-world/evidence/setup.log"),
        )

        rendered = "\n".join(render_install_event(event))

        self.assertIn("FAILED live setup", rendered)
        self.assertIn("structured event details recorded in evidence", rendered)
        self.assertIn(".tiny-swarm-world/evidence/setup.log", rendered)
        self.assertNotIn('{"secret":"must remain in the log"}', rendered)


if __name__ == "__main__":
    unittest.main()

