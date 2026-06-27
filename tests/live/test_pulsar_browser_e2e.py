import unittest

from tests.live.browser_e2e_contract import BrowserRouteE2EContract


class TestPulsarManagerBrowserE2E(BrowserRouteE2EContract, unittest.TestCase):
    route_name = "pulsar-manager"


class TestPulsarAdminApiBrowserE2E(BrowserRouteE2EContract, unittest.TestCase):
    route_name = "pulsar-admin-api"


if __name__ == "__main__":
    unittest.main()
