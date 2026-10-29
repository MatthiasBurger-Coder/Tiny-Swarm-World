# Component discovery and update planning

Classic component inspection and planning are read-only on Linux and WSL2:

```bash
tiny-swarm-world services list --json
tiny-swarm-world services updates --json
tiny-swarm-world services updates --services swagger,traefik --json
tiny-swarm-world services update --services swagger,traefik --preview --json
tiny-swarm-world services update --services swagger --to swagger-ui-5-32-7 --preview --json
```

When an existing stack is updated through Portainer, the update request does
not prune services omitted from the submitted stack definition. Such services
can remain. Explicit service removal and ownership verification require
separate reviewed workflows; this setting does not prove full convergence.

Run these commands from the prepared environment. Alternatively use
`PYTHONPATH=src python3 -m tiny_swarm_world` in place of `tiny-swarm-world`.
`services updates` defaults to the persisted installed selection. Update preview
requires an explicit nonempty comma-separated selection; it never adds services
or updates dependencies implicitly. `--to` selects a catalog **target ID** for one
service; batches resolve their catalog targets individually. Unknown IDs,
duplicates, wildcards, empty entries and conflicting options fail. An uninstalled
service must first be added explicitly through the selective setup workflow.

The catalog records two proposed stateless source-to-target policies as
non-executable candidates pending current-source live qualification:
Traefik 3.7.4 → 3.7.5 (`traefik-3-7-5`) and Swagger UI 5.32.6 → 5.32.7
(`swagger-ui-5-32-7`). They pin Linux/amd64 child manifests for Classic on native
Linux/WSL2. Historical bounded live results for these transitions used an earlier
runner source; they do not qualify the current runner source. See the
[W09 qualification](../evidence/lcm-w09-qualification.md) and
[source-hash applicability](../evidence/lcm-w09-transition-proposal.md).
Broader W09 acceptance remains open. Swagger's editor/API/NGINX members retain exact immutable identities. All members must match
the complete immutable source bundle in desired and observed installation state;
ordinary tag-only baseline state is insufficient and is not silently rewritten.
Inspect actual runtime and use the existing explicit inventory/adoption boundary;
never fill in observations from catalog defaults. See the
[reviewed transition pins](../evidence/lcm-w09-transition-proposal.md).

Other generic services remain unadmitted. Portainer has a dedicated W07
transition described below. As a negative control,
`services update --services jenkins,nexus --preview` returns a blocked plan
(exit 1) because those services have no admitted targets. `native-baseline`
identifies packaging metadata, not an approved upgrade or downgrade. Upstream
`latest` is never promoted automatically.
Any additional admitted transition must provide complete immutable source/target
bundle identities, compatible hosts/presets, explicit migration/backup policy,
availability impact and recovery limits in the existing component catalog.

Discovery separates `installed` (recorded observations) from `desired`, and
separates upstream version, local build identity, image repository, tag and
digest. Null values mean unknown, never inferred from another field. For example,
the local Jenkins build tag `0.2.0` does not establish its upstream version.
The native catalog currently leaves upstream versions and unresolved digests
unknown when its image contracts do not provide them.

These commands use local authoritative catalog assets and the installation
manifest. They perform no registry/release lookup or runtime probe, work offline,
and report `metadata_status` / `observation_source` accordingly. Recorded
observations may be stale. Missing observations, unresolved identities and drift
are visible; unavailable/corrupt native assets or installation state block the
operation rather than yielding an empty successful result. A missing manifest
requires explicit inventory/adoption; directory presence is not installation proof.

Preview reports deterministic dependency order for selected services, each
component's desired/observed/target identity and drift, direct dependencies and
installed dependents, downtime/restart impact, backup requirements, migrations and
recovery restrictions. A qualified target requires a digest for **every** image in
the service bundle. Unsupported source versions, unqualified downgrades, missing
source observations, drift, incompatible hosts/presets and ambiguous targets fail
before mutation. Empty migration lists on unsupported plans do not qualify a
transition. Image rollback is not a persistent-data restore.

Per-service outcomes are `planned`, `no_op`, `unsupported`, `blocked` or
`dedicated_upgrade`. The batch is blocked if any selected service is not admitted.
A `no_op` requires matching recorded desired and observed immutable target
identities; it makes no live-convergence claim. Execution must revalidate current
runtime state. Valid discovery/preview exits 0; blocked/uninstalled/unsupported
requests exit 1; malformed arguments or unknown service IDs exit 2.

