# Test Results

## Required static gates

- Lint: PASS
- Architecture lint: PASS, 290 files, 658 dependencies, 3 contracts kept
- Architecture tests: PASS, 18/18
- Typecheck: PASS, 472 files, 0 errors
- Full test gate: PASS, 1410 tests, 28 skipped
- Aggregate quality: PASS, 1410 tests, 28 skipped

## Focused regression tests

- Windows PowerShell 5.1 parser: PASS
- Windows Pester: PASS, 40/40
- Windows bridge Python asset tests: PASS, 11/11
- Provider/inventory/storage/secret tests: PASS, 69/69
- Compose repository tests: PASS, 46/46
- Browser contract static tests: PASS, 17/17
- Skill registry integrity: PASS, 3/3

## Live results

- `install.sh --headless --confirm-reset --non-interactive-live-approval`: PASS; reset exit 0, setup exit 0, all ten phases completed.
- Final deployment apply: PASS in 15.3 seconds with every returned verification result `verified`.
- Final deployment verify: PASS in 5.3 seconds; nine stack readiness targets verified on attempt 1.
- Final platform verify: PASS in 15.5 seconds; 25 preflight checks, three nodes, Docker, Swarm, 18 proxy devices, and Portainer endpoint verified.
- First Selenium run: FAIL as expected evidence, 30/31; Pulsar Manager bootstrap task had exit 137 and no user existed.
- Repaired bootstrap task: exit 0; API login returned success.
- Final Selenium run: PASS, 31/31; suite summary represents nine routes, all passed.
- Windows route: DNS loopback, HTTP 301 to HTTPS, HTTPS 200.

Detailed ignored follow-up logs are under `.tiny-swarm/evidence/follow-up-issue-157-live-install-recovery-20260711/`. Installer reset and setup logs are under `.tiny-swarm-world/evidence/installation-tests/wsl2/20260712T095313Z/`.
