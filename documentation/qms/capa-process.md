# CAPA Process

Corrective and Preventive Action (CAPA) keeps quality problems visible until
the cause is addressed and effectiveness is verified. CAPA is a process
record, not an assertion that an audit finding is closed.

## Triggers

| Trigger | Initial action | Evidence link |
| --- | --- | --- |
| Audit finding | Create or update a CAPA linked to the finding ID and containment decision. | Findings register and evidence matrix |
| Quality-gate failure | Record failed gate, affected slice and reproducible command; do not retry silently. | Quality-gate output summary and workflow evidence |
| Security finding | Apply containment, redact sensitive detail and route to the Security Owner. | Security review and CAPA record |
| Failed live run | Preserve the failed scenario/state, rollback or stop safely, and classify live evidence. | Live-evidence contract and redacted result |
| Regression | Identify the behavior and add a regression check before closure. | Test result and changed requirement |
| Documentation drift | Correct the authoritative page or open a documentation CAPA with an owner. | Documentation diff and review record |

## Severity and ownership

- **Critical:** potential secret exposure, unsafe live mutation or release-blocking
  integrity failure. Security Owner and Lead Architect review immediately.
- **Major:** failed required gate, major audit finding or reproducibility loss.
  The responsible owner and Senior Tester define containment and correction.
- **Minor:** localized defect, stale link or non-blocking documentation gap.
  The responsible domain/process owner schedules correction.
- **Observation:** improvement opportunity. The owner records disposition and
  review date without treating it as closed evidence.

Every CAPA has an ID, trigger, severity, owner, reviewer, affected requirement or
finding, containment state, root-cause record, corrective action, preventive
action, due date, evidence links and status.

## Lifecycle

1. **Record and triage:** capture the trigger, source, severity, owner and
   affected requirement. Keep the originating evidence redacted.
2. **Contain:** prevent unsafe merge/release or further exposure. A refused or
   blocked live action remains blocked; it is not converted into success.
3. **Analyze cause:** use an appropriate root-cause method (for example
   five-whys, fault tree or causal timeline). Critical and major actions require
   a reviewed cause statement.
4. **Correct:** define the immediate corrective action, changed artifact,
   reviewer and verification check.
5. **Prevent:** define the systemic control, documentation/process update or
   regression test that prevents recurrence.
6. **Verify effectiveness:** compare the objective or expected behavior against
   new evidence after the correction. Effectiveness evidence must be specific,
   reproducible and reviewed by someone other than the implementer for
   critical/major actions.
7. **Close or retain:** close only when containment, cause, corrective action,
   preventive action and effectiveness evidence are all present. Otherwise keep
   `Open`, `In progress`, `Evidence pending`, `Blocked` or another
   explicit non-pass state.

Skipped, missing, refused, resource-gated, failed-to-apply and failed-to-verify
evidence cannot close a CAPA. Documentation presence alone cannot close an
audit finding. Link applicable actions to
`documentation/audit/findings-register.md` and its evidence matrix.

