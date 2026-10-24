# Product release upgrades

The product controller implements one prepared-Git transition for Classic:
**0.4.0 → 0.5.0 (RC-5)**, on native Linux and WSL2 with Python 3.12.
The source revision is `346f4a43dbdc43380e7bc703ab185bc06746965b`;
the target revision is `b3de7fa16e24c5702d61f855851c6c3255871489`.
Both published revisions have package metadata version `0.2.0`. Release tag,
executed revision and lock hash identify the transition; the controller preserves
the package-version distinction instead of rewriting the published release.
Live cross-host qualification remains owned by W09; local tests are not live
upgrade evidence.

## Start from management tooling

Neither published release includes the new `product upgrade` command. Use a
separate trusted checkout containing this controller and its prepared Python
environment. Keep that checkout available throughout recovery and repeated
verification. Do not repoint or rewrite an existing release tag.

Set `TSW_REPOSITORY_ROOT` to the **existing 0.4.0 installation checkout**, not
the management checkout. The existing installation remains the state anchor.
Do not run setup, reconcile, deployment, component updates or other installation
writers concurrently. The controller shares current component/gateway locks,
but older released programs cannot honor a guard they do not contain.

```bash
# Run inside the management checkout and its Python 3.12 environment.
export TSW_REPOSITORY_ROOT="$HOME/tsw-installed"
unset TSW_INFRA_ROOT
PYTHONPATH=src python3 -m tiny_swarm_world product upgrade --help
PYTHONPATH=src python3 -m tiny_swarm_world product upgrade --to 0.5.0 \
  --adoption-manifest "$HOME/tsw-inventory.json" --preview --json
```

The source checkout must be clean, including nonignored untracked files.
Ignored local state, environment files and credentials remain protected; never
commit them to satisfy the cleanliness guard. Dirty tracked overrides block
before mutation. Preserve them and resolve them explicitly rather than resetting.
Wheel-only installations, archives, arbitrary repositories/releases, future
schemas and downgrades are unsupported. Official release metadata/ref reads need
network access; staging needs at least 2 GiB free disk beyond the existing runtime.
The selected runtime must already pass its platform, endpoint and task checks.

## Explicit legacy inventory

0.4.0 has no automatic installation manifest. Supply an independently inventoried
schema-1 JSON manifest using the [installation manifest contract](../contracts/installation-manifest.md).
It must contain installation UUID, actual host, Classic preset, requested and
resolved services with dependency reasons, complete selected component inventory,
and symbolic configuration/credential-source references. Its product fields are
release `0.4.0`, the exact source revision above, the SHA-256 of the source
`requirements.lock`, configuration schema 1 and installation model `prepared-git`.
Component IDs and image identities come from the existing installation and native
catalog. Incus and Portainer are mandatory. Do not supply passwords, tokens,
credential fingerprints or arbitrary configuration maps.

The controller rejects absent, malformed, incomplete or inconsistent inventories.
It verifies the actual selected runtime before recording any progress, then records
adoption only after the product switch is verified. A supplied file is not runtime
proof. An existing valid manifest is used directly; omit `--adoption-manifest` in
that case. There is no automatic reset or inference that directories prove an
installation.

## Preview and apply

Preview performs bounded read-only Git, metadata, manifest, host and resource
checks. It writes no journal, environment, configuration or runtime state. It
separates product revisions, dependency locks, infrastructure changes, state
migrations and component changes. This release transition preserves installed
component images; it does not invoke the component or Portainer upgrade engines.

```bash
PYTHONPATH=src python3 -m tiny_swarm_world product upgrade --to 0.5.0 \
  --adoption-manifest "$HOME/tsw-inventory.json" --live --approve-live --json
```

Without `--approve-live`, `--live` uses the existing interactive confirmation.
Preview and live flags are mutually exclusive. Selection overrides and image
update flags are rejected: a product upgrade verifies the entire installed set.

Execution records a private durable checkpoint, stages the official pinned
checkout and a new environment, installs hash-locked dependencies and checks their
actual versions. It copies protected infrastructure into a private snapshot,
updates changed release defaults and preserves local files/references. Unsupported
asset removals or new paths colliding with overrides block. It does not modify the
original checkout, old environment, identities, service data or credentials.

The staged target runs its own selection-aware platform/deployment verification.
The controller also checks fresh service identities, desired and task images,
replicated/global task state, completed Pulsar bootstrap and authenticated
Portainer endpoint access. Reachability or a healthy old image alone cannot
complete the upgrade. After verification an atomic pointer activates target
code/configuration; the final manifest records the target revision and lock.

Use the resulting installation launcher for normal target commands:

```bash
"$TSW_REPOSITORY_ROOT/.tiny-swarm-world/product/tiny-swarm-world" product version --json
```

The original checkout remains the anchor. The launcher uses staged target code
and environment with the migrated infrastructure snapshot. Keep original assets
and the private product directory; neither is disposable cache. The published
target launcher does **not** gain the newer controller: use the management
checkout commands above for recovery and repeated upgrades.

## Interruption and recovery

```bash
# Always run these from the preserved management checkout/environment.
PYTHONPATH=src python3 -m tiny_swarm_world product upgrade --to 0.5.0 --recover --preview --json
PYTHONPATH=src python3 -m tiny_swarm_world product upgrade --to 0.5.0 --recover --live --approve-live --json
```

Recovery uses the original pinned inventory, revisions, locks and per-stage
journal; omit the adoption file. Staging/migration resume idempotently. Only the
operation's incomplete private configuration copy may be rebuilt. A moved tag,
source change, unrelated activation, modified migrated snapshot or changed
manifest/runtime identity blocks for inspection. Preserve all files and correct
the reported drift; do not delete checkpoints or reset the checkout.

After a switch or manifest-write interruption, recovery re-verifies and completes
the same target. Retaining old code/environment is not whole-host rollback or
persistent-data restore. Automatic downgrade/reverse migration is unsupported.
Repeating a completed operation through management tooling is a no-op only after
fresh product, active configuration, manifest and whole-selection verification.
Recovery preview reports durable stage without executing runtime commands.

Checkpoint authority: `.tiny-swarm-world/installation/product-upgrade.json`.
Private code/configuration/activation: `.tiny-swarm-world/product/`.
Do not publish those directories; they contain protected configuration and may
contain runtime credentials. Evidence must remain redacted and separate from
credential sources, and W09 must identify the exact management SHA and source/
target release, host/profile, selection, commands, exits and before/after results.
