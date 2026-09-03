# Test Results: #285 / CRED-07

## Local verification

- `PYTHONPATH=src python3 -m unittest tests.test_install_script`: PASS, 20 tests.
- `python3 tools/quality_gate.py quality`: PASS, 1908 tests, 18 expected skips;
  verification policy, lint, architecture lint/tests, typecheck and full test
  stages passed.
- `git diff --check`: PASS.

## WSL2 live evidence

All commands below used explicit live approval and the `service-access` profile.
Credential values are intentionally omitted.

| Check | Result |
|---|---|
| Protected fresh install at `20260903T072101Z` | PASS; reset 0, setup 0 |
| WSL2 host and `/mnt/d` checkout | PASS; kernel classified WSL2 |
| Protected evidence root | PASS; user-owned `0700` root/host/run directories |
| Setup phases | PASS; preflight, platform, cluster, secrets, artifacts, deployment and verification completed |
| Catalog source metadata | PASS; required entries resolved as `default` labels |
| Service readiness | PASS; all expected services `1/1` except completed one-shot bootstrap task |
| Protected installer-output redaction | PASS; URLs/users shown, password values not printed |
| Protected evidence redaction scan | PASS; no raw credential/header pattern observed |
| Separate `platform reconcile` with in-process catalog defaults | PASS; exit 0, three nodes verified |
| Portainer forced restart and recovery | PASS; service `1/1`, status endpoint HTTP 200 |
| Deployment readiness verification | PASS; 9 deployment verification targets |
| Direct catalog-backed service authentication | PASS; Portainer, Infisical, Nexus, Jenkins, SonarQube, Pulsar and Pulsar Manager |

The protected run is stored outside the checkout at:
`/home/micro/.local/state/tiny-swarm-world/evidence/cred07-wsl2-secure-20260903/wsl2/20260903T072101Z`.

## Non-pass states

- Native Linux: `LIVE_PREREQUISITE_MISSING`; no target was available.
- Custom/Infisical override: not run; protected input and rotation reference
  were not supplied.
- Browser acceptance: not run; the protected browser-runner contract was not
  satisfied.
- Credential-drift comparison: not verified; reconcile passed but no
  before/after comparison was recorded.

The direct authentication trace is in `service_authentication.md`. Earlier
bounded failures are summarized in `preflight.md`; none is reported as a pass.
