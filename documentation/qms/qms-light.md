# QMS-light

## Purpose and scope

QMS-light is the repository's lightweight quality-management operating model.
It makes quality objectives, change control, CAPA, internal audits and
evidence-driven improvement explicit without creating a heavyweight enterprise
QMS or claiming ISO 9001 certification.

The product scope remains Linux/WSL-only Python automation, Docker Swarm-first,
with managed LXC through Incus as the node-provider direction. This document
does not authorize live infrastructure commands, change runtime behavior or
replace a product source of truth.

## Authority and traceability

The authority order is:

1. `AGENTS.md` for product identity, safety and architecture boundaries.
2. `QUALITY.md` and the verification-state policy for local quality commands
   and verification-state classification.
3. The System Unification EPIC at
   `documentation/arc42/01_introduction/system-unification.md` for compatible
   architectural/process context.
4. #120/#122 and the issue requirement matrix for issue scope.
5. This QMS-light documentation for process guidance.

The canonical audit evidence vocabulary and findings links are maintained by
[#121](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/121) in
`documentation/audit/`. QMS-light explains how that evidence is reviewed; it
does not turn planned, missing, blocked or skipped evidence into a pass.

## Quality principles

- No pass claim without a named, reviewable evidence source.
- A local quality-gate pass is local repository evidence, not live, browser or
  external-service success.
- Failed, blocked, refused, resource-gated and evidence-pending states remain
  visible until verified.
- Findings are not closed by documentation presence alone.
- Secrets, tokens, raw environment payloads, private host data and unredacted
  command output do not belong in committed evidence.
- Quality controls may be tightened by an approved change, never silently
  weakened by a QMS document.

## Responsibilities

| Role | QMS-light responsibility |
| --- | --- |
| Lead Architect | Owns architecture authority, boundary decisions and escalation. |
| Senior Tester | Owns applicable checks, reproducibility and test/evidence review. |
| Senior Documentation Engineer | Owns navigation, audience separation and documentation freshness. |
| Senior DevOps Engineer | Reviews deployment, CI/CD and operational evidence boundaries. |
| Security Owner | Reviews secrets, admin surfaces, security CAPA and risk acceptance. |
| Workflow Executor | Enforces S3/S3D, slice locks, evidence, quality gates and handoffs. |

## Evidence model

Each objective, change, CAPA and audit record identifies its source, status,
owner and review date. Evidence is summarized and redacted. The
`documentation/audit/` registers remain the canonical audit index; QMS records
reference them rather than duplicating findings.

## Operating cycle

`objective -> change/evidence -> quality review -> finding/CAPA -> effectiveness
verification -> internal audit -> objective review`

QMS-light is a readiness and governance aid. It is not a certification,
conformity assessment or statement that all audit findings are closed.

