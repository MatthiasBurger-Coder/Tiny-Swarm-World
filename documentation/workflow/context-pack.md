# ARCH-03.12 workflow context

Workflow issue-355-operation-results, version 1.0; process strand workflow create;
profile FULL_PATH. Branch `architecture/workflow-355-operation-results-20260926`; baseline `3487ce322bb2b251a45695fc88a70ffa8132b0de`.
Status READY_FOR_WORKFLOW; implementation NOT STARTED.

Read [workflow](workflow.md), [requirements](requirement-matrix.md),
[authoring review](authoring-review.md) and [machine context](context-pack.json).
The JSON records required/conditional roles, affected/forbidden areas, quality
commands and SHA-256 governing-file hashes. Recompute every hash at execution;
any change makes this context stale. No context pack replaces AGENTS.md, QUALITY.md,
ADRs, routing or skills. S355-01 must accept the ADR and inventory before code work.

Execution requires an isolated worktree and declared branch; specialist write
streams require distinct branches/worktrees and disjoint reviewed scopes. Reviews
are read-only. Product slices require targeted tests plus full local quality.
Authoring publication is commit and branch push only. No PR or merge is requested.
