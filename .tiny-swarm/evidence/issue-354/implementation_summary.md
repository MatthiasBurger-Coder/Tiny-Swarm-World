# Issue #354 implementation

Centralized production spawning in infrastructure/process/runner.py,
async_runner.py and streaming.py. Migrated installer, composition probes,
legacy bridge, host/network/preflight probes, LXC commands/services and
Infisical execution. Terminal clearing no longer starts a process.

The existing injectable sync runner delegates to the same compatibility
execution function. Async outcomes preserve exit code, timeout and launch
classification. Installer outcomes are an explicit named tuple preserving
unpacking. Cancellation and timeouts clean up the child session; exit races
are tolerated and cleanup waits are bounded.

Result representations hide payloads; checked failures, partial timeout output,
launch paths and chained errors are sanitized. Functional text/byte output
remains available to parsers/credential consumers. LXC gateway logs omit raw
scripts/stdout/stderr, including unlabelled credential output.

Architecture enforcement reduces the direct-spawn allowlist from 19 files to
3 process modules. The existing legacy installer dependency exception now
explicitly names its two process dependencies; independent architecture review
confirmed this replaces existing execution ownership, without a new exception
file or application dependency. Broader installer extraction is separate work.

## Independent review

Real subagent architecture_review reviewed architecture fit and implementation.
It identified traceback leakage, process-group identity loss after leader exit,
unbounded final waits and cleanup exit races. All were corrected and covered
by regression tests. Requirement, architecture and final test/evidence review passed the
independent issue-completion-auditor audit (audit.md).

Final full quality gate: PASS in hash-verified mounted copy. 2179 tests, 18 skipped. PowerShell/Pester succeeded after unrestricted execution made the existing interop socket accessible. No host configuration change or WSL restart was performed.

Status: DONE. All REQ-001–008 implemented and verified; independent audit PASS. Publication is being handled by the subsequently requested push auto; PR checks and merge are separately verified.
