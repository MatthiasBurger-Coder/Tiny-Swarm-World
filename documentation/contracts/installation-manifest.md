# Installation manifest and component catalog (LCM-W02 / #442)

Contract version 1. Implements the persistence/inspection part of the accepted
[Classic lifecycle ADR](../arc42/09_decisions/adr-classic-product-component-lifecycle.adoc).
Classic on native Linux and WSL2 only. Runtime execution, arbitrary selective
setup and qualified upgrades remain owned by W04–W09. W03 adds
[deterministic selection planning](service-selection.md) and approved local
selection persistence over these contracts.

## Inspect an installation

Run from the prepared checkout/environment:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world product version --json
PYTHONPATH=src python3 -m tiny_swarm_world services list --json
```

These commands read native catalog assets and
`.tiny-swarm-world/installation/manifest.json` beneath the repository root.
They do not create directories, logs, state, credentials, runtime clients or
live observations. No manifest means `adoption_required`, with installed service
state `unknown`, never an inferred successful installation. `services list`
separates installed/uninstalled services when an instance is present. A valid
inspection exits 0; corrupt/unsupported/inconsistent state exits 1; mutation,
consent and update-only options are rejected with exit 2. `--help` and
`--list-workflows` remain available. There is no new mutating CLI in W02.

The product field identifies the recorded installed product, not necessarily
the currently executing checkout. It records release, exact revision, lock
SHA-256, configuration schema and the `prepared-git` installation model.
Read-only commands do not run Git or claim a dirty working tree is upgradeable.
W08 owns checkout verification and source-to-target release admission.

## Schema and ownership

`domain/lifecycle/models.py` is the canonical machine-validated logical contract
shared with #318. `InstallationManifest.model_json_schema()` and
`ComponentCatalog.model_json_schema()` expose the schemas. Both use schema and
catalog version 1; extra fields and malformed types are rejected. The manifest
contains a UUID installation identity, host, Classic runtime profile, distinct
service preset, requested/resolved service IDs and provenance for every added
service; full selected component inventory; symbolic effective configuration
provenance; credential key/source references; and optional operation/checkpoint
references. Credential values and arbitrary effective configuration maps are
not admitted. References follow the existing secret-manifest key/source vocabulary.

Component upstream version, local build identity, image repository/tag and resolved
SHA-256 digest are separate fields in desired and observed state. Unknown fields
are null; a tag is never promoted to a digest or upstream version. This release's
catalog supplies native image references/build identities; upstream discovery
belongs to W05. Incus has no container image or automatically inferred package
version. Runtime observations must be supplied by a qualified caller; W02 does
not contact the engine or registry. Missing observations and known desired-field
mismatches/unknowns produce explicit per-component `drift` codes, including
`resolved_image_unknown`. Inspection is never an update-success claim.

`NativeComponentCatalog` owns logical Classic policy projection: mandatory Incus
and Portainer, dependencies, capabilities, preset support, resources, asset
references, update owner and backup/migration restrictions. It consumes the existing
`ServiceStackContract` membership and `ContainerImageContract` versions, reads
native Compose through structured YAML, and rejects missing/mismatched images
or unconsumed contracts. All bundle images are included, including Portainer
agent, databases and the Pulsar one-shot bootstrap. Native assets are references,
not generated replacements. Existing deployment/readiness, artifact/build and
preflight contracts keep their own responsibilities; no second orchestrator exists.

Catalog compatibility version 1 admits only the current native baseline for
Classic, not arbitrary vendor targets. Every service says
`no-qualified-transition`: W05–W08 must explicitly admit transitions and migration
owners before executing them. Stateful services require backup before a future
transition; image rollback is not data restore. Incus host-package changes belong
to the host operator and Portainer upgrades to its dedicated adapter.
`ResourceRequirements` reports native declarations only: absent Compose limits
mean unknown/unqualified capacity, never zero resource demand. #314 owns runtime
capability vocabulary; the recorded Classic requirements do not claim other
profiles work. #318 owns shared schema evolution; W02 incrementally implements
it, without inventing a parallel cross-profile catalog.

Current fixed setup still requires routing/Traefik and artifacts/Nexus;
service-access additionally couples Infisical and generated dashboard links.
Logical dependencies expose Nexus for local Jenkins/dashboard images and
Infisical/Traefik for Service Access. Arbitrary omission is not supported until
W04 integrates selection into every existing phase. The catalog does not
change current setup, #297 update, bootstrap or consent semantics.

## Persistence, migration and interruption

The infrastructure JSON repository keeps the manifest separate from Compose,
operator YAML and credential stores. Writes require the token returned by the
last read (`expected_token=None` means create only). An advisory local writer
lock serializes compare-and-replace. Identical writes are no-ops; stale tokens
fail with a request to inspect again. Writers must preserve installation identity
and use application policy rather than replacing other installations.

The adapter validates before writing, uses a private same-directory temporary
file, flushes/fsyncs it, atomically replaces the manifest and fsyncs the directory.
Files/locks are created with mode 0600 and newly created state directories 0700.
A pre-replace failure leaves the original intact. A directory-fsync failure may
leave the new manifest installed, so the error explicitly requires inspection
before retry. Normal failures remove their own temporary file. A process kill
may retain `.installation-manifest-*.tmp`; reads report `interrupted_write` and
never promote, delete or trust these files automatically. Preserve them for
manual comparison with the final manifest and the original reviewed inventory.

Schema migration ownership is shared-contract owner #318, implemented in the
lifecycle codec/application boundary, never in readers or unrelated setup stages.
Version 1 has an identity migration only. No earlier installation-manifest
schema was shipped; legacy preflight/setup/update state is not this schema.
Version 0, future versions, duplicate JSON fields and corrupt state are blocked,
left byte-for-byte intact and require matching code or a separately reviewed
explicit migration. Do not change a version number manually or rerun install as
a migration. Tests cover current-schema roundtrip/no-op and rejection/preservation
of unknown, legacy, corrupt and interrupted state. Future migrations must keep
installation identity, operator configuration/provenance and credential references,
preview without writes and use the same atomic commit boundary.

## Existing installations and adoption

Legacy installations remain usable through existing commands. They cannot be
silently adopted from directory presence, a running stack or a healthy page.
W02 inspection deliberately blocks assumptions with `adoption_required`. To
resolve it, inventory the exact product revision/release/lock/schema, existing
service preset and complete bundle selection, installation UUID, protected
credential-source references and operator override provenance. Do not copy
credential values into an inventory or evidence. Resolve conflicting/missing
identity or selection evidence before attempting any write; preserve original
configuration and runtime state throughout.

The application integration path is
`InstallationLifecycleService.adopt(manifest, preview=True)`, followed by
`adopt(manifest, preview=False, approved=True)` only after the inventory is
reviewed. It validates foundations, dependencies, preset and exact component
membership and refuses an existing different identity/state or interrupted
adoption. Repeating the same adoption is a no-op. Observations remain unverified;
adoption is neither runtime convergence nor live consent. This callable local
boundary is for W03/W04 integrations, not an operator CLI yet. Operators lacking
verified inventory must stop with the actionable diagnosis and keep using the
legacy path until the selection-aware adoption integration is available. No
reset, removal, secret rotation or data migration is an adoption remedy.

## Evidence and qualification

AC1 maps to codec/schema/migration rejection tests; AC2 to atomic repository,
preview/no-op and read-only CLI tests; AC3 to identity/drift and bundle catalog
tests; AC4 to adoption inventory/approval/conflict tests and the blocked operator
path above. `tests/domain/lifecycle`, `tests/infrastructure/adapters/lifecycle`,
`tests/application/services/test_lifecycle.py` and `tests/test_lifecycle_cli.py`
provide deterministic local evidence. Issue evidence lives under
`.tiny-swarm/evidence/issue-442/`; tracked completion evidence is linked from
`documentation/evidence/issue-442-completion-audit.md`.

No live mutation, browser check, authenticated service verification, upgrade or
cross-host qualification is claimed. W09 consumes this local evidence and must
record exact committed SHA, host/profile, actual product/component identities,
resolved selection, commands, exit codes and redacted before/after observations
for every separate live claim. Missing/skipped/inconclusive checks remain non-pass.
