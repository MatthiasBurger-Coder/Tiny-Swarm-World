# Pull-Request Review Policy

## Required PR body evidence

Every PR must contain these fields:

1. Summary.
2. Files changed or affected areas.
3. Scope and non-goals.
4. Quality-gate commands, environment and exact result.
5. Explicit live-command statement: what was not run, or the separately
   authorized live evidence reference.
6. Security impact, including secret/redaction and admin-surface impact.
7. Documentation and architecture impact.
8. Remaining blockers, deferred states and rollback/recovery reference.

The body must distinguish local, live, browser, installation, external and
certification evidence. A local test or quality pass must never be described
as a live or SonarQube success.

## Reviewer triggers

| Change type | Required review |
| --- | --- |
| Any change to workflow, process or evidence status | Requirement and evidence review; QMS review when quality/CAPA is affected |
| Runtime, ports/adapters or dependency direction | Senior System Architect and relevant implementation/test reviewer |
| Secrets, admin surfaces, transport, Docker socket or service exposure | Security reviewer; ASVS review where applicable |
| CI, branch, release or quality policy | Branch CI Governance Expert, Tester and Documentation Engineer |
| Requirement drift, new non-goal or acceptance change | Three Amigos / Requirement Engineer |
| Live validation or installation behavior | Explicit live-validation applicability, consent and evidence review |

The implementer is not the sole completion authority. Issue-driven work needs
an independent completion audit and a requirement-to-evidence matrix.

## Gate and merge handling

- Failed, unavailable or unverifiable required checks block merge.
- A skipped check requires an exact reason, applicability decision, nearest
  meaningful check and non-pass status; it cannot be silently waived.
- Reviewers may not approve a bypass based on an unobserved or guessed status.
- Security, architecture and requirement blockers remain open until treatment
  and evidence are recorded.
- Merge only after required approvals, required checks and PR evidence are
  present. Use the repository-approved branch and cleanup flow.
- Post-merge cleanup must verify the merge before deleting only the merged
  remote head branch; no force-push or direct `main` push is allowed.

## QMS, audit and security traceability

Change control, review, CAPA and internal-audit expectations come from #122
QMS-light. Security boundaries, secret handling, risk ownership, redaction and
incident routing come from #123 ISMS-light. #121 audit findings remain linked;
MAJ-05 is the specific QMS governance finding addressed by this policy set.

No PR body may contain real credentials, raw environment values, private host
data, protected control text or unsupported certification/closure claims.
