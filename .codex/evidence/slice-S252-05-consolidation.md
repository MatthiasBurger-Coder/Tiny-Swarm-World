# Issue #252 — S252-05 Consolidation

- Workflow: `issue-252-classic-public-beta-rc1-20260818`
- Slice: `S252-05` — WSL2 post-install acceptance and reconcile
- Branch: `feature/classic-public-beta-rc1-stabilization`
- Host: WSL2/Linux userspace, commands executed through WSL
- Commit under test: `14cd01a391462aeec631d70640b4b490c560f955`
- Final slice result: `S252-05_LIVE_VERIFIED`

## Commands and results

| Scenario | Command | Start | End | Duration | Exit |
|---|---|---|---|---:|---:|
| Pre-reconcile verification | `./tsw --json --service-profile service-access --allow-wsl-windows-filesystem platform verify` | `2026-08-21T22:36:19+02:00` | `2026-08-21T22:36:37+02:00` | ~18 s | 0 |
| Reconcile | `./tsw --live --approve-live --json --service-profile service-access --allow-wsl-windows-filesystem platform reconcile` | `2026-08-21T22:38:00+02:00` | `2026-08-21T22:38:08+02:00` | ~8 s | 0 |
| Classic acceptance | `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests/e2e/classic -t .` | `2026-08-21T22:38:17+02:00` | `2026-08-21T22:38:26+02:00` | ~9 s wall / 3.669 s test runtime | 0 |
| Post-reconcile verification | `./tsw --json --service-profile service-access --allow-wsl-windows-filesystem platform verify` | `2026-08-21T22:39:15+02:00` | `2026-08-21T22:39:31+02:00` | ~16 s | 0 |

The operator environment was loaded only inside each WSL process from
`.tiny-swarm-world/local/live-installation.env`; values were not printed or
copied into tracked evidence. The WSL-mounted filesystem override was explicit
and recorded by the CLI.

## Acceptance

- Classic suite: `92` tests executed, `17` expected skips, `0` failures.
- `platform reconcile`: mutation result `no_op`, verification `verified`.
- Preflight/platform verification: `26` checks passed; all three managed Incus
  nodes reported `already_present` and `verified`.
- Incus nodes before/after: `swarm-manager`, `swarm-worker-1`,
  `swarm-worker-2`, all `RUNNING`.
- Swarm nodes before/after: three nodes, all `Ready`/`Active`; manager remained
  `Leader`.
- Stacks before/after: nine expected stacks, with identical names and service
  counts: `infisical(3)`, `jenkins(1)`, `nexus(1)`, `portainer(2)`,
  `pulsar(3)`, `service-access(2)`, `sonarqube(2)`, `swagger(4)`,
  `traefik(1)`.
- Running services before/after: all long-running services remained ready;
  `pulsar-manager-bootstrap` remained the expected completed `0/1` one-shot.
- Routing: all `18` expected LXC proxy devices were present, with zero drift,
  missing or unknown devices.
- Portainer: local endpoint remained registered and ready.
- Secret evidence: only names were inspected; the expected Traefik secret
  names remained present. No secret value, password, token, hash or env-file
  content was emitted.

## Findings and review

- No duplicate nodes or stacks were created.
- No unrelated healthy state was destroyed or changed.
- No product defect was found in S252-05.
- An initial outer timing wrapper had a shell-quoting error after the first
  successful reconcile. It was discarded as harness noise and the reconcile
  was rerun with a correct exit-code wrapper; the recorded result above is the
  corrected run.
- Role-based fallback review was used because callable subagents were not
  available. Senior DevOps, Senior Tester, Senior Python Automation Developer,
  Senior System Architect and Live Evidence Validation Expert concerns were
  covered in the distribution decision.

## Redaction and evidence

Redaction confirmed. This tracked consolidation contains no raw credentials,
join tokens, authorization headers, private keys, password values or full env
file. Runtime detail remains in ignored local evidence only. `composition.py`
was not changed.

Decision: S252-05 is live-verified. S252-06 and later slices remain open.
