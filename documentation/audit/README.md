# Audit Evidence

This directory is the canonical, versioned governance index for audit
evidence in Tiny Swarm World. It connects findings to standards, owners,
planned remediation, review decisions and evidence locations. It does not
replace source code, tests, runtime configuration or redacted live-run
artifacts as sources of truth.

## Relationship to the roadmap

- [Issue #120](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/120)
  is the parent roadmap and closure/re-audit authority.
- [Issue #121](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/121)
  establishes this evidence structure.
- Later child issues use the stable IDs and paths here. A link to a planned
  artifact is not evidence that the artifact exists.
- The repository-local [`audit-summary.md`](audit-summary.md) snapshots the
  explicitly enumerated #120/#121 finding set and is the local source for
  completeness checks. It does not claim that findings are closed.
- The [System Unification EPIC](../arc42/01_introduction/system-unification.md)
  explicitly owns this audit-evidence backbone as a governance extension.

The current documentation baseline is an evidence-management structure, not a
certification, conformity assessment or completed audit. Applicability of a
standard must be decided in the relevant follow-up work.

## Files

| File | Purpose |
| --- | --- |
| [`audit-register.md`](audit-register.md) | Audit scopes, standards, owners and review status. |
| [`findings-register.md`](findings-register.md) | Stable finding IDs, severity, risk, remediation and disposition. |
| [`evidence-matrix.md`](evidence-matrix.md) | Requirement/finding-to-evidence mapping and redaction obligations. |
| [`remediation-plan.md`](remediation-plan.md) | The ten roadmap workflows and their completion criteria. |

## Evidence-state contract

Repository evidence, planned evidence, live evidence and missing evidence are
different states. The following states are never pass states by themselves:

- `planned`
- `missing`
- `blocked`
- `refused`
- `resource-gated`
- `failed-to-apply`
- `failed-to-verify`

Finding disposition (`Open`, `In progress`, `Evidence pending`, `Risk
accepted`, `Closed`, `Not applicable`), evidence state, live/external
verification state and issue-completion state are recorded separately. `Closed`
requires a linkable, redacted evidence artifact and an independent review; the
presence of a documentation file cannot close a finding.

## Standards and applicability references

These references provide vocabulary and review lenses only. They do not imply
certification, registration or automatic applicability:

- ISO 19011: audit-program and audit-activity guidance.
- ISO 20246: review and evaluation guidance.
- ISO/IEC 33001 ff.: process-assessment vocabulary and related parts.
- ISO 9001: quality-management reference for QMS-light work.
- ISO/IEC 25010: product-quality model reference.
- ISO/IEC 27001: information-security-management reference for ISMS-light
  work.
- OWASP ASVS: application-security verification reference.
- DIN 66270: applicability must be assessed for the concrete product and
  evidence purpose before use.
- ISO/IEC 12207: software-lifecycle reference.
- ISO/IEC/IEEE 26514: user and system documentation reference.

The registers must state when a reference is planned, not applicable,
resource-gated or awaiting an authoritative applicability decision.

## Repository and live evidence boundary

Repository evidence may include committed documentation, source paths,
configuration schemas, test results, quality-gate results and checksums. Live
evidence may be summarized only after an explicitly authorized run and must be
redacted before it is retained. No live evidence is claimed by this baseline.

Do not commit or copy into this area:

- secrets, passwords, API tokens or credentials;
- raw environment payloads or `.env` content;
- Docker Swarm join tokens;
- raw command dumps or raw stdout/stderr;
- private host paths, private IP addresses or unredacted local logs.

If such data is necessary to support a conclusion, retain it in the approved
protected system and commit only a redacted summary, reference, checksum or
state. A missing or redaction-blocked artifact stays non-pass.

## Ownership and maintenance

The Audit Evidence Manager maintains the registers. Requirement Engineering
maintains requirement mappings, Documentation Engineering maintains navigation,
Security and QMS/ISMS owners review their respective controls, and the Issue
Completion Auditor decides whether an issue can be marked complete. Changes
must preserve stable IDs, explicit status and source-path accuracy.
