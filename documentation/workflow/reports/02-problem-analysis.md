# Problem Analysis: Stable Live Setup Failure

## What Worked

- Project Python dependencies were installed into `.venv`.
- Ruff, mypy and import-linter were available in the virtual environment.
- The local quality gate passed:
  lint, import-linter architecture contracts, architecture tests, typecheck
  and unit tests.

## What Failed

Manual host checks failed before live setup:

```text
multipass info -> cannot connect to the multipass socket
multipass get local.driver -> cannot connect to the multipass socket
```

Live setup then failed at:

```text
setup run -> platform init -> platform:init:multipass-vms -> failed_to_apply
```

## Root Cause Shape

Preflight currently checks that `multipass` is available on `PATH`. That is
necessary but not sufficient. A live setup also needs:

- Multipass daemon reachable;
- Multipass socket present and accessible by the current Linux/WSL user;
- expected Linux/WSL driver state;
- a command path that distinguishes "VM missing" from "Multipass unreachable".

The command template for Multipass VM initialization currently starts with
`multipass info {vm_instance}`. Any failure goes to the `else` path and tries
`multipass launch`. If the first failure was caused by socket access, launch
fails for the same reason and the platform workflow records `failed_to_apply`.

## Related Noise

The quality gate output also contained intentional mocked failure log lines
with `boom` and an unawaited coroutine warning. Those should be cleaned up as
test-output hygiene, but they are not the live setup root cause.

## Desired New Behavior

- If Multipass is unreachable, live preflight or the platform guard should
  stop before VM mutation.
- The operator should see a safe classification and remediation, not a late
  generic apply failure.
- A healthy host should continue through platform, artifact, deployment and
  verification phases with observed-state checks.

## Safety Boundary

The workflow plans detection and documentation. It does not authorize
automatic host repair, service restarts, socket permission changes, driver
changes, package installation or live infrastructure execution during default
verification.
