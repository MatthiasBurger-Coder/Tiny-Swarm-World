# Issue #191 — S191-02 Distribution Decision

- Workflow: `issue-191-20260809` / `issue-191-v1.0.0`
- Slice: `S191-02` — Typed builders and gradual caller migration
- Execution branch: `feature/typed-verification-evidence-solid`
- Profile: `FULL_PATH`
- Chosen execution mode: sequential
- Real subagents used: `no`; no callable project-subagent tool is exposed.
- Fallback role-based review: `yes`; architecture, Python, testing and security
  reviews are performed in the main execution thread.
- Parallelization: rejected because the builder and all callers share one
  serialized evidence contract and the caller migration must preserve exact
  keys and values.
- Locked implementation areas: LXC node evidence, existing provider evidence
  helpers, LXC provider preflight and their focused tests.

## Boundary decision

Introduce a small infrastructure `EvidenceBuilder` with typed key constants.
It performs only key normalization, scalar serialization and defensive copy
creation. It must not classify failures, decide remediation, redact process
output, execute commands or own lifecycle policy. Existing producers retain
those responsibilities and pass already safe values to the builder.

## Verification plan

- Add deterministic builder tests for strings, integers, booleans, omitted
  `None` values and copy isolation.
- Migrate the common lifecycle envelope, teardown summary and LXC preflight
  evidence constructors without changing serialized output.
- Retain profile/resource helpers as producer-owned policy helpers while using
  the same serialization seam.
- Run focused tests and the required local quality gate before consolidation.
