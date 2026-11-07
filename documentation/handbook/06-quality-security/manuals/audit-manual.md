# Audit Manual

[Product Handbook](../../../README.adoc) / [Part 6: Quality, security and audits](../README.adoc)

This is the audit and evidence entry point. Audit documents are governance
artifacts, not certification evidence.

## Canonical sources

Start with the [audit evidence README](../audit/README.md),
[findings register](../audit/findings-register.md),
[evidence matrix](../audit/evidence-matrix.md) and
[remediation plan](../audit/remediation-plan.md). The
[traceability matrix](../../07-evidence-release/traceability/traceability-matrix.md) maps selected
requirements through architecture, implementation, tests, quality and
evidence.

## Quality and review

Use [QMS-light](../qms/qms-light.md), the
[change-control process](../qms/change-control.md), the
[internal-audit process](../qms/internal-audit-process.md) and the
[PR review policy](../governance/pr-review-policy.md). Findings remain open,
blocked or evidence-pending until their required evidence exists.

## Evidence language

The [verification-state policy](../../05-development/process/verification-state-policy.md) is
authoritative. Local quality is not live success; missing, refused,
resource-gated and unavailable external results remain non-pass states. For
future live runs use the [canonical live evidence contract](../../07-evidence-release/evidence/live-greenpath-evidence-contract.md)
and its [redaction rules](../../07-evidence-release/evidence/redaction-rules.md).
