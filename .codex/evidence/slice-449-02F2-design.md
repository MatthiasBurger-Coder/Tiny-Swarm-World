# S449-02F2 design decision — symbolic native unit diagnosis

## Trigger

The committed S449-02F v1.37 collector ran under its dedicated post-commit S3D plan and returned `BLOCKED:EXECUTABLE_IDENTITY_BLOCKED`. A bounded follow-up confirmed that the inventory artifact was absent. The private attempt record confirms no runtime state changed.

## Three-Amigos decision

- Requirement: the attempt remains BLOCKED; it does not prove ownership or satisfy any acceptance criterion. Diagnose only the fixed unit and symbolic identity; unknown remains blocked.
- Architecture: conditionally approved inside the existing collector, reusing its Runner, parser, fixed unit list and exact identity map. No separate module or client path.
- Python automation: approved after the actual v1.37 failure was confirmed. Add only an explicit opt-in diagnostic mode; preserve exact allowlist and execution limits.
- QA: conditionally approved; tests must prove fixed units, validated service PIDs, no raw path/PID/output leakage, immediate stop on unknown, no endpoint/client calls and no artifact.
- Security: symbolic-only output is required; never return or persist raw executable paths or command output.
- DevOps: approved as a separate read-only phase only after exact source commit/hash binding and a fresh S3D plan.

## Scope

Add `--diagnose-units` to `tools/qualification/native_runtime_inventory.py` and deterministic tests. The mode processes the five fixed systemd units one at a time in their declared order, reading executable identity only for active service units with validated positive MainPID. It compares the resolved path in memory against the current exact allowlist and rechecks that service's normalized state/PID tuple before moving on. On the first unknown identity it stops before issuing any command for a later unit. Stdout is one compact deterministic JSON object: a complete result lists service IDs and allowlisted identities in fixed order; the first unknown result emits only its fixed unit ID and `UNKNOWN`, with no partial successes. Other failures emit only a fixed block code. PIDs, raw paths, raw output, exception strings and command records are prohibited from output. The CLI mode takes no output path, performs no endpoint/client/resource calls and never writes an artifact. No allowlist is broadened.

The diagnostic CLI rejects any extra argument before argparse can print usage
or echo caller-supplied values; it emits only
`BLOCKED:DIAGNOSTIC_ARGUMENTS_INVALID`. Normal inventory CLI behavior remains
unchanged.

## Verification and phase boundary

Run the focused suite and full quality gate on the approved PC WSL host against exact hashes. Commit this sub-slice before requesting a dedicated native diagnostic S3D plan. A diagnostic `UNKNOWN` remains BLOCKED. Any identity mapping change requires authoritative provenance and a separate reviewed source/test/workflow/context amendment and S3D plan.
