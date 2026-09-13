# Remaining Risks — #347 / ARCH-03.04

- The concrete `PreflightService` remains intentionally broad; decomposition
  of individual probe categories is outside this issue.
- Live Incus, Docker Swarm, compose, host bridge, browser, and external service
  verification were not applicable and were not claimed.
- Existing legacy installer preflight helpers remain compatibility surface for
  the separate installer decomposition work.
