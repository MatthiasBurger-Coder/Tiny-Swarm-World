# Context pack — issue-449-lcm-w09

- Workflow version: 1.5
- Issue: #449, parent EPIC #440, bounded coordination with #318
- Workflow: `documentation/workflow/issues/issue-449/workflow.md`
- Index: `documentation/workflow/workflow.index.md`
- Implementation branch: `feature/lcm-w09-issue449-implementation-20261027`
- Workflow authoring branch: `docs/workflow-lcm-w09-route-baseline-20261027`
- Base: `a0310224946b63e2152ff4086d22a450c3d0f214`
- Existing root #355 workflow/context are preserved and are not selected for #449.

## Scope and operator decision

The user approved a selection-scoped Incus profile and bounded #318 manifest/
optional-stack semantics: Swagger exposure is `published|internal`; schema-v1
state defaults to `published` and direct-Swarm (`swarm`) ownership without
read-time adoption; Portainer-owned stack updates verify endpoint, stack,
ResourceControl and saved-definition identity, disable pruning, and persist
selection only after Swarm convergence. Internal Swagger has no host-published
ports or implicit route. The TSW application route under qualification is
limited to TCP/10001. The user accepted the existing WSL Windows firewall
(`RemoteAddress=Any`) and complete PortProxy state as-is for this run; the
fixture must preserve both snapshots byte-for-byte and adds no external route;
S449-02C captures effective ActiveStore profiles/global settings/rules and all
associated filter types before GO, verifies and records the exact target host
IP, and the independent review binds that read-only capture to the same target
and route-state digest in the GO;
its sole temporary Incus proxy listener is bound to the unique GO-approved
127.0.0.1 fixture port and must be removed after cleanup. A live GO
may bind an exact empty TCP/10001 host-listener and Incus-route baseline; if
present, current routes must be validated and preserved. The fixture does not
attest reachability through other pre-existing Windows forwards. The broad #318
cross-profile Epic stays open and is not completed by this issue.

The user authorized replacing the three owned TSW instances and waived optional
host-baseline backup work. This does not waive the Portainer cold `/data`
archive required by the Portainer-upgrade contract. Live actions still require
exact-source quality, version capability admission, fresh host JIT, per-scenario
same-hash GO and explicit cleanup/recovery.

## Current evidence state

- Existing bounded native/WSL evidence is historical and remains attached to
  its exact source/revision.
- #449 is INCOMPLETE: AC1–AC4 are partial; AC5 and W10 handoff are open.
- WSL Q12/LIVE-4, Q13 attribution, remaining Q16–Q20 variants, R35 attribution,
  full cross-host source/evidence linkage and independent completion audit remain
  open.
- Incus version support for the new selection-scoped capability remains empty
  until the isolated listener fixture and independent review pass.
- No issue is closed by this workflow baseline.

## Required roles

Senior Requirement Engineer, Senior System Architect, Senior Python Automation
Developer, Senior Tester, Senior Workflow Architect, Security, Senior DevOps
Engineer and independent Issue Completion Auditor. All issue-workflow reviews
must bind the final workflow/context hashes.

## Verification and execution boundary

Run Python tests and all QUALITY gates only through SSH to the approved PC WSL
test host, from a verified checkout with matching files/hashes. Live setup and
upgrade scenarios run only on the two designated test machines, serialized by
host. Keep Windows networking unchanged and do not enable unapproved routes.

See `context-pack.json` for the SHA-256 pins for authoritative governance,
workflow and private requirement-artifact snapshots.
