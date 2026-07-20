# Internal Orchestrator Responsibility Model

This model documents existing boundaries; it does not introduce a new public
command or alter workflow ordering.

| Component | Owns | Must not own |
|---|---|---|
| Command Router | Selects the public process strand | Skill activation, implementation, publication |
| Activation Resolver | Selects optional context after strand selection | Requirements, gates, ordering, stop conditions |
| Planner / S3D | Validates slice metadata and dependency order | Rewriting workflows or executing live infrastructure |
| Lock Coordinator | Acquires file, contract, module and architecture locks | Merging branches or weakening locks |
| Slice Executor | Performs authorized slice work and targeted checks | Expanding scope or changing public command semantics |
| Completion Auditor | Verifies requirements, tests and evidence | Implementing the slice or self-approving missing evidence |
| Publication Guard | Applies commit, push and PR lifecycle rules | Bypassing quality gates or silently cleaning unrelated changes |

The Command Router remains authoritative. The Activation Resolver is a
post-selection context filter and cannot call back into routing.
