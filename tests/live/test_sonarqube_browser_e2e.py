import unittest

from tests.live.browser_e2e_contract import BrowserRouteE2EContract


class TestSonarQubeBrowserE2E(BrowserRouteE2EContract, unittest.TestCase):
    route_name = "sonarqube"


if __name__ == "__main__":
    unittest.main()
