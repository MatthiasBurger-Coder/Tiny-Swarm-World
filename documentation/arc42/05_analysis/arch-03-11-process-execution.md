# ARCH-03.11: external process execution

Issue: #354. Baseline: 687e2ea7.

## Ownership

Runtime process creation belongs exclusively to `infrastructure/process`:

| Module | Responsibility | Consumers |
|---|---|---|
| `runner.py` | Finite synchronous calls, text/bytes, explicit exit codes, sanitized failures | Host/network probes and repairs, composition probes, installer probes, Infisical, LXC service/runtime adapters |
| `async_runner.py` | Bounded argv/shell calls, launch classification, timeout/cancellation cleanup | Command application-port adapter, LXC node/provider probes, Socat exposure |
| `streaming.py` | Streamed installer phases and captured legacy bridge lifecycle | Installer and Windows bridge adapter |

The existing synchronous `ProcessRunner` protocol remains available to injected
adapters. `run_process` preserves the subprocess result/error family where
existing adapters translate those outcomes into capability-specific results.
The typed runner maps failures to `ProcessLaunchError`, `ProcessTimeoutError`
and `ProcessExecutionError`; both paths use the same execution function.
Async execution reports return code, timeout and launch classification explicitly.
The installer receives a named tuple preserving its historical unpacking contract.
No process is started during imports or constructors.

Adapters retain command construction, retry and capability-specific outcome
mapping. Application services use their existing application ports and never
import subprocess or the concrete runners. Installer orchestration remains an
existing legacy boundary; its two explicit process imports replace direct
spawning and signal handling. This does not complete installer orchestration
extraction. Its legacy dependency map names those two modules specifically.

The AST spawn guard now allows process creation in three central modules,
down from 19 files. It rejects direct spawning in application, adapters and
installer. Terminal clearing uses escape output without a child process.
Standalone development/bootstrap tools remain separately owned; see the
issue inventory. Pure operations gained no abstractions.

## Diagnostics and behavior

Raw stdout/stderr remain private functional data for JSON parsing, image byte
transport, provider classification and credential consumers. Do not log them.
Process result representations hide arguments/output. Timeout diagnostics redact
partial output; launch failures omit executable paths and OS text. Checked
nonzero exits expose only return codes. Original exception chains are suppressed
so formatting a traceback does not restore sensitive command payloads.

Captured/streamed installer output remains subject to its existing evidence and
presentation policy; redirecting a stream is not permission to publish its raw
contents. Callers explicitly choose inherited or redirected output, preserving
interactive installer behavior. The shared boundary never logs raw payloads.

The async runner starts a new session, terminates its process group on timeout
or cancellation, and retains the group identity when the session leader exits.
Socat's detached service remains intentional; only the launch/probe is bounded.
The legacy Windows bridge retains its injected launch seam and outcome flags.

## Verification

`tests.infrastructure.process.test_execution_contract` covers functional results,
nonzero exits, missing commands, timeout, cancellation, launch classifications,
traceback secrecy and process-group termination. Existing installer, network,
LXC and bridge regression tests verify capability-specific mappings.
`tests.architecture.test_process_spawn_boundaries` enforces the single ownership
boundary; `test_hexagonal_imports` protects application imports.

Issue evidence: `.tiny-swarm/evidence/issue-354/`. Local tests do not establish
live infrastructure or external quality results.
