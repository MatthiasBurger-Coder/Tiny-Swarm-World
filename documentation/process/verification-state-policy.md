# Verification-State Policy

This policy is the canonical repository rule for deciding whether local,
live, browser, installation, or external quality checks apply to a change.
It is referenced by `AGENTS.md`, `QUALITY.md`, the workflow processes, and the
issue-completion discipline.

## Default local verification

Unless a Three-Amigos decision classifies a live or external check as
applicable and separate operator consent is available, implementation
verification consists of:

```bash
python3 tools/quality_gate.py quality
```

plus focused unit, integration, architecture, contract, or mocked-adapter
tests appropriate to the change. The command is the default authoritative
local gate.

The default gate must not implicitly:

- create or destroy VMs or containers;
- reset an installation;
- change WSL, Linux, or Windows networking;
- bootstrap LXC, LXD, or Incus;
- deploy Docker or Swarm stacks;
- use real credentials;
- start Selenium against live services; or
- require a SonarQube or other external result that the workflow cannot access.

## Applicability decision

The Three-Amigos note for each affected workflow must classify every optional
gate as exactly one of:

| State | Meaning |
|---|---|
| `NOT_APPLICABLE` | The check protects no behaviour changed by the workflow. |
| `APPLICABLE_LOCAL` | A local, static, mocked, or deterministic check protects the changed behaviour. |
| `APPLICABLE_LIVE` | A live installation, service, browser, or infrastructure check protects the changed behaviour. |
| `APPLICABLE_EXTERNAL` | An external system, such as SonarQube, protects the changed behaviour. |

This decision explains why the gate applies and what behaviour it protects. It
does not grant permission to mutate live infrastructure. Live execution still
requires explicit operator approval through the approved live-validation
mechanism.

## Live-validation states

Installation, Docker/Swarm, LXC/LXD/Incus, networking, service bootstrap,
credential-backed, and browser/Selenium checks use these states:

| State | Meaning |
|---|---|
| `LIVE_NOT_APPLICABLE` | The live check was classified as not applicable. |
| `LIVE_CONSENT_MISSING` | The check applies, but explicit operator consent is absent. |
| `LIVE_PREREQUISITE_MISSING` | Consent exists, but a required runtime, credential, or service prerequisite is absent. |
| `LIVE_BLOCKED_BEFORE_MUTATION` | A guarded preflight stopped the check before mutation. |
| `LIVE_FAILED_AFTER_MUTATION` | The check failed after live mutation started. |
| `LIVE_PARTIAL` | Only part of the live scenario was verified. |
| `LIVE_DEGRADED` | The scenario completed with an observed degraded or incomplete runtime state. |
| `LIVE_VERIFIED` | The authorized scenario executed successfully and produced redacted evidence. |

Only `LIVE_VERIFIED` may be described as live success. A skipped test,
unavailable credential, missing prerequisite, absent infrastructure, or missing
evidence is never a pass. A failure after mutation blocks completion until it
is repaired or handled under the repository blocker policy.

For installation-relevant pull requests, installation and browser-verification
applicability must always be classified. The canonical full live-install
command remains:

```bash
./install.sh --headless --confirm-reset --non-interactive-live-approval
```

It is opt-in and must never be executed automatically merely because a change
touches an installation-related file. When authorized, the evidence must be
redacted and identify the command, runtime classification, selected profile,
reset/setup result, exit code, evidence path, and blocker or success summary.

## External quality-gate states

SonarQube and other external systems use these states:

| State | Meaning |
|---|---|
| `EXTERNAL_GATE_NOT_APPLICABLE` | The external check protects no behaviour changed by the workflow. |
| `EXTERNAL_GATE_UNAVAILABLE` | The external system or its result cannot be accessed. |
| `EXTERNAL_GATE_BLOCKED` | Repository policy prevents publication or merge until the external gate can be observed. |
| `EXTERNAL_GATE_FAILED` | The accessible external result is a failure. |
| `EXTERNAL_GATE_VERIFIED` | The workflow accessed the actual external result and it passed. |

`EXTERNAL_GATE_VERIFIED` is valid only when the actual result is observable.
When the gate is unavailable, the local quality gate remains authoritative for
local implementation completion; publication or merge may still be blocked by
repository rules. An unavailable external result must never be reported as
green.

## Completion and evidence language

Workflow and issue text must distinguish:

1. implementation completion based on local verification;
2. live applicability, consent, prerequisites, and evidence state; and
3. external-gate availability, result, and publication policy.

Claims such as “live verified”, “Selenium passed”, or “SonarQube is green”
require executed, redacted evidence for the actual scenario. The presence of a
configuration file, a skipped test, a planned command, or a reachable-looking
URL is not evidence of success. Local files such as
`.tiny-swarm-world/local/live-installation.env` are configuration inputs only;
they do not grant live consent and must not be committed.
