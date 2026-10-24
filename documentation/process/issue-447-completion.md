# W07 Portainer adapter verification and W09 handoff

Issue: [#447](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/447).
Implementation baseline: `4fe6c306c83c9b3ea3fd1c10362ccd9230bfd2a1` plus the
reviewed W07 changes. This report distinguishes bounded adapter acceptance
from cross-host live qualification owned by W09.

## Requirement and acceptance evidence

| Requirement | Implementation and verification |
|---|---|
| Inspect deployment, versions, state and endpoints; AC3 | Portainer inspection, topology and API adapters; runtime integration tests verify identities, authentication, endpoints and ownership. |
| Supported upgrade and backup; AC1/AC2 | CE Server/Agent 2.45.0 to 2.45.1 with fixed image identities, cold checked backup and pre-mutation admission; unsupported versions, missing images, invalid topology and backup failures are tested. |
| API-independent recovery; AC1 | Manager-shell backup restoration preserves failed state and restores original images before API and managed-update verification; interrupted and API-down recovery tests pass. |
| Reuse lifecycle boundaries; AC4 | Application depends on runtime/journal ports; composition wires the existing manager-shell and HTTP adapters; integration tests exercise managed stack PUT and positive task readiness. |
| Preserve foundations; AC5 | No Incus package upgrade, reset, data deletion or credential rotation; generic planner restrictions remain tested. |
| Operator safety and documentation | Preview/no-op, CLI help, invalid arguments and explicit live-consent rejection are covered; the component update guide states supported topology and recovery limitations. |

Full local evidence is retained under `.tiny-swarm/evidence/issue-447/`:
the requirement matrix R1-R13, implementation summary, changed-file list,
test results, risks, acceptance checklist and independent audits. The directory
is intentionally ignored; private runtime material is not published.

## Local verification

The prior full quality gate passed: 2803 tests, 18 skips; architecture tests,
seven import contracts, lint, typecheck, complexity and verification-policy
checks passed. All 25 recorded W07 file hashes matched that tested tree before
this publication review; subsequent edits reconcile documentation and the
operator-requested SSH test-host instructions.

On 2026-10-24, the SSH/WSL test checkout matched all 2579 files in the live
candidate source manifest. The current focused unittest set passed 52 tests
in 2.476 seconds, exit 0. The host is WSL2, Python 3.14.4, using an isolated
virtual environment. This is local/mock verification executed remotely, not
live service qualification.

The fresh full `python3 tools/quality_gate.py quality` gate passed with the
venv on PATH and a fresh temporary `XDG_STATE_HOME`: 2803 tests in 176.372s,
18 skipped, exit 0. Policy, complexity (341 modules), lint, seven import
contracts, architecture (43 tests) and typecheck (866 files) all passed.
Skipped checks are not live successes. Earlier attempts exposed missing
development tooling, an outdated AGENTS.md registry hash and two existing
tests reading the user's real bootstrap checkpoint. Installing the pinned CI
tools, synchronizing the registry hash and isolating test state resolved them;
the seven targeted rechecks passed. No quality rule or test was weakened.

Independent evidence reconciliation passed and verified the open W09 handoff.
Final publication checks, including CI and SonarCloud, must pass before merge.

## Live evidence and unresolved W09 blocker

The October 24 records supersede the older statements that no live execution
occurred. Native logs record upgrade, managed-update proof, repeat no-op and
API-down recovery. This supports the recorded bounded native scenario only,
not completion of the W09 host matrix or browser checks.

WSL2 is **LIVE_FAILED_AFTER_MUTATION** during qualification setup. An isolated
project, bridge, manager container and Swarm were prepared; image preparation
then failed with command exit 1. The remote runner was missing, so the actual
adapter upgrade/recovery scenario never started. The final inventory retains
the running test manager. Existing service IDs/specification hashes and volume
names match, but original workers changed from stopped to running and original
node configuration hashes changed. The cause is unverified; the existing host
must not be described as unchanged.

The open [W09 blocker handoff](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/449#issuecomment-6382026747)
assigns diagnosis, restoration or explicit retention of owned resources, and
fresh qualification to #449, which already owns cross-host live evidence under
#447 AC4. This handles the failed live qualification separately from bounded
W07 implementation acceptance; it does not turn failure into success. W09
AC1/AC2/AC4 remain non-pass for this WSL attempt until resolved.

Preserve recovery artifacts and serialize shared-host operations. Verify
explicit live consent before further mutation. This publication review makes
no live infrastructure changes. Never publish private credentials, raw backups,
environment values or JWTs. CI and SonarCloud status must be verified on the
published PR; local tests do not establish external-gate success.
