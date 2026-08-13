# Change Control

Change control connects an intended change to a reviewed, verified and
evidence-backed integration decision.

## Required flow

```
Requirement
  -> issue/workflow
  -> dedicated branch/worktree
  -> small locked slice
  -> implementation
  -> applicable quality gate
  -> review
  -> PR evidence
  -> merge
  -> baseline/evidence update
```

Every governed change uses a dedicated workflow branch and small slices with
explicit owner, dependencies, locks, acceptance criteria and rollback or
recovery considerations. Shared or mandatory-order changes are serialized.

## Classification and impact analysis

Before implementation, classify the change as documentation/governance,
runtime/DevOps, architecture, security-sensitive, contract, or release. Record
affected files/modules, requirements, evidence, risks, live applicability,
external-gate applicability and required reviewers.

Security-sensitive changes require Security Owner review. Runtime, deployment,
network, secret, admin-surface and live-evidence changes additionally require
the relevant architecture, DevOps and live-evidence decisions. Documentation
changes that describe behavior must be checked against verified repository
behavior; planned behavior stays labeled planned.

## Review and merge controls

- A PR is required for governed changes unless repository policy explicitly
  records an exception.
- The PR body records summary, changed files, requirement/evidence mapping,
  quality-gate result, no-live confirmation and remaining gaps.
- The applicable quality gate must pass before merge. For #122, this includes
  `git diff --check` and `python3 tools/quality_gate.py quality`.
- Reviewers verify architecture, requirement coverage, security impact,
  documentation consistency and evidence integrity.
- Unavailable, skipped, blocked or failed checks are recorded as such and do not
  become a pass by omission.
- Merge does not close an audit finding unless the finding's closure evidence
  and independent review are present.

## Documentation and safety rules

Update the nearest authoritative documentation when behavior changes. Do not
duplicate large content into navigation pages. Live infrastructure commands,
service bootstrap, reset and network mutation are prohibited unless explicitly
requested and approved through the live-validation mechanism. This document
does not grant that approval.

No secrets, tokens, raw environment payloads, private host paths/IPs or
unredacted command output may be committed. A suspected leak is a Security CAPA
and blocks the change until handled.

