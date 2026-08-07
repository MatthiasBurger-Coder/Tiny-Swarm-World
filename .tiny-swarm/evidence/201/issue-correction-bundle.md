# Issue #201 External Issue-Correction Bundle

Prepared: 2026-08-06
Publication status: `COMPLETE` — public issue bodies were updated and
re-read through the GitHub connector.

This bundle records the applied GitHub issue corrections. The repository
policy is defined in
[`documentation/process/verification-state-policy.md`](../../../documentation/process/verification-state-policy.md).

## Shared policy block for issues #183, #184, and #186–#192

Append or replace the unconditional live/external verification sections with:

```md
## Verification policy

The default authoritative verification for this refactor is:

    python3 tools/quality_gate.py quality

plus focused unit, architecture, contract, integration, or mocked-adapter
tests appropriate to the changed responsibility. This default does not create
or destroy infrastructure, change networking, deploy Docker/Swarm stacks,
start Selenium against live services, use real credentials, or require an
externally inaccessible SonarQube result.

The Three-Amigos note must classify each optional live or external gate as one
of `NOT_APPLICABLE`, `APPLICABLE_LOCAL`, `APPLICABLE_LIVE`, or
`APPLICABLE_EXTERNAL`, explain why it applies, and identify the behaviour it
protects. Applicability does not grant live-mutation consent.

If a live installation, browser/Selenium, infrastructure, or credential-backed
check is applicable, it is separately authorized and reported with one of:

- `LIVE_NOT_APPLICABLE`
- `LIVE_CONSENT_MISSING`
- `LIVE_PREREQUISITE_MISSING`
- `LIVE_BLOCKED_BEFORE_MUTATION`
- `LIVE_FAILED_AFTER_MUTATION`
- `LIVE_PARTIAL`
- `LIVE_DEGRADED`
- `LIVE_VERIFIED`

Only `LIVE_VERIFIED` is live success. Skipped checks, missing consent or
prerequisites, and missing evidence are non-success states. A failure after
mutation blocks completion until repaired or explicitly handled by repository
blocker policy.

SonarQube and other external checks use `EXTERNAL_GATE_NOT_APPLICABLE`,
`EXTERNAL_GATE_UNAVAILABLE`, `EXTERNAL_GATE_BLOCKED`,
`EXTERNAL_GATE_FAILED`, or `EXTERNAL_GATE_VERIFIED`. The actual external result
must be observable before `EXTERNAL_GATE_VERIFIED` can be claimed. When it is
unavailable, local implementation completion is still evaluated by the local
quality gate, while publication or merge may remain blocked by repository
policy.

Any genuinely necessary live or Selenium scenario remains opt-in and must
include executed, redacted evidence. This issue must not claim Selenium success
or a green SonarQube gate from a skipped test, a planned command, a local
configuration file, or an inaccessible external result.
```

## Issue-specific application

| Issue | Required public correction |
|---|---|
| #176 | Replace the unconditional mandatory-install criterion with applicability classification for installation and browser verification. Require the canonical headless command only when the change is installation-relevant, the live gate is `APPLICABLE_LIVE`, and explicit operator consent is present. Preserve non-success handling for missing consent/prerequisites, require redacted evidence for `INSTALL_VERIFIED` or browser success, and separate local implementation completion from unavailable live/external publication policy. |
| #183 | Apply the shared policy to the LXC Swarm runtime refactor; keep the Three-Amigos note and focused regression tests, and make browser verification an authorized opt-in rather than unconditional acceptance. |
| #184 | Apply the shared policy to the LXC node-provider refactor; keep evidence-schema compatibility and lifecycle regression tests, and classify rather than require live Selenium/SonarQube checks. |
| #186 | Apply the shared policy to the explicit composition/DI refactor; keep deterministic DI and architecture tests, and classify rather than require live Selenium/SonarQube checks. |
| #187 | Apply the shared policy to the preflight strategy refactor; keep service-port regression tests, and classify rather than require live Selenium/SonarQube checks. |
| #188 | Apply the shared policy to command-runner centralisation; keep command-result and architecture tests, and classify rather than require live Selenium/SonarQube checks. |
| #189 | Apply the shared policy to shared LXC utilities; keep backend mapping and architecture tests, and classify rather than require live Selenium/SonarQube checks. |
| #190 | Apply the shared policy to stack prerequisite strategies; keep stack-specific regression tests, and classify rather than require live Selenium/SonarQube checks. |
| #191 | Apply the shared policy to typed evidence builders; keep serialized-evidence compatibility tests, and classify rather than require live Selenium/SonarQube checks. |
| #192 | Apply the shared policy to LXC service wrappers; keep URL/authentication/delegation tests and credential-redaction rules, and classify rather than require live Selenium/SonarQube checks. |

## Traceability preservation

- Issue #195 remains the corrected Composition Root merge target.
- Issue #185 remains an absorbed duplicate of #195 and must not be
  reactivated.
- The issue-specific implementation, architecture, and regression-test
  requirements remain unchanged; only their unconditional live/external gate
  wording is normalized.

## Final public issue audit

| Issue | Final state | Verified link |
|---|---|---|
| #176 | open; corrected | https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/176 |
| #183 | open; corrected | https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/183 |
| #184 | open; corrected | https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/184 |
| #185 | closed; absorbed duplicate | https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/185 |
| #186 | open; corrected | https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/186 |
| #187 | open; corrected | https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/187 |
| #188 | open; corrected | https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/188 |
| #189 | open; corrected | https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/189 |
| #190 | open; corrected | https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/190 |
| #191 | open; corrected | https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/191 |
| #192 | open; corrected | https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/192 |
| #195 | open; authoritative successor | https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/195 |

The final audit re-read all listed issue bodies on 2026-08-06. No affected
issue unconditionally requires Selenium success or an external green gate.

## Publication procedure

1. Re-read each issue body immediately before editing to detect concurrent
   changes.
2. Apply the issue-specific correction and shared policy block to #176, #183,
   #184, and #186–#192.
3. Re-read every updated issue body and record the resulting URLs and update
   timestamps in the issue-201 audit evidence.
4. Re-run the repository-wide phrase audit and confirm that no affected issue
   still unconditionally requires Selenium evidence or a green SonarQube gate.
