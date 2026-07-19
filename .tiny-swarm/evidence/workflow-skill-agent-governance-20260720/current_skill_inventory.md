# Current Skill Inventory — Slice 01 Baseline

## Inventory scope

The mandated read-only scope is:

```text
AGENTS.md
QUALITY.md
.agents/**
.codex/**
documentation/process/skills/**
documentation/workflow/**
documentation/process/issue-completion-discipline.md
```

`src/tiny_swarm_world/infrastructure/composition.py` was inspected only as an
architecture boundary. It is the 2,487-line runtime composition root with
builders for host detection, setup, platform, artifact and deployment services;
it is not a skill or agent orchestrator and is excluded from all write scopes.

## Deterministic baseline

The read-only `rg --files --hidden` inventory found the following authoritative
entrypoint counts. Only `.agents/skills/**/SKILL.md` is project-skill discovery;
other governance Markdown files are not skill entrypoints.

| Entry kind | Count |
|---|---:|
| Discoverable project skills (`.agents/skills/**/SKILL.md`) | 132 |
| Project roles | 17 |
| Agent definitions/references | 34 |
| Subagent documents | 8 |
| Prompts | 6 |
| Governance/orchestrator documents | 49 |
| Registry/audit artifacts | 8 |
| Orchestrator documents | 7 |

The canonical registry claim of 132 discoverable project skills is confirmed.
The earlier count of 140 was an inventory-method error caused by counting
non-entrypoint governance documents. A separate parity finding remains: the
Markdown registry lists 48 canonical required skills while the JSON registry
contains 47. That documentation inconsistency remains explicit for registry
reconciliation.

## Preliminary relationship matrix

| Skill or agent family | Type | Current owner | Activation path | Owned paths | Delegates/partners | Conflict | Project relation | Reachability |
|---|---|---|---|---|---|---|---|---|
| Workflow routing/execution | governance skill/agent | Senior Workflow Architect / Workflow Executor | exact command routing | `.agents/orchestrator/**`, workflow skills | S3D, requirement gate, quality gate | must not cross-call strands | `TINY_SWARM_WORLD_CORE` | reachable |
| Requirement/completion | governance skill | Senior Requirement Engineer | issue/workflow phases | requirement and evidence docs | Three Amigos, Issue Completion Auditor | completion authority must stay independent | `TINY_SWARM_WORLD_CORE` | reachable |
| Registry/audit | governance skill | Skill Registry Conflict Auditor | skills update / audit phase | registry and skill entrypoints | Documentation Engineer, Workflow Architect | owner and count drift | `TINY_SWARM_WORLD_CORE` | reachable |
| Python automation/quality | engineering skill | Senior Python Automation Developer / Senior Tester | affected Python scope | `src/**`, `tests/**`, quality tooling | architecture and DevOps reviewers | product scope forbidden in this workflow | `TINY_SWARM_WORLD_CORE` | reachable |
| Docker/Incus/networking/service bootstrap | conditional skill | Senior DevOps Engineer | matching runtime evidence | platform/configuration paths | platform verification | must not load without matching issue evidence | `TINY_SWARM_WORLD_CONDITIONAL` | reachable |
| Jenkins/Nexus/SonarQube/Portainer/Traefik/Infisical | conditional skill | Senior DevOps Engineer | named service/config evidence | service bootstrap/config docs | quality/security owners | live operations forbidden without explicit approval | `TINY_SWARM_WORLD_CONDITIONAL` | reachable |
| Spring/Java/React/Joern/forensic/Kubernetes-first assets | reusable or legacy skill | external owner or stale route | explicit exception only | `.agents/**`, `.codex/**` legacy assets | Root Architect only after scope proof | must not enter Tiny Swarm World core implicitly | `EXTERNAL_LIBRARY` or `STALE` | conditional/unreachable by default |

## Review status

- Senior Requirement Engineer: baseline captured; the 132-entrypoint count is confirmed; registry parity remains open.
- Senior System Architect: `composition.py` boundary verified; governance/runtime separation preserved.
- Senior Python Automation Developer: no Python product scope authorized; quality tooling is verified separately.
- Senior Tester: quality gate is green after documented dev-tool installation; regression tests remain later-slice work.
- Skill Registry Conflict Auditor: the 140-vs-132 conflict is resolved as a measurement error; the 48-vs-47 registry parity issue remains open.
