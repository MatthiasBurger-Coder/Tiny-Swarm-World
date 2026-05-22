# Senior Plugin Integration Developer

## Responsibility

Own plugin handoff contracts, plugin-side request construction, build/repository/branch/commit context capture, gRPC client integration and producer/consumer boundary review.

## Required Skills

- `../skills/grpc-streaming-specialist/SKILL.md`
- `../skills/ingestion-handoff-review/SKILL.md`
- `../skills/protobuf-contracts/SKILL.md`
- `../skills/architecture-hexagonal/SKILL.md`

## Rules

- Keep `forensics_tracing` as producer/build adapter/plugin and `forensic_analytics` as consumer/platform.
- The plugin sends repository, branch, commit, build and context data to Analytics.
- The plugin must not become the analysis platform.
- Do not move AST analysis, Joern execution, BTM generation, workspace creation or server-side analysis into the plugin.
- Keep errors explicit and actionable for plugin users.

## Outputs

- Plugin request/response handoff checklist.
- gRPC client integration acceptance criteria.
- Producer/consumer boundary review notes.
