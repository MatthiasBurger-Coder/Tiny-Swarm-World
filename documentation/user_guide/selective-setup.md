# Selective Classic setup

Issue #444 / LCM-W04 connects the W03 selection planner to the existing Classic
setup workflow on native Linux and WSL2. Incus is a mandatory **host prerequisite**;
prepare its daemon, storage and network through the existing host preparation
steps. Portainer is a mandatory **managed foundation**. Selection does not install
or initialize the host Incus daemon.

Use a prepared checkout, activate its prepared Python environment, and retain the
existing operator environment/credential source.
Inspect first; the following preview commands perform no runtime composition,
secret generation or state writes:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world setup run --minimal --preview
PYTHONPATH=src python3 -m tiny_swarm_world setup run --services swagger --preview
PYTHONPATH=src python3 -m tiny_swarm_world setup run --services jenkins,sonarqube --preview
```

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
Fresh desired inventory leaves observed component versions unknown. Existing
manifest identity, product, observed components and credential/configuration
references are retained when adding services.

Selection is committed through the W02 atomic optimistic-concurrency repository
only after complete setup verification. An unchanged rerun leaves metadata
unchanged and uses existing reconciliation. If setup fails, the previous manifest
remains authoritative; inspect partial runtime work before retrying. If runtime
setup succeeds but metadata persistence fails, the command reports a partial
operation and failure exit, preserving runtime/data and requiring inspection or
adoption. An interrupted fresh run that created nodes before manifest commit
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
