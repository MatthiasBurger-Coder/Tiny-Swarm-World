# Slice 02 Distribution Decision

Workflow: `issue-183-20260808`
Slice: `02` — Extract the LXC command gateway and shared diagnostics

## Affected areas

* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py`
  manager/node shell methods and diagnostic helpers;
* new `infrastructure/adapters/clients/lxc/command/` package;
* focused command-gateway tests.

## Execution decision

* Chosen mode: `sequential`.
* Real Codex subagents used: `No callable subagent surface is available.`
* Fallback role-based review used: `Yes`.
* Git worktrees used: `No`; shared legacy-module and test locks require the
  checked workflow branch and serialized execution.
* Selected streams: backend, tests, architecture, security/diagnostics.
* Documentation and runtime streams: review-only; no live command is allowed.

## Fallback role review

* Senior Python Automation Developer: extract only reusable shell execution
  and diagnostics; preserve the old runtime delegation methods and patch
  compatibility.
* Senior System Architect: keep the gateway in infrastructure, preserve
  existing application ports, and avoid introducing a new service boundary.
* Senior Tester: preserve subprocess/time patch behavior, bounded output,
  retry, timeout, failure, and backend-selection test coverage.
* Senior Security Sandbox Engineer: retain redaction of assignments, bearer
  values, token parameters, and bounded diagnostic output.

## Expected touched files/directories

* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/__init__.py`
* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/diagnostics.py`
* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/manager_shell_gateway.py`
* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py`
* `.codex/evidence/slice-02-distribution.md`
* `.codex/evidence/slice-02-consolidation.md`

## Conflict risks

The legacy test suite patches `subprocess.run` and `time.sleep` through the old
module path after runtime construction. The compatibility delegation must
resolve those callables at operation time. No parallel stream may touch these
files.

## Quality gates

* focused command-gateway unittest;
* `python3 tools/quality_gate.py lint`;
* `python3 tools/quality_gate.py typecheck`;
* `python3 tools/quality_gate.py arch-lint`;
* `python3 tools/quality_gate.py arch-tests`;
* `git diff --check`.

## Consolidation plan

Codex will run the focused legacy/runtime and new gateway tests, inspect the
diff for compatibility and redaction, write consolidation evidence, and create
one Slice 02 checkpoint commit before Slice 03.

## Parallelization decision

Rejected because the gateway changes the shared legacy module and its existing
patch/test surface. Sequential fallback review is required.
