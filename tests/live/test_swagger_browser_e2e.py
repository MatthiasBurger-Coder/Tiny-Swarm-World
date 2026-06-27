import unittest

from tests.live.browser_e2e_contract import BrowserRouteE2EContract


class TestSwaggerBrowserE2E(BrowserRouteE2EContract):
    route_name = "swagger"


if __name__ == "__main__":
    unittest.main()
