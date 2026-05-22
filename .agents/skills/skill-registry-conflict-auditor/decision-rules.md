# Decision Rules

## Conflict Classification

Use `BLOCKING` when:

- a mandatory repository rule is weakened;
- an output has multiple owners with incompatible rules;
- a required owner cannot be verified;
- a workflow references a missing skill, role, task, prompt or command;
- a required quality gate is skipped, downgraded or treated as optional;
- a service boundary permits shared Java implementation modules;
- a data ownership rule permits cross-service database access;
- a `.codex` file receives project-specific governance without portability review;
- continuing would require guessing source of truth.

Use `NON_BLOCKING` when:

- responsibilities overlap but one skill is clearly advisory and another is authoritative;
- examples are missing but required rules are complete;
- a future extension is documented as optional;
- a reviewer skill is not yet created but the workflow names an explicit bootstrap fallback role;
- an optional external tool cannot run and the required local gate is still clean.

## Continuation Decision

Return `CONTINUE` only when:

- no `BLOCKING` conflict remains;
- each `NON_BLOCKING` finding has an owner and follow-up path;
- the active workflow location is unambiguous;
- quality-gate authority comes from `QUALITY.md`;
- architecture authority comes from `AGENTS.md` and ADRs.

Return `STOP` when any `BLOCKING` conflict remains.

## Evidence Rules

- Cite exact files inspected.
- Keep planned behavior separate from implemented behavior.
- Do not infer skill responsibility from a similar name when the skill file says otherwise.
- Do not convert an unimplemented target skill into a verified owner.