Portainer remains a mandatory management foundation and is classified for its
dedicated W07 upgrade/backup/recovery adapter. Generic Incus host-package upgrades
are refused and remain the host operator's responsibility. Neither foundation is
removed or implicitly changed by planning.

`services update --preview` is read-only. The W06 execution and recovery contract
is described below; W07 owns Portainer execution and W09 owns cross-host live
qualification. The existing `platform update` / `platform update --recover`
commands retain their #297 compatibility contract and do not themselves persist
installation desired pins. Use catalog-admitted component updates for persisted
configuration. Legacy image-update success does not qualify a catalog transition.

See the [lifecycle contract](../contracts/lifecycle.md),
[installation state](../contracts/installation-manifest.md) and
[selective setup](selective-setup.md) for related boundaries.

## Execution and recovery (W06)

The component executor supports explicit live apply and recovery through the
existing Classic image-update adapters. Jenkins/Nexus examples below still fail
admission; the only generic policies currently admitted are the pinned Swagger
and Traefik transitions above. Synthetic test policies are not live qualification.
There is no arbitrary image/tag execution escape hatch.

For an installation with independently verified complete source pins, preview
the fixed single or selected batch transition:

```bash
tiny-swarm-world services update --services swagger --to swagger-ui-5-32-7 --preview --json
tiny-swarm-world services update --services swagger,traefik --preview --json
```

Apply retains `--live --approve-live` or existing interactive consent; recovery
uses the original selection with `--recover` and no `--to`. Swagger and Traefik
must already be installed for the batch. No foundation/dependency is updated
implicitly. Only Swagger UI and Traefik image pins change; retained Swagger members
are freshly observed and have no separate image transition scheduled. The existing
deployment workflow may reapply the whole stack; actual sibling task preservation
or restarts must be observed during W09, not inferred from mocked transition calls.
All four Swagger image variables use
the same existing Compose/artifact/desired-pin path:
`TSW_SWAGGER_EDITOR_IMAGE`, `TSW_SWAGGER_UI_IMAGE`, `TSW_SWAGGER_API_IMAGE`,
`TSW_SWAGGER_NGINX_IMAGE`. Their installation defaults remain unchanged.

These stateless policies perform no data/schema migration. Preserve mounted
OpenAPI/configuration, TLS/secrets, identities and credential sources, and retain
a verified recoverable host baseline. Routing/UI may be unavailable during the
bounded restart. Recovery restores only the original pinned images; it does not
restore persistent data. Live evidence must include authenticated Traefik dashboard,
TLS/routing, Swagger OpenAPI/configuration/API behavior and authenticated Portainer
stack ownership, in addition to actual service/task digest convergence.

```bash
tiny-swarm-world services update --services jenkins,nexus --preview --json
tiny-swarm-world services update --services jenkins,nexus --live --approve-live --json
# Repeat the original selection to resume a partial/interrupted apply.
tiny-swarm-world services update --services jenkins,nexus --live --approve-live --json
# Inspect the original reverse image transition before recovery.
tiny-swarm-world services update --services jenkins,nexus --recover --preview --json
tiny-swarm-world services update --services jenkins,nexus --recover --live --approve-live --json
```

`--live` uses the existing interactive confirmation or `--approve-live` boundary.
Without accepted consent no runtime adapter is constructed. Recovery requires
the original complete service selection and does not accept `--to`. Preview and
discovery remain read-only. Generic Portainer/Incus updates, missing Classic image
mappings, unqualified targets, and transitions requiring backup or migration
execution fail before runtime mutation. Backup/migration execution requires a
qualified adapter; acknowledging a backup flag is not backup proof.

The executor records the original installation, selected dependency order,
source/target identities and per-component stage in
`.tiny-swarm-world/installation/component-update.json` before any runtime apply.
A nonblocking lock prevents concurrent component batches. It delegates each
image transition to the existing bounded Classic observer/deployment workflow:
30 convergence observations by default, 2 seconds between polls and a 10-second
per-observation timeout. The deployment workflow retains its existing bounds.
A successful exit or a healthy task using the old image does not prove success.

