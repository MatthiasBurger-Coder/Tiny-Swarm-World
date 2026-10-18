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

`services update` currently accepts **only `--preview`**. Live/consent/recovery
options fail without initializing runtime services. W06 owns component execution,
verified convergence and desired-state persistence; W07 owns Portainer execution;
W09 owns cross-host live qualification. The existing `platform update` and
`platform update --recover` commands retain their #297 contract, including the
limitation that they do not persist desired image configuration. A successful
legacy image update is not automatically a qualified catalog transition.

See the [lifecycle contract](../contracts/lifecycle.md),
[installation state](../contracts/installation-manifest.md) and
[selective setup](selective-setup.md) for related boundaries.
