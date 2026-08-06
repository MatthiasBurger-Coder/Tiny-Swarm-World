# Issue #201 Policy Reference Map

Date: 2026-08-06

Canonical source: `documentation/process/verification-state-policy.md`

| Source document | Referenced section | Reference type | Role | Result |
|---|---|---|---|---|
| `AGENTS.md` | Python/testing and workflow execution rules | path reference plus local-first guardrail | consuming governance | PASS |
| `QUALITY.md` | quality contract and optional-gate failure policy | path reference plus local/external distinction | consuming quality contract | PASS |
| `documentation/process/issue-completion-discipline.md` | mandatory completion loop | path reference plus evidence wording | consuming completion process | PASS |
| `documentation/process/workflow-create.md` | slice and gate definition | path reference plus applicability rule | consuming workflow-authoring process | PASS |
| `documentation/process/workflow-execute.md` | targeted and required gates | path reference plus non-success rule | consuming workflow-execution process | PASS |
| `documentation/workflow/workflow.md` | verification-state policy note | direct path reference | consuming checked workflow | PASS |
| `tools/check_verification_policy_consistency.py` | canonical state constants and required fragments | executable validation of the canonical source | deterministic quality guard | PASS |

No consuming document defines a competing complete state vocabulary. The
checker rejects unknown state tokens, unconditional Selenium/Sonar wording,
unavailable-or-skipped success claims, and the canonical install command when
nearby explicit consent context is absent.
