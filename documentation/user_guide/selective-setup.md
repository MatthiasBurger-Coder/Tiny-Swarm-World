# Selective Classic setup

Issue #444 / LCM-W04 connects the W03 selection planner to the existing Classic
setup workflow on native Linux and WSL2. Incus is a mandatory **host prerequisite**;
prepare its daemon, storage and network through the existing host preparation
steps. Portainer is a mandatory **managed foundation**. Selection does not install
or initialize the host Incus daemon.

For `--minimal`, Portainer is deployed and authenticated during bootstrap.
There are then no selected application stacks to deploy. The apply phase still
runs its prerequisite/configuration/preparation guards and freshly verifies
Portainer admin access and a positive local endpoint identity before reporting
completion without deployment execution. Final readiness verification must also
succeed before the installation manifest is committed. This empty-apply result
is limited to the exact minimal selection. Other selections and update plans
still require their stack contracts; failed access checks block completion.

Explicit image pins are passed to Compose execution for each selected stack,
including both Portainer server and agent and all four Swagger components.
Existing stack settings are retained. Supplying an image environment variable
for an unselected service does not select or deploy that service. Image-policy
and committed desired-state conflict checks still apply; passing a pin is not
an observed-runtime version claim.

Use a prepared checkout, activate its prepared Python environment, and retain the
existing operator environment/credential source.
Inspect first; the following preview commands perform no runtime composition,
secret generation or state writes:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world setup run --minimal --preview
PYTHONPATH=src python3 -m tiny_swarm_world setup run --services swagger --preview
PYTHONPATH=src python3 -m tiny_swarm_world setup run --services jenkins,sonarqube --preview
```

To inspect the compatibility policy for an existing v1 installation manifest,
run the dedicated read-only preview:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world services migration-preview
```

The JSON result contains `status: PREVIEW`, `source: operator_local_unverified`,
`applied: false`, `qualified: false`, UNKNOWN project/profile/route/owner identities and
policy labels for selected stacks. A blocked preview returns the fixed JSON
`{"status":"BLOCKED_UNKNOWN","source":"operator_local_unverified","applied":false,"qualified":false}` and exit 2.
The command does not migrate or adopt state, qualify the host or declare
version support; its policy labels do not establish actual stack ownership.
The local catalog and assets are operator-provided and unverified. The preview
does not establish catalog authority, release provenance or host safety.
Only fixed Compose assets under the local project root are previewed;
`TSW_INFRA_ROOT` is not evaluated. Missing project-root assets block the preview.

Apply uses the existing explicit live-consent boundary. These are operator commands,
not commands executed as development verification:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world setup run --minimal --live --approve-live
PYTHONPATH=src python3 -m tiny_swarm_world services add --services swagger --preview
PYTHONPATH=src python3 -m tiny_swarm_world services add --services swagger --live --approve-live
PYTHONPATH=src python3 -m tiny_swarm_world deployment verify
```

`--services` takes precedence over `--selection-config`; an overridden file is not
read. Otherwise the persisted selection wins, then the compatibility preset.
An explicitly supplied `--service-profile` must expand to the same resolved set
as an explicit selection. `--minimal` conflicts with explicit services, selection
configuration and preset. A preset is separate from runtime/backend selection.
Existing fixed-profile setup without selection or a manifest keeps its established
compatibility behavior. Once a manifest exists, setup and standalone platform,
artifact and deployment composition use that persisted resolved selection.

Jenkins adds Nexus; the service-access dashboard adds Nexus, Infisical and
Traefik. Public-image-only selections do not require Nexus authentication or its
registry bootstrap. Secret validation, assets, deployment, forwarding and
verification are scoped to selected services and their dependencies. Without
selected Traefik, access output uses published localhost ports instead of claiming
HTTPS ingress. With Traefik, only selected routes and links are exposed.

The current Classic node topology remains three nodes regardless of optional
services. Configured allocations total 8 CPU threads, 19 GiB memory and 80 GiB
disk; existing provider host-capacity admission remains active. Fixed-profile
host floors are compatibility checks, not measured selected-service consumption.
Selection previews expose only selected native resource declarations; missing
limits/reservations remain **unknown**, not zero or a qualified smaller-host
capacity claim. This slice does not resize or recreate healthy nodes.

For a fresh selective installation, bounded read-only Incus inventory must prove
that no configured or Tiny Swarm World marked node already exists before assigning
a new installation identity. Existing nodes without a manifest require explicit
W02 inventory/adoption; setup refuses rather than guessing or resetting them.
Fresh desired inventory initially leaves observed component versions unknown.
After successful setup, including its existing Portainer authentication and endpoint
checks, a new complete Swagger or Traefik bundle whose immutable desired pins match
an admitted full source or target bundle receives bounded service/task observations
before the single selection commit. Only actual observed repository/tag/digest facts
are recorded; upstream/build versions are not inferred from desired metadata.
Every eligible member must match its pinned desired image and converged running
tasks. Partial, tag-only or unknown bundles retain unknown observations.

This enrichment applies only to newly introduced components. Existing manifest
identity, product, component states and credential/configuration references are
retained when adding services. An ordinary rerun does not refresh old unknown
observations or rewrite unchanged metadata. It is not a general inventory-refresh
command or permission to replace an existing adoption manifest. Image/task facts
alone do not establish Traefik authentication/TLS or Swagger functional acceptance.

Selection is committed through the W02 atomic optimistic-concurrency repository
only after complete setup verification. An unchanged rerun leaves metadata
unchanged and uses existing reconciliation. If setup fails, the previous manifest
remains authoritative; inspect partial runtime work before retrying. If runtime
setup succeeds but metadata persistence fails, the command reports a partial
operation and failure exit, preserving runtime/data and requiring inspection or
adoption. Failed or timed-out required source observations after runtime success
also report failed verification and a partial operation without committing any
selection metadata. Cancellation propagates; no automatic reset is performed.
An interrupted fresh run that created nodes before manifest commit
requires reviewed adoption. There is no automatic rollback/data restore.

Deselection apply is refused. `services remove --services <ids> --preview` remains
read-only and explains impact; it never deletes deployments, volumes or data.
Credential rotation and destructive reset are separate explicit operations.

Local tests use mocked process, service and network boundaries. Native Linux and
WSL2 live installation, browser access and preservation proof remain
`LIVE_CONSENT_MISSING` here and are coordinated by #449 / W09. Record exact tested
SHA and working-tree identity, host/profile, product/component versions, resolved
selection, command, exit and redacted before/after observations for each actual
live qualification scenario. Local test success is not live or SonarQube success.
