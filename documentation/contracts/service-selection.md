# Deterministic Classic selection — #443 / LCM-W03

W03 implements read-only service planning. W04 owns installation, addition,
selection-aware preflight, routes, output and runtime verification. A valid plan
is not proof that a minimal installation or service combination has been deployed.
Existing setup without selection options retains its current fixed-preset behavior.

From the repository root on Linux/WSL:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world setup run --minimal --preview
PYTHONPATH=src python3 -m tiny_swarm_world setup run --services jenkins,sonarqube --preview --json
PYTHONPATH=src python3 -m tiny_swarm_world setup run --selection-config selection.yml --preview
PYTHONPATH=src python3 -m tiny_swarm_world services add --services swagger --preview
PYTHONPATH=src python3 -m tiny_swarm_world services remove --services jenkins --preview
```

The selection file is YAML or JSON with a single `services` list:

```yaml
services:
  - jenkins
  - sonarqube
```

Explicit `--services` wins over the selection file; an overridden file is not
read. Without either, an existing manifest supplies selection; otherwise the
compatibility preset expands the native catalog. An explicit preset is tracked
separately from the parser default; it is compatible with explicit selection only
when its expanded service set equals the resolved selection.
`--minimal` requests foundations and conflicts with explicit services, config
and preset. Empty comma entries, duplicate IDs, wildcards, aliases and unknown
IDs fail. Runtime/orchestrator selection is separate from service selection.

Incus is a mandatory host prerequisite, with host-operator ownership; Portainer
is a mandatory managed foundation. Planning does not prepare the host Incus
daemon. Foundations are added automatically, and attempts to remove them fail.
The catalog remains the W02 projection of native contracts/assets, with no second
service schema. Jenkins adds Nexus; service-access adds Nexus, Infisical and
Traefik. Dependencies are transitive, explained and ordered before their
consumers, with deterministic alphabetical tie handling. Unsupported preset or
capability combinations, cycles and unknown dependencies fail before persistence.
The CLI checks static catalog support, without querying host capabilities; declared
capabilities are prerequisites, not verified host readiness.

Previews expose requested/resolved sets, dependency reasons, additions, removal
impact and resource declarations/totals. Missing declarations are unknown;
zero declared totals are not a capacity estimate. Existing native Compose
assets do not currently declare resource limits. Whole-bundle resources count
once per resolved service. Removal preview includes reverse-dependent impact
and retains deployments, volumes and all persistent data. Removal apply is
unsupported. Setup selection previews also show deselection without applying it.

All selection commands require `--preview` and reject live/approval flags.
They load catalog/state without runtime composition, logging initialization,
secret generation, directory creation or writes. Successful previews exit 0,
invalid selections/arguments exit 2 and invalid stored state exits 1. Unavailable
or corrupt manifests must be repaired/adopted through W02 rather than inferred
from directory presence.

The application selection service also provides an explicitly approved local
manifest-persistence API for W04 callers. It uses the W02 atomic/CAS repository,
preserves installation/product/component/credential provenance, and refuses
removal. It does not assert deployment convergence. Fresh installation identity
and inventory must first be explicitly admitted through W02; the planner never
fabricates them. Preview tokens protect against concurrent edits. An interrupted
or failed write follows W02 diagnostics and requires inspection before retry;
no runtime rollback or data restore is implied. Repeating an unchanged selection
is a metadata no-op. CLI live selection application remains unavailable in W03.

Local unit/mocked checks verify planning and persistence only. Native Linux and
WSL2 live qualification belongs to W09; no live install, browser, infrastructure
or external quality success is claimed here.
