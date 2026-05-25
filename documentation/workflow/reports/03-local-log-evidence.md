# Local Log Evidence: Stable Live Setup

## Scope

This report summarizes local ignored runtime evidence from `.tiny-swarm-world`
for workflow planning. The raw logs remain uncommitted local evidence and must
not be copied into documentation when they contain host-specific paths, local
addresses, credentials, raw commands or diagnostic payloads.

## Evidence Sources

- `.tiny-swarm-world/logs/AsyncCommandRunnerUI.log`
- `.tiny-swarm-world/logs/AsyncPortCommandRunner.log`
- `.tiny-swarm-world/logs/application.log`
- `.tiny-swarm-world/logs/PortVmRepositoryYaml.log`
- `.tiny-swarm-world/live-runs/*.log`
- `.tiny-swarm-world/evidence/verification_results.json`

## Findings

1. The `boom` failures are test/mock noise.

   They appear around unittest execution and use the same `swarm-manager`
   fixture shape. They should be cleaned up as test-output hygiene, but they
   are not the live setup root cause.

2. The current afternoon live failures are real command-runner failures.

   The runner logs show `swarm-manager`, `swarm-worker-1` and
   `swarm-worker-2` failing together with return code `2`. The command runner
   records a redacted diagnostic payload, so the raw Multipass stderr is not
   available from the safe evidence.

3. The failure is before downstream deployment readiness.

   The latest setup stops in `platform init` at
   `platform:init:multipass-vms`. Later phases are not reached.

4. A previous full live setup completed.

   `live-runs/setup-20260525-014558.log` records a completed setup including
   deployment verification and platform verification. This matters because the
   target is stable rerun behavior and actionable readiness gating, not a
   wholesale replacement of the live setup model.

5. Earlier live runs show additional historical downstream failures.

   Older run logs include failures around Portainer admin verification, Nexus
   readiness/admin access and Jenkins image preparation. These should be
   handled in later hardening slices after Multipass readiness is made
   deterministic.

## Diagnosis Boundary

The logs narrow the latest failure to the Multipass VM initialization path, but
they do not expose the exact stderr. Therefore the workflow must avoid claiming
a single confirmed operator cause such as "VM already exists". The implementable
product fix is to classify and gate all known Multipass runtime states before
mutation:

- executable missing;
- daemon/socket unreachable;
- permission denied;
- driver unavailable or misconfigured;
- VM absent;
- VM exists but is stopped, deleted, unknown or unhealthy;
- command output redacted but safely classifiable.

## Workflow Impact

- Slice 02 must include mocked regression tests that keep `boom` out of normal
  quality output or classify it as intentional test noise.
- Slice 03 must add live-readiness probes that check Multipass usability, not
  just executable presence.
- Slice 04 must ensure `platform init --live` cannot bypass the same readiness
  guard and that command catalog logic does not treat Multipass socket failures
  as missing VMs.
- Slice 07 must later harden downstream Portainer, Nexus, Jenkins, registry and
  service-readiness behavior with observed-state tests.
