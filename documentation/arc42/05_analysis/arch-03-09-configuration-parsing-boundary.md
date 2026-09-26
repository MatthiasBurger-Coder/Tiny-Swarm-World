# ARCH-03.09 — Configuration Parsing Boundary

Status: implemented locally; final issue acceptance is tracked in the
[completed #352 requirement matrix](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/blob/3487ce322bb2b251a45695fc88a70ffa8132b0de/documentation/workflow/requirement-matrix.md).
Issue: #352; parent: #313.

## Ownership and typed boundaries

Infrastructure adapters own external YAML syntax, configuration-tree checks,
schema conversion and safe parser errors. Domain models own parser-independent
invariants. Application services receive explicit models through ports; ordinary
validated string mappings and opaque validated Compose text remain supported.
The existing ARCH-03.02 layer ownership applies without a new ADR or parser
replacement.

`SecretManifestYamlRepository` returns immutable `SecretManifestEntry` values
through `PortSecretManifestRepository`. `SecretManifestRenderer` delegates to
that port and translates its safe error into `manifest_schema_invalid`; it no
longer checks raw YAML shapes. The installer uses the same manifest adapter.
`PortLocalFileStorage.load_yaml` has been removed after migrating its consumer.
The manifest retains PyYAML safe-loader semantics; existing ruamel repositories
retain their parser. Duplicate keys, recursive configuration aliases and unsafe
scalar/shape coercions fail at the appropriate boundary.

Provider, inventory, command and port repositories return their existing typed
models with stricter external scalar validation. `ComposeFileRepositoryYaml`
validates the service catalogue and TSW-consumed Compose structures, including
service, image, deployment, port and renderer-owned fields. It preserves
extensions, ordinary aliases, interpolation and supported port syntax. This is
not validation of the entire Compose specification.

## Selected configuration before managed mutation

The production Compose repository's `validate_and_snapshot` validates all
selected stacks before publishing its cache. It retains immutable
`StackDefinition` content and service metadata derived from that content.
Subsequent selected reads use the retained content even if source files change.
The port also returns an immutable `StackConfigurationSnapshot`; callers of
other repository implementations must retain that result rather than assume
those implementations cache reads. Deployment steps retain their prepared
`StackDefinition` before running.

Deployment runs prerequisite checks, prepares selected static configuration,
then permits mutating preparation and apply steps. A bad later stack therefore
fails before an earlier stack is deployed. Setup prepares both deployment
workflows and validates the selected environment in its artifact-contract
preflight phase, before host preparation, provider, network, artifact or
service mutation. Composition retains provider configuration, operator values
and Docker mirror settings so runtime consumers use the checked selection.

Fresh installation validates a private copy of the selected infrastructure
configuration and operator source before reset. Reset and setup receive the
same staged roots and effective environment. Dependency bootstrap, private
staging and sanitized evidence preparation may write local files before
managed lifecycle mutation; the guarantee is not zero filesystem writes.

Static preparation does not contact the vault. The full service-access
composition can defer `TSW_JENKINS_ADMIN_PASSWORD` only where the Infisical sync
step and Jenkins credential callback are wired. The resolved credential
snapshot is checked when Jenkins deploys after that runtime preparation.
Update/custom paths without the callback require their static value, and the
normal installer validates catalog/operator-resolved requirements before reset.
This does not change credential precedence, consent or vault readiness policy.

## Compatibility, limits and verification

See [operator migration guidance](../08_configuration/operator-configuration-contract.md#configuration-parsing-and-migration)
for retained defaults and intentionally rejected input. Private installer
staging checks the original source's storage policy, rejects symlink/special
file traversal, uses owner-only storage and cleans up when its context exits.
It does not make an unsafe original credential source acceptable.

The [configuration inventory](../08_configuration/config-contract-inventory.md#parsing-boundary-classification-arch-0309)
distinguishes active inputs from dormant compatibility paths, declarative
contract mirrors, service-owned pass-through files and runtime observations.
Auxiliary bridge scripts and tool-owned configuration are not claimed to have
new schema validation.

Deterministic repository, domain, deployment, setup and installer tests cover
malformed/valid input, actual retained-input consumption, preparation failures
before mutation, source substitution and safe error rendering. Architecture
checks guard domain/application against `ruamel` and `ruamel.yaml` imports;
runtime model checks verify returned values do not contain parser containers.
The workflow's required local quality gate and independent issue audit remain
the completion authority. These checks provide no live installation, Swarm,
Selenium or external quality-service success claim.
