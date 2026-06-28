# Skill And Agent Creation Process

Use this process when adding project skills, role files, or Codex agent
definitions.

## Rules

- Skills live under `.agents/skills/<name>/SKILL.md`.
- Grouped `.md` files are documentation indexes only; they are not
  authoritative skill entrypoints unless local skill discovery rules change.
- Every project skill `SKILL.md` must include YAML frontmatter with `name` and
  `description`.
- Project roles live under `.agents/roles`.
- Codex callable-agent definitions live under `.codex/agents`.
- Root `AGENTS.md` and `QUALITY.md` remain authoritative.
- New Python implementation roles must preserve the hexagonal architecture and live-infrastructure safety rules.
- New or changed git publication skills, agents, or prompts must preserve the
  `push auto` lifecycle: task-scoped changes, including Python product code and
  Python product-behavior tests, may be automatically merged only after commit,
  pull request creation, green required checks including SonarQube when
  configured, merge verification, remote branch deletion and local cleanup.
- Java roles are out of scope unless the user explicitly changes the project
  architecture.
- Tiny Swarm World is Docker Swarm first and Kubernetes-aware, not
  Kubernetes-first.
- Console/status UI skills are terminal-oriented and do not authorize browser
  React work.

## Canonical Audit Paths

- `documentation/process/skills/audit/skill-registry.md`
- `documentation/process/skills/audit/skill-registry.json`
- `documentation/process/skills/audit/organigramm.md`
- `documentation/process/skills/audit/owner-map.md`

Repository files remain authoritative. The registry and organigramm are audit,
navigation, and coordination artifacts.

## Verification

Run:

```bash
git diff --check
```

Run `python3 tools/quality_gate.py quality` when practical before commit or push.
