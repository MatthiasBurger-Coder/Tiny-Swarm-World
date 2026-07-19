"""Expose the static browser E2E contract to default unittest discovery."""

import unittest

from tests.live.browser_e2e_contract import BrowserRouteE2EContractStaticTest


class BrowserRouteE2EContractDiscoveryTest(unittest.TestCase):
    def test_static_browser_e2e_contract_exposes_unittest_cases(self) -> None:
        loader = unittest.defaultTestLoader

        discovered = loader.getTestCaseNames(BrowserRouteE2EContractStaticTest)

        self.assertGreater(len(discovered), 0)


__all__ = ["BrowserRouteE2EContractStaticTest"]
