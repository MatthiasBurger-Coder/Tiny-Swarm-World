import unittest

from modules.tsw_core.tests.e2e.classic.browser_e2e_contract import BrowserRouteE2EContract


class TestJenkinsBrowserE2E(BrowserRouteE2EContract, unittest.TestCase):
    route_name = "jenkins"


if __name__ == "__main__":
    unittest.main()
