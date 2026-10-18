# Component discovery and update planning

Classic component inspection and planning are read-only on Linux and WSL2:

```bash
tiny-swarm-world services list --json
tiny-swarm-world services updates --json
tiny-swarm-world services updates --services jenkins,nexus --json
tiny-swarm-world services update --services jenkins,nexus --preview --json
tiny-swarm-world services update --services jenkins --to native-baseline --preview
```

Run these commands from the prepared environment. Alternatively use
`PYTHONPATH=src python3 -m tiny_swarm_world` in place of `tiny-swarm-world`.
`services updates` defaults to the persisted installed selection. Update preview
requires an explicit nonempty comma-separated selection; it never adds services
or updates dependencies implicitly. `--to` selects a catalog **target ID** for one
service; batches resolve their catalog targets individually. Unknown IDs,
duplicates, wildcards, empty entries and conflicting options fail. An uninstalled
service must first be added explicitly through the selective setup workflow.

The current native catalog provides installation baseline image references and
**no qualified source-to-target component upgrade transitions**. Consequently,
`available_supported_targets` is empty and the preview examples above return a
blocked plan (exit 1). `native-baseline` identifies packaging metadata, not an
approved upgrade or downgrade. Upstream `latest` is never promoted automatically.
A future qualified transition must provide complete immutable source/target
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

The component executor now supports explicit live apply and recovery through the
existing Classic image-update adapters. The production catalog still has **no
qualified upgrade transitions**; these examples therefore fail admission until a
reviewed compatible transition is supplied. Synthetic test policies are not
production qualification. There is no arbitrary image/tag execution escape hatch.

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
