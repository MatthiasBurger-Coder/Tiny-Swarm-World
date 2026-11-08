import unittest
from unittest.mock import AsyncMock, Mock

from tiny_swarm_world.application.services.platform.host.prepare_with_preflight import (
    PrepareHostWithPreflight,
)
from tiny_swarm_world.domain.preflight import LiveConsent


class PrepareHostWithPreflightTest(unittest.IsolatedAsyncioTestCase):
    async def test_failed_preflight_never_resolves_mutating_adapter(self) -> None:
        preflight = Mock(run=AsyncMock(return_value=Mock(passed=False)))
        create_preparation = Mock()

        outcome = await PrepareHostWithPreflight(preflight, create_preparation).run(
            "prepare", LiveConsent(live_flag=True, confirmed=True)
        )

        self.assertIsNone(outcome.preparation)
        create_preparation.assert_not_called()

    async def test_each_action_runs_once_after_passed_preflight(self) -> None:
        for action in ("prepare", "cleanup"):
            with self.subTest(action=action):
                preflight = Mock(run=AsyncMock(return_value=Mock(passed=True)))
                preparation = Mock()
                create_preparation = Mock(return_value=preparation)
                consent = LiveConsent(live_flag=True, confirmed=True)

                outcome = await PrepareHostWithPreflight(preflight, create_preparation).run(
                    action, consent
                )

                preflight.run.assert_awaited_once_with(consent)
                create_preparation.assert_called_once_with()
                getattr(preparation, action).assert_called_once_with()
                self.assertIs(outcome.preparation, getattr(preparation, action).return_value)
