# #440 requirement-to-delivery matrix

Source: [current GitHub #440](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/440), last updated 2026-11-08T14:31:54Z.
Inspected runtime baseline: `ca6902579f51c2c6d9439bf9c58dec02bfb45a93`. This is a planning matrix, not independent PASS.
Original parent acceptance remains authoritative. No closed implementation issue
or bounded historical row qualifies an unexecuted current-candidate scenario.

## Parent acceptance crosswalk

| ID | Requirement | Actual baseline state | Owning slices | Evidence/gap |
|---|---|---|---|---|
| P01 | Historical product release 0.4.0 → 0.5.0 | VERIFIED (historical bounded scope) | S440-10, S440-12 | Retain accepted Q14/Q15; only remaining current-candidate variants need qualification. |
| P02 | Single and selected-batch component updates | OPEN | S440-05, S440-09, S440-11, S440-12 | Current Swagger/Traefik targets are candidates; live convergence and persisted desired pins required. |
| P03 | Real Portainer upgrade and subsequent managed deployment | OPEN | S440-04, S440-06, S440-07, S440-08, S440-12 | Native history retained; attributable WSL upgrade, cold backup and API-down recovery required. |
| P04 | Minimal and two distinct optional resolved selections | PARTIAL | S440-04, S440-06, S440-07, S440-10, S440-12 | Reconcile historical cases; qualify missing exact-current-source selections. |
| P05 | Mandatory foundation and unsupported-combination refusal | PARTIAL | S440-01, S440-04, S440-10, S440-12 | W03 regression acceptance retained; remaining entrypoint/host cases required. |
| P06 | Optional-service add preserves identity, data and credentials | PARTIAL | S440-04, S440-10, S440-12 | Exact WSL preservation and retention evidence remains incomplete. |
| P07 | Routes, access output and verification match persisted selection | PARTIAL | S440-04, S440-10, S440-11, S440-12 | Full-service browser checks are bounded evidence; omitted-service cases remain. |
| P08 | Every mutating entrypoint help, syntax, preview and consent | PARTIAL | S440-01, S440-03, S440-04, S440-05, S440-10, S440-11, S440-12 | Complete public CLI/recovery/checkpoint matrix; no direct-adapter substitute. |
| P09 | No-op, interruption, partial failure and recovery | PARTIAL | S440-03, S440-04, S440-05, S440-08, S440-09, S440-10, S440-12 | Historical product Q15 retained; component and attributable WSL Portainer gaps remain. |
| P10 | Explicit unsupported downgrade/migration rejection | PARTIAL | S440-01, S440-08, S440-09, S440-10, S440-11, S440-12 | No image rollback presented as data restore. |
| P11 | Visible configuration/runtime drift; no false success | PARTIAL | S440-02, S440-03, S440-04, S440-08, S440-09, S440-10, S440-12 | Wrong/mixed tasks, dirty/moved/unknown sources and stale checkpoints require attributable results. |
| P12 | Exact cross-host versions, source, selection and redacted evidence | PARTIAL | S440-01, S440-05, S440-06, S440-07, S440-08, S440-09, S440-10, S440-11, S440-12 | Native and WSL deployments remain separate; historical source bindings preserved. |
| P13 | Architecture, targeted tests and applicable quality/security gates | BLOCKED | S440-02, S440-03, S440-04, S440-05, S440-07, S440-09, S440-11, S440-12 | Main Python/coverage gates pass; actual Sonar security/reliability ratings E remain. |
| P14 | Verified operator documentation and truthful support limits | PARTIAL | S440-01, S440-09, S440-11, S440-12 | Candidate wording corrected in #518; complete example verification/reconciliation pending. |
| P15 | Independent final requirement/architecture/evidence review | OPEN | S440-12 | No independent parent PASS; authoring role reviews do not close the Epic. |

## Explicit LCM requirement inventory

Each bullet/numbered obligation from the five requirement groups has a stable ID.
TO_RECONCILE means S440-01 must supply actual implementation symbols, public CLI
dispatch, dependencies, tests and source-bound system artifacts. It is not a claim
of missing implementation. The matrix may only move to VERIFIED on relevant
executed evidence, not on a planned command. Preserve these IDs when refining.

| ID | Original requirement | Owning slices | State |
|---|---|---|---|
| LCM-01-01 | Inspect the installed TSW release/revision, effective configuration and managed runtime state. | S440-01, S440-05, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-01-02 | Resolve an explicit target release using a defined release source and supported upgrade matrix. | S440-01, S440-05, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-01-03 | Distinguish the TSW product version from upstream component versions and locally built image versions. | S440-01, S440-05, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-01-04 | Validate source and target state, dependency compatibility, host support and required resources before mutation. | S440-01, S440-05, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-01-05 | Upgrade product code/package and locked Python dependencies through the supported installation model. | S440-01, S440-05, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-01-06 | Apply versioned configuration/state migrations in an explicit order. | S440-01, S440-05, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-01-07 | Preserve local overrides, credential-source references, installation identity and persistent service data. | S440-01, S440-05, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-01-08 | Keep runtime credentials out of source-control operations, logs and upgrade evidence. | S440-01, S440-05, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-01-09 | Use a controlled checkout/package switch; do not overwrite an operator's uncommitted changes or perform an implicit reset. | S440-01, S440-05, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-01-10 | Define interruption handling, resumability and recovery for each supported transition. | S440-01, S440-05, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-01-11 | Record the actual resulting version and verify the complete installed service selection. | S440-01, S440-05, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-02-01 | Report installed and desired component versions, available supported targets and compatibility restrictions. | S440-01, S440-05, S440-09, S440-11, S440-12 | TO_RECONCILE |
| LCM-02-02 | Separate upstream versions, image tags and resolved image digests. | S440-01, S440-05, S440-09, S440-11, S440-12 | TO_RECONCILE |
| LCM-02-03 | Support one selected service and an explicitly selected batch of installed services. | S440-01, S440-05, S440-09, S440-11, S440-12 | TO_RECONCILE |
| LCM-02-04 | Resolve updates through an authoritative component catalog and profile support policy. | S440-01, S440-05, S440-09, S440-11, S440-12 | TO_RECONCILE |
| LCM-02-05 | Preview the exact changes, dependency order, restart/availability impact and required migrations. | S440-01, S440-05, S440-09, S440-11, S440-12 | TO_RECONCILE |
| LCM-02-06 | Reuse #297 for supported stack-service image transitions. | S440-01, S440-05, S440-09, S440-11, S440-12 | TO_RECONCILE |
| LCM-02-07 | Verify deployed task-image convergence and authenticated service behavior after an update. | S440-01, S440-05, S440-09, S440-11, S440-12 | TO_RECONCILE |
| LCM-02-08 | Update the persisted desired configuration after a successfully verified transition so later setup/deployment does not silently restore the old image. | S440-01, S440-05, S440-09, S440-11, S440-12 | TO_RECONCILE |
| LCM-02-09 | Represent no-op, unsupported, blocked, failed, partial and recovered outcomes explicitly. | S440-01, S440-05, S440-09, S440-11, S440-12 | TO_RECONCILE |
| LCM-02-10 | Do not update uninstalled or unselected services implicitly. | S440-01, S440-05, S440-09, S440-11, S440-12 | TO_RECONCILE |
| LCM-02-11 | Document stateful-service migration, backup and downgrade restrictions; an image rollback is not a persistent-data restore. | S440-01, S440-05, S440-09, S440-11, S440-12 | TO_RECONCILE |
| LCM-03-01 | Inspect the current Portainer version, deployment mode, persistent state and endpoint connectivity. | S440-01, S440-04, S440-05, S440-06, S440-07, S440-08, S440-11, S440-12 | TO_RECONCILE |
| LCM-03-02 | Define and test at least one supported source-to-target upgrade. | S440-01, S440-04, S440-05, S440-06, S440-07, S440-08, S440-11, S440-12 | TO_RECONCILE |
| LCM-03-03 | Back up the required Portainer state and document compatible recovery boundaries. | S440-01, S440-04, S440-05, S440-06, S440-07, S440-08, S440-11, S440-12 | TO_RECONCILE |
| LCM-03-04 | Preserve administrative access, endpoint registration and managed stack ownership. | S440-01, S440-04, S440-05, S440-06, S440-07, S440-08, S440-11, S440-12 | TO_RECONCILE |
| LCM-03-05 | Verify the Portainer API and authenticated access, then prove that a managed deployment/update still works. | S440-01, S440-04, S440-05, S440-06, S440-07, S440-08, S440-11, S440-12 | TO_RECONCILE |
| LCM-03-06 | Recover without depending exclusively on an unavailable Portainer API. | S440-01, S440-04, S440-05, S440-06, S440-07, S440-08, S440-11, S440-12 | TO_RECONCILE |
| LCM-03-07 | Keep Incus host-package upgrades separate from service-image updates; define their ownership and reject unsupported requests explicitly. | S440-01, S440-04, S440-05, S440-06, S440-07, S440-08, S440-11, S440-12 | TO_RECONCILE |
| LCM-04-01 | Provide a canonical catalog of service IDs with versions, dependencies, resource requirements and profile support. | S440-01, S440-04, S440-06, S440-07, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-04-02 | Let operators select optional services through CLI/configuration and persist the resolved selection. | S440-01, S440-04, S440-06, S440-07, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-04-03 | Keep **Incus/LXC and Portainer mandatory for Classic**; attempts to disable either must fail before mutation with an actionable explanation. | S440-01, S440-04, S440-06, S440-07, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-04-04 | Treat Incus as a host/provider prerequisite and Portainer as a managed foundation; mandatory status does not imply that the installer already provisions the host Incus daemon. | S440-01, S440-04, S440-06, S440-07, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-04-05 | Resolve transitive dependencies deterministically. Show dependencies added to the requested selection and the reason for each. | S440-01, S440-04, S440-06, S440-07, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-04-06 | Document any additional unavoidable dependencies in the current implementation rather than claiming that every remaining service can already be omitted. | S440-01, S440-04, S440-06, S440-07, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-04-07 | Preflight only the resources, credentials, artifacts and capabilities needed for the resolved service set and mandatory foundations. | S440-01, S440-04, S440-06, S440-07, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-04-08 | Install, route, display and verify only the resolved services. | S440-01, S440-04, S440-06, S440-07, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-04-09 | Support a subsequent request to add optional services to an existing installation. | S440-01, S440-04, S440-06, S440-07, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-04-10 | Preview removals separately; deselection must not silently delete deployed services or persistent data. | S440-01, S440-04, S440-06, S440-07, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-04-11 | Use the same persisted selection for setup, reconcile, update and verification. | S440-01, S440-04, S440-06, S440-07, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-04-12 | Do not conflate service selection with runtime/orchestrator selection. | S440-01, S440-04, S440-06, S440-07, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-05-01 | Current-state inspection and supported-transition validation. | S440-01, S440-03, S440-04, S440-05, S440-08, S440-09, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-05-02 | A read-only preview with exact targets and planned changes. | S440-01, S440-03, S440-04, S440-05, S440-08, S440-09, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-05-03 | Explicit live-operation intent through existing consent boundaries. | S440-01, S440-03, S440-04, S440-05, S440-08, S440-09, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-05-04 | Ordered execution with bounded waits and per-stage results. | S440-01, S440-03, S440-04, S440-05, S440-08, S440-09, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-05-05 | Post-operation verification tied to the actual deployed state. | S440-01, S440-03, S440-04, S440-05, S440-08, S440-09, S440-10, S440-11, S440-12 | TO_RECONCILE |
| LCM-05-06 | A documented failure/recovery path and redacted evidence. | S440-01, S440-03, S440-04, S440-05, S440-08, S440-09, S440-10, S440-11, S440-12 | TO_RECONCILE |

## Late additions and overarching obligations

| ID | Requirement/source | Owner and sequencing | Baseline state / gate |
|---|---|---|---|
| A440-01 | Parent final-acceptance order 1: exact Incus 6.0.5 listener fixture, independent support decision, recoverable WSL Portainer Server/Agent 2.45.0→2.45.1 with cold backup, managed update, no-op and API-down recovery | S440-04→05→06→07→08 | OPEN; native fixture history is bounded, WSL attribution and capability admission remain separate |
| A440-02 | Parent order 2: real current-runner single/two-service changes, persistence, no-op, partial failure, recovery and drift; promotion follows evidence | S440-05,09 | OPEN; production targets remain candidates at baseline |
| A440-03 | Parent order 3: retain P01 history, reconcile remaining selection/product/source cases, preserve WSL overrides/data/credentials and retention; run only actual gaps | S440-01,10 | PARTIAL; exact-source and variant reconciliation required |
| A440-04 | Parent order 4: exact source/host/selection/commands/exits before/after evidence, applicable gates, examples, consistent admission wording and independent review | S440-01,05,11,12 | PARTIAL; wording fixed, actual Sonar findings/final review remain |
| G440-01 | Preserve config, local overrides, credential references, installation/service identities and persistent data; no implicit reset, removal, data deletion or secret rotation | All mutating slices | Non-negotiable preservation and negative-case checks |
| G440-02 | Initial Classic only; #297 reuse, existing #313/#314/#318 ownership and contracts; no competing catalog/orchestration model or unrelated runtime expansion | S440-01,04,05,12 | Architecture boundary and owner review |
| G440-03 | Product/package, upstream version, local image/tag and resolved digest remain distinct; real task/authenticated service state establishes success | S440-08,09,10,11 | Exact source-to-target and observed-state evidence |
| G440-04 | Proposed one-token commands in the parent are not shipped promises; use accepted two-token CLI and preserve platform update compatibility | S440-01,05,11 | Inspect actual parser/entrypoint/tests; no invented command claims |
| G440-05 | Scenario-specific live authorization, qualified recoverable targets, source-bound results; missing/stale/simulated evidence is non-pass | All live slices | Separate consent, prerequisite, result and retention states |

## Implementation and verification evidence to fill before completion

For every row record the exact source/path and production owner, actual
prerequisites and their owner, changed code/config/docs, executable command/test,
substituted versus real dependencies, evidence level (CONTRACT/COMPONENT/EXECUTABLE/
SYSTEM as applicable), result/skips/limits, source and host identities and artifact
checksums. Historical references keep their original scope. Final accepted
records belong in `.tiny-swarm/evidence/issue-440/requirement_matrix.md` and the
W09/W10 published reconciliation. Any unmapped or non-pass row blocks parent PASS.
