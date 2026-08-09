# Issue #197 Review — WSL Socat Extraction

Decision: `KEEP_OPEN`

Review baseline: `main` at `ecdc71d94a72530905ecb0a41d2845921ad6debb`.
The issue body and all six acceptance cases were re-read from GitHub.

## Source ownership

The requested extraction is not complete:

- `src/tiny_swarm_world/infrastructure/composition.py:558` still defines
  `_WslSocatExposeStep`.
- The composition module still checks for `socat` at lines 602-614.
- It still inspects processes through `pgrep` at lines 2165-2173.
- It still starts `sh`/`nohup` subprocesses at lines 2176-2184.
- `SocatManager` remains in the application layer at
  `src/tiny_swarm_world/application/services/network/socat/socat_manager.py:13`.
- No focused Socat infrastructure adapter exists under
  `src/tiny_swarm_world/infrastructure/adapters/network`.

## Acceptance trace

| Case or requirement | Status | Evidence |
|---|---|---|
| No subprocess-based Socat management in `composition.py` | `BLOCKED` | Residual ownership and subprocess calls remain. |
| Infrastructure-only behavior | `BLOCKED` | `SocatManager` remains application-owned and no infrastructure adapter was found. |
| Explicit consent and fail-closed behavior | `UNVERIFIED` | A `LiveConsent` guard exists, but no Socat-specific missing-consent regression was found. |
| Native Linux no-op | `VERIFIED_LOCAL` | `test_composed_wsl_socat_expose_verifies_not_required_on_native_linux`. |
| Missing consent | `UNVERIFIED` | Existing consent coverage concerns the LXC proxy path, not the Socat path. |
| Missing `socat` | `VERIFIED_LOCAL` | Composition test coverage reports the unavailable-tool case. |
| Existing process, start success and start failure | `UNVERIFIED` | No dedicated current tests were found for these three Socat cases. |

## Recommended issue action

Keep #197 open and add a current evidence comment. The residual work is to
move process inspection/startup into a focused infrastructure adapter, leave
composition responsible only for wiring, and add dedicated consent, existing
process, success and failure tests while retaining the native no-op and missing
tool guards.

Closing reason: not applicable; architecture and safety acceptance criteria
remain incomplete.

