# Slice Distribution — I146-S01

Primary role: Senior System Architect
Review roles: Senior Requirement Engineer, Senior Python Automation Developer, Senior Tester
Distribution mode: role-based fallback review; no visible Codex subagent runtime was available.

## Independence decision

- Each configured `NodeSpec` is an independent target for inspect,
  install-if-needed and verify calls through `PortContainerDockerRuntime`.
- The service owns no mutable per-node state; runtime results carry the node and
  role identity.
- No shared host package-manager call, Swarm bootstrap, join, overlay network,
  or manager-level mutation is moved into the scheduler.
- Result order is the configured node order, independent of completion order.

## Concurrency decision

The default maximum is `2` concurrent node lifecycles. It is constructor
configurable and validated as a positive finite integer. Two permits allow a
manager/worker pair to make progress while keeping a bounded local resource
footprint; this is not a global platform parallelism setting.

## Exit decision

`PASS`: the node lifecycle and bounded scheduler contracts are explicit and
safe to implement in the later serial slices. No product behavior changed in
S01.
