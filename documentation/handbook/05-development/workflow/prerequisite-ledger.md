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
