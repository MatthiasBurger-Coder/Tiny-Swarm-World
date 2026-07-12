"""Expose the static browser E2E contract to default unittest discovery."""

from tests.live.browser_e2e_contract import BrowserRouteE2EContractStaticTest


__all__ = ["BrowserRouteE2EContractStaticTest"]