Stages progress through `applying`, `runtime_verified`, and `committed`. Failure
stops later stages; `failed` or `partial` exits 1 and is never complete success.
After verified task-image convergence, a compare-and-swap manifest write commits
the desired image pin and qualified identity. The pin is consumed by later setup,
artifact preparation and actual stack deployment, including sibling images.
Conflicting environment image overrides fail instead of silently restoring an
old version. Other configuration and credential inputs retain existing behavior.

If runtime converges but the configuration/journal write is interrupted, preserve
both state files and rerun the **same selection**. Runtime is inspected again and
an already converged image is not redeployed. Setup and ordinary deployment refuse
an unfinished journal. Unrelated manifest changes block resume for inspection.
Mixed, failed or drifted rollouts may require recovery rather than forward retry;
neither path accepts images outside the original source/target transition.

Recovery runs in reverse component order and commits verified original desired
images. Original transition metadata is retained across retries and repeated
recovery; an already restored service is inspected without redeployment. Recovery
restores images only: **image rollback is not persistent-data restore**. No data
reset, service removal, credential rotation, secret bootstrap or unrelated-stack
deployment is introduced. Once recovery starts, finish recovery before requesting
a new transition. A new target must be previewed/admitted explicitly.

Verification for W06 is local unit/mock and deployment-input evidence. Actual
service authentication/data preservation and native Linux/WSL2 qualification
remain W09 responsibilities; no live success follows from these tests.

## Portainer management-gateway upgrade (W07)

Portainer uses a dedicated adapter through the same operator command:

```bash
tiny-swarm-world services updates --services portainer --json
tiny-swarm-world services update --services portainer --to portainer-ce-2.45.1 --preview --json
tiny-swarm-world services update --services portainer --to portainer-ce-2.45.1 --live --approve-live --json
tiny-swarm-world services update --services portainer --recover --preview --json
tiny-swarm-world services update --services portainer --recover --live --approve-live --json
```

