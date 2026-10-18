# Classic lifecycle contract — LCM-W01 / #441

Contract version: 1. Decision: [lifecycle ADR](../arc42/09_decisions/adr-classic-product-component-lifecycle.adoc).
Inventory baseline: `a43bb7965a0fba4ca4f190f545f459005c653b28` (2026-10-17).
Scope: native Linux/WSL2 → managed Incus/LXC → Docker Engine → Docker Swarm.
**New commands below are specified for W02–W08; W01 does not implement them.**
W02 implements read-only `product version` and `services list`, the manifest and
native component catalog; see [installation state contract](installation-manifest.md).
W03 implements read-only selection previews for `setup run`, `services add` and
`services remove`; see [selection contract](service-selection.md).
W04 implements selective setup/addition; W05 adds read-only `services updates`
and `services update --services <ids> [--to <target-id>] --preview`. See
[component planning](../user_guide/component-updates.md) for actual availability:
the native catalog has baseline references and no qualified upgrade transitions.
W06 implements selected component execution/recovery and committed desired-image
pins through the existing Classic engine; no production transition is newly
qualified. Backup/migration execution and unmapped components remain blocked.
W07 Portainer execution and W08 product upgrades remain future scope.
The [requirement matrix](../evidence/issue-441-requirement-matrix.md) covers every
LCM-01–05 bullet and parent acceptance criterion. Parent implementation stays open.

## 1. Verified behavior and current operator path

Paths below are relative to the repository root and identify implementation authority.

