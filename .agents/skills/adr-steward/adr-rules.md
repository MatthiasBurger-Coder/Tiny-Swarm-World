# ADR Rules

## Naming

Use the repository's existing convention:

```text
ADR-0009-short-kebab-case-title.md
```

Do not create files named `0009-title.md` unless the repository convention is explicitly changed by an ADR.

## Required Sections

- Title
- Status
- Date
- Context
- Decision
- Consequences
- Alternatives Considered
- Related Documents

## Status Values

- Proposed
- Accepted
- Superseded
- Rejected

## When An ADR Is Required

An ADR is required for durable decisions affecting:

- microservice boundaries;
- contract-first communication;
- shared-module policy;
- data ownership;
- storage type selection as architecture policy;
- workflow governance;
- quality gate policy;
- security or threat model policy;
- observability or correlation model policy.

## STOP Rules

Stop when:

- the decision conflicts with an existing ADR;
- status is unclear;
- rationale is missing;
- consequences are missing;
- ADR numbering would collide;
- the decision owner is not verified.
