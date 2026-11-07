# Native fresh installation and memory assessment — 2026-10-03

## Scope and provenance

The operator authorized a fresh managed installation on native Ubuntu 26.04.1
with manager/worker limits of 8/6/3 GiB. The host reported 18.73 GiB RAM. This
was an already prepared host with an existing platform; resetting its managed
nodes does not establish a clean-host installation result or a physical
15 GiB-host qualification. WSL2 was outside this run.

Source base: `4efd3c0844319e6f3cde69e5858e424509a3ff99`, with the uncommitted
native `service-access` RAM-floor amendment from 20 to 15 GiB and its tests.
The protected evidence includes the exact source patch, checksums, node
inventories, results and an independent completion audit. The runtime provider
configuration was a local `TSW_INFRA_ROOT` override; repository node defaults
were preserved. No raw logs, credentials or operator-specific paths are
published in this summary.

## Executed results

| Check | Observed result |
|---|---|
| Native installer preflight | Exit 0 |
| Governed managed-node reset | Exit 0; three nodes removed; empty managed inventory before installation |
| Fresh identities and limits | All three UUIDs changed; live limits 8/6/3 GiB |
| Native installer | Exit 0; all setup phases completed |
| Separate platform verification | Exit 0 |
| Continuous services | All 18 reached desired replicas; Portainer agent 3/3 |
| Pulsar Manager bootstrap | One-shot task `Complete`; its service displays 0/1 after completion |
| Authenticated functional E2E | 8 readiness checks before + 9 browser tests + 8 readiness checks after = 25 tests; zero failures, errors or skips |
| API authentication | Seven checks; authenticated access and invalid-login rejection verified |
| Formal E2E runner | Exit 1, `LIVE_PARTIAL`; dirty source checkout prevents formal acceptance |

The browser routes covered Infisical, Jenkins, Nexus, Portainer, Pulsar admin
API, Pulsar Manager, Service Access, SonarQube and Swagger.

The unrelated host container `tiny-swarm-nexus-cache` remained available but
was not configured as a Docker registry mirror for the new nodes. Images
were downloaded directly upstream. The reset operated only on configured
Incus nodes. No LXD reset or deletion was issued; preservation is a scoped
claim, not an independent LXD database comparison.

## Memory observations

Sampling covered approximately 27 minutes (107 samples) during installation
and functional acceptance. Node cgroup measurements include cache and kernel
memory as well as applications.

| Node | RAM limit | Observed peak | OOM / OOM kills | Node swap |
|---|---:|---:|---:|---:|
| Manager | 8 GiB | Approximately 8 GiB | 0 / 0 | 0 |
| Worker 1 | 6 GiB | 0.99 GiB | 0 / 0 | 0 |
| Worker 2 | 3 GiB | 0.99 GiB | 0 / 0 | 0 |

The manager ended near 7.98 GiB and recorded 6,416 `memory.events max` limit
events. These indicate pressure at the limit and are not a count of individual
reclaim operations. Host swap was already occupied: about 2.07 GiB initially
and 3.43 GiB finally. Zero node swap does not imply a swap-free host, and this
measurement does not attribute host swap growth to a particular workload.

**Assessment:** 8/6/3 GiB supports the installation and functional checks in
this run, with little spare capacity on the manager. Spare worker capacity
does not automatically relieve manager-placed services. Sustained concurrency,
builds and larger analysis workloads were not qualified.

## Completion status

The requested fresh managed installation is completed and functionally
verified. Formal E2E acceptance remains `LIVE_PARTIAL` for this recorded run.
Committing the source later does not retroactively change that result.
Original issue #363 / ARCH-03.20 remains **INCOMPLETE**: this native baseline
does not establish all remaining lifecycle, RC1 or WSL2 requirements.