| Surface | Verified behavior | Boundary / source |
|---|---|---|
| `./prepare_linux.sh` | Separate guarded prerequisite preparation; readiness is not service acceptance | `application/services/native_preparation.py`, `incus_preparation.py`, `network_preparation.py` and their infrastructure adapters under `src/tiny_swarm_world`; [bootstrap contract](bootstrap.md) |
| `./install.sh` | Dependency-light wrapper selects simple installer; ordinary native/WSL installation reconciles after preparation | `install.sh`, `simple_installer.py`, `application/services/installation.py`, `infrastructure/adapters/installation/` |
| Installer `--preflight`, `--dry-run` | Validate without installation mutation; dry-run describes reconciliation, not an exact release or selection transition | `InstallationService.run`; installer presentation/configuration adapters |
| Installer reset | Explicit deprecated WSL `--confirm-reset`; native rejects it; separate exact reset intent and live consent | `_validate_install_mode`, [accepted reconciliation ADR](../arc42/09_decisions/adr-wsl-install-reconciliation.adoc) |
| CLI help / `--list-workflows` | Global parser plus two-token namespaces; `--service-profile default\|service-access` plus W03 selection preview options | `infrastructure/adapters/cli/parser.py`, `registry.py` |
| `setup run` | Fixed aggregate preflight, host, platform, Docker/Swarm, exposure, artifact, deployment and validation phases | `infrastructure/composition_setup.py`, `application/services/setup/workflow.py` |
| `platform reconcile` | Ensures configured provider nodes; does not update TSW code or all stack images | `application/services/platform/lifecycle.py`, `platform/workflow/mutating.py` |
| `platform update` | One configured stack/service A→B; static preview; runtime source guard, target task-image convergence, stable rollout and verified no-op | `application/services/platform/workflow/update.py`, `domain/update/`, `application/ports/update/` |
| `platform update --recover` | Uses protected original image transition, keeps recovery direction across retries; bounded observed source convergence | Same update workflow; `infrastructure/adapters/update/json_state_store.py` |
| Update desired state | Image override is invocation-local; legacy update/recovery does **not** persist the target into desired configuration | `infrastructure/composition_setup.py:build_classic_update_workflow`; [#297 ADR](../arc42/09_decisions/adr-classic-update-contract.adoc) |
| `deployment bootstrap` | Ensures Portainer stack through Swarm, admin access and endpoint, plus Nexus bootstrap; subsequent stacks use Portainer | `infrastructure/composition_deployment.py`; `application/services/deployment/ensure_portainer_{stack,admin_access,endpoint}.py` |
| Portainer upgrade | Bootstrap ensure is not qualified version migration, backup or recovery; generic image transition does not qualify this gateway | Separate W07 adapter required |
| `platform verify`, `deployment verify` | Observations/readiness have defined scopes; not complete authenticated lifecycle acceptance on their own | Platform/deployment workflows and existing Classic suites |

W02 adds `product version` and `services list`; W03 adds read-only
`setup run --preview` and `services add/remove --services <ids> --preview`.
Top-level `version`/`update` remain absent. Existing `platform update --preview`
checks configuration without runtime observation; its historical option and
consent behavior remains unchanged. Live setup without selection options still
uses fixed aggregate phases; W04 owns selective execution.

Safe current examples (activate the prepared environment first):

```bash
tiny-swarm-world --help
tiny-swarm-world --list-workflows
tiny-swarm-world platform update --stack jenkins --service jenkins \
  --from-image 127.0.0.1:13500/jenkins:0.2.0 \
  --to-image 127.0.0.1:13500/jenkins:0.3.0 --preview --json
```

The image references illustrate syntax, not a newly qualified transition.
Apply uses `--live` and interactive confirmation, or `--live --approve-live`.
`--approve-live` alone is insufficient. Recovery uses the same stack/service
with `--recover` instead of image arguments and the same live-consent boundary.
Do not rerun setup blindly after an image update: reconcile desired-image drift
explicitly because legacy updates leave configuration unchanged.

## 2. Installation, source and model authorities

| Concept | Authority and required representation |
|---|---|
| Current product | `pyproject.toml` package version (`0.2.0` at baseline), exact checkout SHA and dirty status; package version alone cannot identify installed code |
| Supported installation model | Prepared Linux-native Git checkout and checkout-local Python environment with `requirements.lock`; Linux/WSL only. Current install still needs Git metadata for secret-ignore proof. Archives/wheel-only installs are not currently equivalent supported models |
| Product upgrade source (W08) | Explicit published release from `https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World` (its GitHub release metadata and Git refs), release ID pinned to immutable commit and lock/content identity, admitted by a versioned source→target/host/schema matrix. Ref moved, source missing, dirty checkout or unknown transition blocks before mutation; never `git pull`/reset over local edits |
| Upgrade switching (W08) | Stage a separate verified checkout/environment; preserve old code/env and protected local state outside version-controlled source; controlled switch only after preflight. No secret values, tokens or credential fingerprints in Git operations/evidence |
| Product release | TSW release identity plus revision, dependency lock and migration schema; independent of a Jenkins release or container tag |
| Upstream component version | Vendor software version, e.g. Jenkins upstream base; not the local Jenkins `0.2.0` image build version |
| Image tag | Registry reference, potentially mutable; record separately from vendor version and TSW build/version |
| Image digest | Immutable resolved content identity for applicable platform/manifest; record resolution and deployed task identity, never infer it from the tag |
| Native service assets | `infra/config/compose/<stack>` packaging and Dockerfiles; `ContainerImageContract` owns artifact/build details; `ServiceStackContract` owns current deployment/readiness membership |
| Logical catalog (#318 / W02) | One versioned service identity/version/dependency/lifecycle contract, incrementally implemented for Classic by W02. References native assets; includes capabilities/profile support, resources, migration/backup policy and supported targets. No copied second logical service schema |
| Installation instance (W02) | Product/revision/install model, lock/schema identities, requested/resolved service IDs with dependency reasons, credential **references**, effective overrides, desired component/tag/digest/build identities, observed state and protected operation/checkpoint references |
| Preflight / phase plan | Current `SetupManifest` is a fixed checklist, not persisted installation state. `default_installation_plan()` is typed executable phase authority; `infra/config/installation-plan.yaml` says its parser is future work, so YAML alone is not execution authority |

#318 owns shared semantics; #314 owns capability vocabulary and future profile
selection. #313's decomposition remains authoritative. W02 schema migrations
must preserve existing configurations and define source/generated asset ownership
and drift checks. W03 resolves selection; W04 integrates it into current stages;
W05/W06 plan/execute component changes; W07 owns Portainer; W08 owns product
switching. No generic engine or runtime-specific domain imports are needed.
The #294 historical Classic baseline, #427 native installation integration and
#251 product vision remain separate authorities; #319 owns cross-profile release
qualification when additional profiles become supported. W01 replaces none of them.

## 3. Canonical CLI and operation semantics (future contract)

The executable is `tiny-swarm-world`; all commands retain namespace/action form.
This finalizes the parent issue's explicitly provisional spelling.

| Command | Contract and owner |
|---|---|
| `product version [--json]` | Read installed release/revision, install model, lock/schema, effective config provenance, observed runtime and drift; redact configuration values; W02/W08 |
| `product upgrade --to <release> --preview` | Resolve exact official release, validate source/target/host/resources, show code/dependency/config/state/runtime delta, migrations and recovery; W08 |
| `product upgrade --to <release> --live --approve-live` | Explicit supported product switch, full persisted-selection verification and resulting release commit; W08 |
| `services list [--json]` | Canonical service IDs, installed/desired/observed versions, dependencies/resources/support and drift, distinguish uninstalled; W02/W05 |
| `services updates [--services <ids>] [--json]` | Read-only discovery of catalog-supported targets/restrictions; default installed set only; no mutation or automatic selection of new services; W05 |
| `services update --services <ids> [--to <component-version>] --preview` | One service or explicit selected batch; resolve supported catalog target, immutable image identities, dependency order, restart impact and migration/backup gates; W05 |
| `services update --services <ids> [--to <component-version>] --live --approve-live` | Apply reviewed changes only to selected installed services; reuse #297; special Portainer adapter if selected; W06/W07 |
| `setup run --services <ids> --preview` | Initial requested optional set plus foundations and dependency closure; show reasons, resources, routes/artifacts/credentials required; W03/W04 |
| `setup run --services <ids> --live --approve-live` | Install/verify exact resolved selection and persist it; existing installation uses its persisted set, rejects implicit removal and directs additions to `services add`; W04 |
| `setup run --minimal --preview` or `--live --approve-live` | Initial foundations plus disclosed unavoidable dependency closure; rejects conflicting selection/preset flags; W03/W04 |
| `services add --services <ids> --preview` or `--live --approve-live` | Union with existing persisted selection; add transitive prerequisites; preserve existing identity/data/credentials; W03/W04 |
| `services remove --services <ids> --preview` | Removal-impact inspection only, including reverse dependencies and retained data. No deselection deletion. Apply unsupported in initial delivery; separate accepted removal policy required |
| `platform reconcile` | Retain current platform-node scope. Whole-selection reconciliation uses selection-aware setup; never report a product upgrade |
| `platform update ... [--preview]` / `platform update --recover ...` | Retain #297 syntax and behavior without deprecation/removal. Explicit compatibility layer above it adds catalog selection/persistence; no reinterpretation as product upgrade |

For planned catalog/product operations, use the same command with either
`--resume --operation <id>` or `--recover --operation <id>` instead of new
target/selection arguments. These modes are mutually exclusive and support
`--preview` or existing live-consent flags. Resume retains the recorded forward
plan; recover requests its recorded supported recovery direction and never
toggles it on repeated calls. Refuse absent, foreign, stale or unsupported
operation records before mutation. W06/W07/W08 own these modes for their
respective operations; unsupported reverse migrations remain blocked. Legacy
`platform update --recover --stack ... --service ...` retains its original syntax.

`<ids>` is a comma-separated set of canonical lowercase service IDs; reject empty
entries, unknown IDs, wildcards and duplicate IDs. Normalize deterministic order.
`--services` on mutations is explicit; no implicit all-services batch.
`--to` on component update names a catalog target ID (not an arbitrary tag) and
requires exactly one selected service; batches resolve
one compatible catalog target per selected service and preview all of them.
Portainer/incus disable/remove requests fail with foundation-specific remediation;
`incus` host-package update requests are unsupported and identify the host owner.
Any other uninstalled service update or unsupported capability/host/version fails
before mutation. Missing credentials/resources/artifacts are checked only for
the resolved set and its foundations/dependencies.

Existing `--service-profile default|service-access` remains a compatibility preset,
not a runtime selector. Without explicit selection on a new installation it
expands the preset; on an existing installation persisted selection is authoritative.
If explicit selection is supplied, supplying an explicit conflicting preset fails;
an implicit parser default must not silently override selection. W03/W04 must
track whether a preset was explicitly supplied. Do not infer free omission from
current fixed profile support. An explicit empty selection cannot be expressed
as an empty comma list: reserve `setup run --minimal` for the foundations plus
unavoidable dependency closure; it is mutually exclusive with `--services` and
explicit presets and remains a future W03/W04 option.

For new operations, preview is mutually exclusive with live/approval flags; it
performs no writes to installation, desired configuration, secrets, recovery
records or runtime. Read-only registry/runtime queries use bounded ports; unavailable
observations produce an explicit unverified/blocked plan, not false qualification.
Preview prints current/target identities, resolved set/dependency reasons, stages,
availability impact, required backups, migration/recovery limits and drift.
Apply revalidates those observations and targets; source/plan drift blocks execution.
Without `--live`, a mutation request fails before side effects. With `--live`,
reuse existing confirmation or explicit `--approve-live`; preview never prompts.
Help must work without constructing mutating services. Unknown flags/IDs,
conflicting modes and missing targets return argument error (exit 2).

Reuse existing typed operation/verification models. Distinguish completed,
verified no-op, unsupported, blocked/refused, failed, partial and recovered
results without collapsing uncertain state to success. Exit 0 requires a valid
read/preview or verified successful/no-op/recovered operation; blocked, failed
and partial execution return nonzero (1), argument/consent refusal returns 2.
JSON includes per-stage completed/pending/uncertain outcomes, actual identities,
desired/observed drift and recovery references. Bounded waits apply to all
observations; mutation retries are operator initiated after inspection. Do not
implicitly retry or compensate shared resources.

## 4. Service and dependency inventory

This is an inventory of current coupling, **not a second machine-readable catalog**.
All listed stack assets are under `infra/config/compose`; inspect contracts and
composition with them. No row asserts a new optionality or live qualification.

| ID / layer | Current dependency and consequence for selection |
|---|---|
| `incus` / managed LXC | Mandatory Classic host/provider foundation. Prepared daemon, access groups, storage/network/profile/capacity are prerequisites; installer is not implicit host provisioning. `lxc_native` with Incus remains current provider |
| Docker Engine / Swarm | Runtime inside managed nodes, manager/worker readiness, manager socket and cluster/overlay capabilities; not optional application services or Incus package updates |
| Shared network | Every current stack uses external `service_access_link`; ownership/availability must precede stacks; no automatic shared-network deletion |
| `portainer` | Mandatory managed foundation; Portainer server + matching agent, persistent Portainer data, admin-password secret, endpoint registration and manager Docker socket. Bootstrap uses Swarm before Portainer API can manage other stacks |
| `traefik` | Current common ingress/exposure stage, TLS certificate/key and GUI auth external secrets plus routed service labels. Required for current routed operator experience even though not declared a mandatory product foundation; omission is not yet supported by fixed setup |
| `nexus` | Persistent artifact server + registry. Artifact bootstrap/readiness runs unconditionally today. Locally built Jenkins/service-access images default to `127.0.0.1:13500`; removing Nexus requires eliminating these dependencies first, not just omitting its stack |
| `jenkins` | Custom local-registry build, persistent home, configuration/JCasC/assets and credentials. service-access setup resolves effective Jenkins credentials via Infisical snapshot; not a free-standing omission-safe pipeline today |
| `infisical` | service-access profile adds secret lifecycle/sync/bootstrap. Requires `infisical-db` PostgreSQL, `infisical-redis`, persistent stores and protected encryption/authentication inputs; default profile omits this bundle, not all credential requirements |
| `sonarqube` | SonarQube plus `sonar_db` PostgreSQL and persistent data, configured kernel/resource limits and credential initialization; database cannot be deselected independently |
| `pulsar` | Pulsar broker/standalone storage, Pulsar Manager and one-shot `pulsar-manager-bootstrap` Python image/admin initialization. Readiness contract lists two long-running services; one-shot completion is a separate prerequisite, not a third continuously healthy task |
| `swagger` | Swagger Editor/UI, digest-pinned apisprout API and NGINX aggregator; OpenAPI/NGINX assets transferred before deployment. Internal services are bundle dependencies, not independently selectable product services |
| `service-access` | Dashboard + NGINX custom local-registry images and generated configuration/static links, protected access metadata. Requires selection-aware links/routes and artifact generation before arbitrary omissions are safe. Vaultwarden is not a service in the current stack contract |
| Host/external prerequisites | Supported Ubuntu/Python, locked dependency acquisition, network/registry access, capacity, credentials and certificates, and WSL bridge when applicable. They are preflight capabilities, not new service IDs |

Current `default` includes Portainer, Traefik, Nexus, Jenkins, Pulsar, SonarQube
and Swagger. `service-access` adds Infisical and Service Access, and is the
composition default. Readiness membership, artifact inventory, port allocation,
setup manifest and phase plan are fixed lists today. W03/W04 must make all of
them selection-aware, including routes, access output and final verification.
Minimal must expose its actual dependency closure; never claim Incus+Portainer
alone works while unconditional artifact/routing/secret stages remain.

## 5. Migration, persistence and recovery limits

Product preflight validates install model, host/resources, exact source/target,
lock/config/state schemas, catalog compatibility and backups. Reject dirty
source, unknown transition, unsupported downgrade, insufficient capacity or
unavailable credentials before switch. Preserve overrides, credential references,
installation/node/service identities and service data. Ordered versioned migrations
checkpoint each stage. Interruption leaves recorded old/new code and environment,
completed/pending/uncertain migrations and exact recovery instructions; resume
requires unchanged installation/plan/source identity and fresh consent. Reverse
migrations are never assumed; retain previous code/env but do not claim whole-host
or database rollback. Verify actual installed product revision and every resolved
service after switching before recording completion.

Components qualify runtime source before updating, back up state where required,
verify desired service plus active task-image convergence and authenticated
behavior, then persist desired target/digest. If persistence fails after deployment,
report partial with observed delta and drift, never success; recovery must address
both runtime and desired state. Batch failure stops dependent work, records each
completed/failed/pending service and permits inspection-led resume of the same plan.
Do not update unselected or uninstalled services. A healthy old task is insufficient.

Portainer W07 must specify at least one real source→target pair and deployment
mode, consistent backup of required persistent state, compatible restore, admin
and endpoint preservation, authenticated API verification and a subsequent
managed deploy/update. Recovery must use Incus/manager/Swarm access when the
Portainer API is down. W01 admits no pair. Incus package lifecycle remains host
preparation/operator ownership; it is not implemented by `services update`.

Deselection retains deployments/data and previews dependent impact separately.
No silent removal, data deletion, credential rotation or destructive reset is a
recovery action. Stateful image downgrade without compatible data migration/backup
is unsupported. Legacy recovery restores image convergence only; it is neither
data restoration nor whole-selection/product rollback.

## 6. Classic support and qualification matrix

| Host/profile | Existing local contract | W01 qualification / future admission |
|---|---|---|
| Native Ubuntu 24.04 x86_64 / Classic | Supported preparation/install code path; fixed default/service-access lists | No new live result; W09 must name exact host/component/product versions and transitions |
| Native Ubuntu 26.04 x86_64 / Classic | Same code path; #427 records clean-install evidence, later bootstrap W09 has a narrower existing-host scope | Historical campaigns retain their own SHA/scope; no new clean/minimal/upgrade claim |
| Windows 11 + Ubuntu WSL2 / Classic | Product runs inside Linux; existing guarded host/bridge preparation | Ordinary Windows Apply guard and bootstrap qualification limits remain; W09 needs actual admitted source/target and consent, not assumed parity |
| Minimal and two optional selections / either host family | Planned W03/W04 contracts | Unqualified until fresh installs, repeat runs, add/preservation, omission-aware access/routes and failure/recovery pass W09 |
| Product release upgrade / either family | No implemented transition | W08 defines matrix; W09 qualifies at least one actual source→target transition |
| Component batch / Portainer upgrade | #297 single-image engine is reusable; batch/persistence/gateway upgrade are separate | W06/W07 implementation plus exact W09 qualification required |
| Other Linux distributions/architectures, Podman, Kubernetes, multi-host, HA | Not admitted by this contract | Explicitly unsupported/deferred; no implied capability parity |

## 7. Acceptance scenarios and evidence ownership

These are executable-scenario specifications for downstream work, not passing
tests. Parent requirement IDs refer to the linked matrix. Existing test modules
are regression evidence for current behavior only. W09 consumes per-slice results
and records both native and WSL2 results independently; skipped/missing/stale/
inconclusive required evidence remains non-pass.

| Scenario ID | Given / when / expected result | Unit / integration / live plan; owner |
|---|---|---|
| LCM-S01 | Installed product and runtime drift; inspect reports revision/lock/schema/config provenance, desired/observed identities without secrets | W02/W08 manifest/parser/port tests; W09 actual inspected before/after state; LCM-01-01,03,07,08,11 |
| LCM-S02 | Known official release and clean checkout; preview shows exact code/dependency/migration deltas and writes nothing; dirty/moved/unknown source or incompatible host/resources rejects | W08 source adapter/migration mocks and temporary-checkout integration; W09 valid/invalid source→target; LCM-01-02,04,05,06,09 |
| LCM-S03 | Supported product A→B; apply preserves identities/overrides/data/credentials, verifies whole selection, records actual B; repeat no-op; interruption/resume and reverse limits explicit | W08 staged-switch and checkpoint failure injection; W09 actual upgrade/repeat/recovery; LCM-01-05–11 |
| LCM-S04 | Installed selected component(s); discovery separates upstream/build/tag/digest and restrictions; preview pins exact targets/order/restarts/migrations and no mutation | W02/W05 catalog/parser/registry adapter tests; W09 discovery/preview; LCM-02-01–05 |
| LCM-S05 | Runtime A→B; old/mixed/paused/failed/unobservable tasks cannot pass; convergence plus auth allows desired persistence; repeat no-op; persistence failure reports partial drift | Existing ClassicUpdateWorkflow tests plus W06 persistence/observation integration and W09 actual deployment/auth/no-op; LCM-02-06–09 |
| LCM-S06 | Selected batch, uninstalled/unknown/unselected services or failure midway; reject invalid targets, stop dependents, preserve unrelated state and recover from stable original plan | W05/W06 parser/batch/failed-save/retry tests; W09 partial batch and recovery; LCM-02-09–11 |
| LCM-S07 | Portainer supported A→B with backup; preserve admin/endpoints/stack ownership; prove subsequent deployment; API loss recovers via manager; Incus update rejected | Existing Portainer bootstrap tests + W07 backup/restore/adapter tests; W09 actual gateway upgrade and API-down recovery; LCM-03-01–07 |
| LCM-S08 | Minimal or two distinct optional selections; resolve mandatory/transitive dependencies deterministically, explain additions; reject foundation removal, cycles/unsupported capability; same resolved set persisted | W02/W03 catalog/selection tests; W04 mocked setup/routes/artifacts/credential/resource filtering; W09 fresh minimal + two selections; LCM-04-01–08 |
| LCM-S09 | Existing installation; add optional service, preserve identities/data/effective credentials; reconcile/update/verify use same persisted selection; omitted services absent from routes/access/failure output | W03/W04 selection persistence and full mocked pipeline; W09 add/preservation and omission-aware observations; LCM-04-08,09,11,12 |
| LCM-S10 | Deselection/removal or stateful downgrade; removal preview shows reverse dependencies and retained data; unsupported apply/downgrade fails before mutation | W03/W05/W06 negative parser/plan tests; W09 preservation and rejected mutation checks; LCM-02-11, LCM-04-03,10 |
| LCM-S11 | Every mutation: help, malformed/conflicting input, preview, missing consent, changed source, failed/partial/recovered outcomes; no mutation without matching validated intent; bounded waits and redacted evidence | Existing CLI/update/setup regressions + new W04/W06/W07/W08 CLI integration; W09 each mutating entrypoint incl. repeat and interruption; LCM-05-01–06 |
| LCM-S12 | All accepted scenarios; exact evidence is reviewed independently and operator guidance matches supported behavior | W09 host matrix and W10 requirement/architecture/test-evidence completion audit; all parent acceptance criteria |

W01 checks existing CLI help, invalid input, preview consent bypass, runtime
no-op/convergence/failure/recovery and Portainer bootstrap with existing mocks.
New-command unit/integration tests belong to the implementing packages; running
unknown future commands now cannot qualify them. W01 does not change product
code or add tests that merely assert prose.

For each future live claim record exact committed SHA, source/target product and
upstream/build/tag/resolved digest identities, host/version/profile, requested and
resolved selection, commands, timestamps, exit codes, redacted before/after state,
auth/convergence/preservation observations and backup/recovery references. Never
record passwords, tokens, cookies, private keys or credential fingerprints.

Applicability for this documentation package: local static checks and existing
mocked regressions are APPLICABLE_LOCAL. Live install/browser/upgrade checks are
NOT_APPLICABLE / LIVE_NOT_APPLICABLE to W01 delivery; downstream qualification
is required and not executed here. External quality is
EXTERNAL_GATE_NOT_APPLICABLE for this local documentation change. W09 cannot
reuse these labels to skip required host qualification. Follow the canonical
[verification-state policy](../process/verification-state-policy.md).
