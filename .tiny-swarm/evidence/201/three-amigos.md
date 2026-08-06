# Issue #201 Three-Amigos Gate

Date: 2026-08-06
Issue: [#201](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/201)
Decision: `READY_FOR_COMPLETION`

## Requirement view

The binding requirement is to normalize verification language across the
repository governance documents and the affected public issues without
silently converting a local check into live or external success.

- Local verification is the default implementation authority:
  `python3 tools/quality_gate.py quality` plus focused tests.
- Live verification protects installation, infrastructure, deployment, and
  service behavior. It is `APPLICABLE_LIVE` only when that behavior is in
  scope; applicability does not authorize mutation.
- External verification protects a behavior through an observable external
  system such as SonarQube. It is `APPLICABLE_EXTERNAL` only when such a gate
  protects the changed behavior.
- Every optional gate is classified as `NOT_APPLICABLE`, `APPLICABLE_LOCAL`,
  `APPLICABLE_LIVE`, or `APPLICABLE_EXTERNAL`, with its protected behavior.
- Operator consent, prerequisites, executed evidence, and the resulting state
  are separate facts.
- Only `LIVE_VERIFIED` and `EXTERNAL_GATE_VERIFIED` describe verified success.
  Missing consent, missing prerequisites, skipped checks, partial/degraded
  execution, unavailable external results, and missing evidence are not
  success.

For Issue #201 itself, the repository behavior is governance-only:

- live/install/browser applicability: `NOT_APPLICABLE`;
- live execution: `LIVE_NOT_APPLICABLE`;
- browser/Selenium: `LIVE_NOT_APPLICABLE`;
- SonarQube: `EXTERNAL_GATE_NOT_APPLICABLE`;
- local quality and policy-consistency checks: `APPLICABLE_LOCAL`.

## Developer view

- The sole canonical source is
  `documentation/process/verification-state-policy.md`.
- `AGENTS.md`, `QUALITY.md`, issue-completion, workflow-create,
  workflow-execute, and the checked workflow consume the policy by reference
  and context-specific guardrails; they do not define competing state lists.
- `tools/check_verification_policy_consistency.py` provides a deterministic
  repository guard for canonical states, forbidden unconditional wording,
  skipped/unavailable success claims, and live commands without consent
  context.
- The checker is standard-library-only and is bound into the existing local
  quality gate without changing runtime architecture or live behavior.
- Existing local gates remain unchanged and continue to run under WSL/Linux.

## Test view

- The focused checker tests use temporary repositories and no external
  services, credentials, live infrastructure, or browser.
- The checker validates the real repository tree and canonical policy.
- `git diff --check`, the focused checker test, the complete test gate, and the
  full quality gate are required.
- Public issues #176, #183, #184, and #186–#192 are re-read after correction;
  #195 remains aligned and #185 remains closed.
- Repository-wide searches verify that no affected issue or governance file
  contains unconditional Selenium/Sonar success language.

## Gate result

Requirement, development, and test perspectives agree. No unresolved
requirement conflict exists. Live mutation is not required for this governance
slice, and no live command is authorized by this gate.