The implemented adapter transition is **CE Server and Agent 2.45.0 → 2.45.1**,
using the immutable image-index digests in `domain/lifecycle/portainer_upgrade.py`.
Those digests were resolved from the official Docker Hub repositories on
2026-10-18. Native Linux live evidence verifies the bounded 2.45.0→2.45.1
upgrade. WSL Q12 candidate records report the same transition and repeat, but
R46/R47 artifact reviews found the initial operation lacks unique invocation,
exit, time and source identity; it remains PARTIAL. WSL Q13 reports recovery,
but its stage attribution remains incomplete. WSL LIVE-4 is open. The wider W09
acceptance is still open, and the historical W07 post-mutation failure remains
a non-pass with unverified cause. See the [W07 verification and W09 handoff](../process/issue-447-completion.md)
and [W09 qualification](../evidence/lcm-w09-qualification.md) for exact
evidence, limits and unresolved checks. The isolated native Q12 run also verifies
the subsequent authenticated managed-stack update and Running task readiness;
WSL LIVE-4 remains open because its attempt did not reach the adapter update.
No later version is inferred to be supported.
See the [upstream releases](https://github.com/portainer/portainer/releases),
[Swarm update guidance](https://docs.portainer.io/start/upgrade/swarm) and
[rollback guidance](https://docs.portainer.io/faqs/upgrading/how-can-i-roll-back-to-a-previous-version-of-portainer).

Admission requires an adopted Classic manifest, the existing administrator
credential in `TSW_PORTAINER_ADMIN_PASSWORD`, a reachable authenticated API,
connected registered Swarm endpoints, one manager, the replicated server constrained
to that manager, global agents, and a writable default local Docker volume for
`/data`. Bind-mounted/remote/non-default Docker-root volumes, BE, standalone,
multi-manager placement changes, downgrades and other migrations are unsupported.
The source and target server/agent images must already be cached on the manager;
prepare images through the existing artifact workflow before apply. Worker image
availability must also be arranged by the operator; a failed worker rollout is
not success and requires the documented recovery path.

At least one installed optional service must already be a Portainer-owned Swarm
stack on the local manager's Swarm. Admission checks its saved definition and
environment before shutdown. A foundations-only installation without such a stack
is blocked for this transition because it cannot supply a meaningful deployment
proof. This is an explicit supported-scope limit.

Preview reads local manifest/catalog/checkpoint state only, and writes no files.
It describes live preconditions rather than claiming that they passed. Actual
apply rechecks mode, identities, version, data binding, endpoint connectivity,
ownership and prerequisites. Select Portainer alone; batches containing Portainer
remain blocked by the generic planner. Incus package upgrades remain unsupported.

Apply takes a cold tar snapshot of the entire existing `/data` volume after
scaling the server to zero and confirming that its container has stopped. Backup
storage capacity is checked first. The private archive lives on the managed
manager under `/var/lib/tiny-swarm-world/portainer-backups/<operation-id>/state.tar`.
It contains credential-bearing state: protect it, copy it to protected offline
storage where required, and never attach it to issues or commit it. The adapter
records only its checksum and redacted ownership/endpoint fingerprints in
`.tiny-swarm-world/installation/portainer-upgrade.json` (mode 0600).

Only a verified backup permits target image mutation. Agent and server images are
changed through the existing manager-shell runtime boundary, without recreating
the Swarm, changing credentials or re-registering endpoints. Every expected running
task must converge to the supported digest. After authentication and identity,
endpoint and stack-ownership checks, the adapter reapplies one existing managed
Swarm stack using its stored definition/environment with prune and image-pull
requests disabled. A successful HTTP response alone is insufficient: the stack
must have positive, fully ready replicas. This reapply can restart managed tasks;
schedule a maintenance window. Per-process waits are bounded (300 seconds;
shutdown 60 seconds and rollout/proof polls 120 seconds); HTTP requests retain
existing 30-second request and 180-second stack-update bounds, with bounded
post-restart authentication retries.

Verified desired/observed server and agent identities are committed atomically to
the existing installation manifest. Later setup/deployment consumes those pins;
conflicting overrides fail. Repeating a settled upgrade inspects actual state and
returns `no_op` without another backup, image update or stack reapply. Runtime /
manifest drift blocks instead of silently rewriting desired state.

If apply stops, preserve the journal and backup and use `--recover`. Component
batches and Portainer operations share a nonblocking lock; unsettled operations
block each other. Ordinary setup/deployment checks unsettled state at admission;
it does not hold that execution lock throughout setup. Serialize all live
operations against the same manager/Swarm, including W09 qualification. Recovery validates the original
Swarm, service IDs, topology and `/data` binding without using Portainer's API.
It verifies the checksum **before** stopping the server or touching state, archives
the failed volume contents in a new `failed-state.*` directory, restores the cold
snapshot into the same volume, and restores the source images. Nothing is deleted.
The original credentials, registrations and ownership are then verified and the
managed-stack proof runs again before source pins are committed.

Interruption before a backup checksum was committed permits only source-service
resumption: the unchanged original source image identities and data binding must
still match. It never restores an unchecked archive or starts target images.
Recovery interrupted during restore can be repeated, preserving each failed
attempt. Completed upgrades cannot be downgraded by `--recover`; recovery is for
interrupted operations. If the manager/storage/backup is lost, checksums fail,
service identities change or source data is corrupt before backup, stop for
operator investigation. Image rollback alone is never represented as state restore.
The archive protects Portainer state, not optional-service databases or workloads.

W09 must retain exact tested SHA, host/profile, selected services, version/digest
bundle, commands/exit codes and redacted before/after authentication, endpoint,
ownership, convergence and managed-update observations for upgrade and induced
failure/recovery. Local mocked tests do not establish live or browser success.

Portainer apply checks two visible endpoint and stack inventories and blocks visible
ambiguity, conflicting endpoint identities, malformed records, and drift before
stack or overlay-network changes. Portainer may omit stacks; a visible match is
not proof of ownership and a missing name is not proof of global absence. Legacy
creation and the 404/405 fallback remain in place; those responses do not prove
that no mutation occurred. Concurrent changes can occur after the recheck. Direct
`update_stack` calls bypass these apply checks.

Portainer management-gateway upgrades are blocked until independently persisted
ownership proof is implemented. The checked target-version no-op remains available.
Recovery can cancel an admitted backup or restore a checked backup, then remains
pending ownership proof. Interrupted recovery markers require manual reconciliation;
re-entry performs read-only checks and does not replay cancellation or restoration.
