# Issue #218 — Resource and mutation-gate evidence

## Real WSL2 snapshot

The live service-access host reported:

- CPU threads: `28`
- effective memory: `20968042496` bytes
- cgroup memory limit: unlimited for the current WSL instance
- current memory usage: recorded by the resource inspector
- free disk: `962453090304` bytes in the live preflight snapshot
- Incus manager and worker nodes: running
- no new OOM event was observed during the fresh installation run

The full structured cgroup evidence includes `memory.current`, `memory.max`,
`memory.high`, `memory.events` and `memory.stat` where the host exposed them.

## Resource decisions

- The configured `service-access` profile passed on the real host.
- The filesystem policy failed closed on `/mnt/d` until the explicit override
  was provided.
- A controlled live WSL2 cgroup-v2 run used `systemd-run --user --scope -p
  MemoryMax=8G` with the full `service-access` profile. The inspector resolved
  the nested process cgroup and reported `cgroup_memory_limit_bytes=8589934592`
  and `effective_memory_bytes=8589934592`.
- The controlled preflight returned `RESOURCE-STRUCTURED=INSUFFICIENT`, overall
  status `RESOURCE_GATED` and exit code `1`. The configured manager request is
  `10GiB` (`infra/config/node-providers/provider_config.yaml`); no platform
  phase was entered.
- Read-only before/after snapshots of Incus instances, the manager/Swarm
  profiles, Docker stacks and Docker services were identical. No Incus limit,
  container, Swarm or service mutation occurred.
- Aggregate Incus limit validation is in the provider/application path before
  limit-bearing operations.

The deterministic guard fixture remains in place as a regression test; the
controlled live cgroup run now supplies the corresponding acceptance evidence.
