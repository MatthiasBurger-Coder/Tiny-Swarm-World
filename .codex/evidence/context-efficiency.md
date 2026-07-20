# Context Efficiency Evidence

Governance source references:

- `AGENTS.md` (repository authority; current branch hash checked by Git)
- `QUALITY.md` (quality authority)
- `documentation/process/issue-completion-discipline.md` (completion authority)
- `documentation/workflow/workflow.md` (active workflow authority)

Implemented controls:

- Resolver decisions expose `activated_count` and `rejected_count`.
- Conditional skills require evidence before activation.
- External skills require explicit approval.
- Semantic audit emits blocking `UNNECESSARY_SKILL_ACTIVATION` findings.
- Evidence files reference authoritative documents instead of copying them.

Verification: `tests.architecture.test_activation_resolver` and
`tests.architecture.test_skill_audit`.
