# Slice 06 Distribution Decision

Workflow: `issue-183-20260808`
Slice: `06` — Extend the issue-specific browser evidence contract

## Affected areas

* `tests/live/browser_e2e_contract.py`;
* `tests/live/test_post_install_browser_live.py`;
* ignored issue evidence path under
  `.tiny-swarm-world/evidence/solid-lxc-swarm-runtime/e2e/`.

## Execution decision

* Chosen mode: `serialized-live` with a static-contract branch only.
* Real Codex subagents used: `No callable subagent surface is available.`
* Fallback role-based review used: `Yes`.
* Git worktrees used: `No`; the browser contract and live test file are
  explicitly locked and the live path is consent-gated.
* Selected streams: tester/static contract, DevOps prerequisite review, and
  security/evidence-redaction review.
* Live Selenium execution: `Not authorized`; no live consent, browser
  prerequisites, or external runtime evidence was supplied by this request.

## Fallback role review

* Senior Tester: preserve the issue-specified Selenium imports, routed
  service-access checks, and explicit live-state semantics.
* Senior DevOps Engineer: inspect prerequisites without starting Incus, Docker,
  Swarm, Portainer, Nexus, or browser infrastructure.
* Senior Python Automation Developer: keep the test importable and isolated
  from default local quality gates.
* Senior Security Sandbox Engineer: require redacted evidence and prevent
  credentials/page payloads from being written.

## Expected touched files/directories

* `tests/live/browser_e2e_contract.py`
* `tests/live/test_post_install_browser_live.py`
* `.codex/evidence/slice-06-distribution.md`
* `.codex/evidence/slice-06-consolidation.md`

## Stop condition

The live run stops at `LIVE_CONSENT_MISSING` unless explicit consent and all
required runtime/browser prerequisites are observable. Static contract tests
may run locally and must not claim live success.

## Quality gates

* `PYTHONPATH=src python3 -m unittest tests.live.browser_e2e_contract`;
* `git diff --check`;
* no live command or browser mutation.

## Consolidation plan

Codex will inspect/extend only the static browser contract, run its local
import test, record the live-consent state with no evidence payload, and create
one Slice 06 checkpoint before Slice 07.
