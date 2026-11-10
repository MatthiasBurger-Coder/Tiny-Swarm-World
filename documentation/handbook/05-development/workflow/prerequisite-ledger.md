# Prerequisites, ownership and effort

| Dependency / owner | Inspected baseline | Actual state | Consumer and gate | Included effort |
|---|---|---|---|---|
| Existing CLI and lifecycle composition / Python + Architect | core __main__, composition_profile, component_updates/portainer CLI, application lifecycle services | Implemented paths and substantial tests exist; installed-path completeness must be inventoried | S440-01/04; no second executor | 1.5–4 days |
| Security and reliability / Security + Python + Tester | host_network_repair; installation_profile; versioned_manifest_repository; migration_admission | One S2083 and three S7497/S3403 findings; actual gate red at ca690257 | S440-02/03; regression and unchanged Sonar gate | 2–4 days |
| Scoped profile runtime / Python + Architect | composition_profile/runtime, profile services/Incus clients, installation lock | Integration exists; capability asset admitted_versions is empty | S440-04; prove all direct/recovery/cleanup callers, exact route/ownership and lock semantics | 1–3 days |
| Qualification workflow binding / Python + Tester | incus_profile_listener_fixture.git_preflight and native_lxd_maintenance.FILES | Hardcoded historical issue-449 workflow path; old hash approvals are not current GO | S440-05 must rebind before new fixture use; source/approval mismatch stays fail-closed | 1–2 days |
| Native and WSL Incus 6.0.5 / DevOps + independent reviewers | Accepted scoped-profile ADR; historical native fixture | Native bounded fixture result exists; paired current-source WSL proof and support admission missing | S440-06/07; independently reviewed listener/HTTP/cleanup before exact admission | 1.5–3 days, waiting excluded |
| Recoverable Portainer-owned fixtures / DevOps + Tester | Existing Portainer upgrade service/runtime/CLI and Q12 design | Native bounded upgrade accepted; WSL Q12/Q13 process attribution incomplete | S440-08; cold /data backup, owned managed stack, API-down restore and preservation | 1–2 days plus execution |
| Component qualification policy / Catalog owner + Tester | component_transitions.py and NativeComponentCatalog/#297 executor | Swagger/Traefik pinned candidates, not supported production targets | S440-09 staged candidate-branch qualification then independent admission; no force override | 1–2 days plus execution |
| Selection/product variants / Requirement + Tester | W09 Q01–Q20, selection/product services and CLI | Bounded history and full-install smoke exist; remaining current-source variants unreconciled | S440-10 executes only proven gaps, two distinct resolved optional sets | 2–4 days plus provisioning |
| Final exact-source docs/gates/audit / Documentation + independent auditor | W09/W10, user guides, QUALITY/CI/Sonar | No parent PASS; earlier merge exception covers obsolete configuration only | S440-11/12, all required actual gates green | 1–2.5 days plus review waiting |

Ranges overlap the slice estimates; do not sum this diagnostic ledger separately.
Workflow total: 11–24 engineer-days, including prerequisite implementation and
qualification effort, excluding calendar waiting. No host readiness, unused port,
backup, registry availability or reviewer is assumed from an issue's closed state.

## S440-01 runtime readiness boundary

The local execution branch/ref and clean initial source 07cc4115 were verified.
A separate designated Windows-PC Ubuntu WSL checkout was cloned at that exact
revision, with its own package environment. Its installed tiny_swarm_world resolves
inside that checkout; the previous live-install checkout was not modified.

| Prerequisite fact | Current evidence | Status / owning gate |
|---|---|---|
| Unit/quality host and isolated installed source | SSH/WSL Python 3.12.15; exact 07cc4115 clone and package path checked; 96 CLI tests pass | VERIFIED for deterministic tests only |
| Native/WSL fixture ownership and absence of foreign writers | Historical records identify bounded targets; no fresh operational inventory or maintenance approval in this slice | NOT_VERIFIED; S440-06 JIT/GO |
| Current exact Incus client/server 6.0.5 and isolated listener port | Historical native result is not paired current-source WSL qualification | NOT_VERIFIED; S440-06 before effects |
| Recoverable Portainer-managed stack and cold /data backup | Required by existing dedicated runtime; no usable current fixture backup was asserted | NOT_VERIFIED; S440-08 admission |
| Current Windows firewall/PortProxy/routes/issue447 baseline | Historical preservation evidence exists; fresh snapshots remain required | NOT_VERIFIED; S440-06/08 scoped preservation |
| Current consent for an exact destructive/interruption/restore scenario | workflow execute authorizes configured workflow/testing; no blanket live host mutation is inferred | LIVE_CONSENT_MISSING unless an existing exact-scope approval is separately verified |

S440-01 is PARTIAL overall because its approved-live-fixture clause has no fresh
runtime evidence. Its deterministic inventory is accepted for S440-02/03 under
the explicit instruction to continue independent deterministic fixes; the live
dependency is retained, not silently marked DONE or moved out of parent scope.
