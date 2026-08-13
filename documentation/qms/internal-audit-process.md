# Internal Audit Process

This internal process reviews repository governance and evidence against
declared criteria. It is guidance for project improvement, not an ISO
certification or conformity statement.

## Planning and cadence

- A scheduled internal audit occurs monthly, with a quarterly deeper review of
  quality objectives, release baseline and open major findings.
- An event-driven audit is required after a major security finding, a failed
  public-beta scenario, a repeated required-gate failure, a material architecture
  decision or a significant documentation drift.
- The Lead Architect owns the annual plan and each audit record names the
  scope owner, auditor, reviewer and planned follow-up date.
- Follow-up occurs within 14 days for Critical/Major findings and within 30 days
  for Minor findings or observations, or earlier when release readiness is
  affected.

## Procedure

1. **Plan:** define audit ID, scope, criteria, owner, auditor, dates and
   applicable evidence sources.
2. **Select scope:** choose a workflow, quality objective, architecture
   boundary, security control, release baseline or live-evidence package.
3. **Apply criteria:** use `AGENTS.md`, `QUALITY.md`, the verification-state
   policy, issue/workflow requirements, relevant ADRs and the
   `documentation/audit/` registers.
4. **Collect evidence:** record repository paths, command summaries, status,
   reviewer and redaction treatment. Do not copy secrets or raw host output.
5. **Classify findings:** use the audit register/finding vocabulary; distinguish
   open, evidence-pending, blocked, refused, resource-gated and failed states
   from pass/closure.
6. **Handoff CAPA:** create or update a CAPA with owner, cause, corrective and
   preventive actions, effectiveness evidence and due date.
7. **Review and report:** the independent reviewer records decision, open risks,
   evidence gaps and next review date.
8. **Follow up:** re-check effectiveness against the original criterion and
   retain the evidence link even when the action remains open.

## Guidance references

ISO 19011 and ISO 20246 are used as guidance references for audit planning,
review and evaluation vocabulary only. This repository makes no certification,
conformity or compliance claim from their mention.

## Records

Each audit record includes audit ID, scope, criteria, owner, auditor, date,
evidence links, findings, CAPA links, decision, open risks and follow-up date.
The audit record links to the canonical #121 registers and evidence matrix.

