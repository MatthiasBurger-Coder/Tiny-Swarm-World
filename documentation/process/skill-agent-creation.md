# Skill And Agent Creation Process

Use this process when adding project skills, role files, or Codex agent
definitions.

## Rules

- Skills live under `.agents/skills/<name>/SKILL.md`.
- Project roles live under `.agents/roles`.
- Codex callable-agent definitions live under `.codex/agents`.
- Root `AGENTS.md` and `QUALITY.md` remain authoritative.
- New Python implementation roles must preserve the hexagonal architecture and live-infrastructure safety rules.
- Java roles may cover only the deployment example unless the user explicitly changes the project architecture.

## Verification

Run:

```bash
git diff --check
```

Run `python3 tools/quality_gate.py quality` when practical before commit or push.
