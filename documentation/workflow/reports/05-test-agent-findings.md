# Senior Tester Findings

## Testability

The workflow is testable with deterministic unit tests and fake Portainer HTTP
responses. No test should require live Portainer, Docker, LXC, Incus, or Swarm.

## Required Regression Coverage

* Existing endpoint named `local` returns success.
* Missing endpoint plus successful creation returns success.
* Creation failure returns `failed_to_apply` evidence with HTTP status and
  redacted response body.
* Transient readiness is retried with bounded attempts and no real sleeps in
  tests.
* Unsafe secret-bearing values do not appear in messages, logs, or evidence.

## Targeted Commands

```bash
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_portainer_http_client
PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_portainer_endpoint tests.application.services.deployment.test_deployment_workflows
git diff --check
```

## Full Gate

```bash
python3 tools/quality_gate.py quality
```

## Decision

No quality blocker for workflow execution. Live `./install.sh` validation is a
separate operator-approved step.
