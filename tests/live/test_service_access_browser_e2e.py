import unittest

from tests.live.browser_e2e_contract import BrowserRouteE2EContract


class TestServiceAccessBrowserE2E(BrowserRouteE2EContract):
    route_name = "service-access"


if __name__ == "__main__":
    unittest.main()
