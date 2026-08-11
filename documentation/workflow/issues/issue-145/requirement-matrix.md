# Requirement Matrix — Issue #145

Source: [GitHub Issue #145](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/145)

Status at workflow authoring: `PLANNED`.

| ID | Requirement | Type | Planned implementation area | Slice | Verification/evidence | Status |
|---|---|---|---|---|---|---|
| REQ-145-01 | Derive bounded parallel phase groups from the installation plan's explicit dependencies. | functional | `domain/preflight/installation_plan.py`, setup orchestration | S145-01/S145-02 | graph contract tests | PLANNED |
| REQ-145-02 | Safety-critical shared mutations remain serial. | safety/architecture | setup phase scheduler | S145-02/S145-04 | mutation boundary review | PLANNED |
| REQ-145-03 | Execution stays inside the existing async model; no ad hoc threading or hard-coded special cases. | architecture | setup workflow | S145-03/S145-04 | source scan and tests | PLANNED |
| REQ-145-04 | Result aggregation and progress reporting remain deterministic. | UX/observability | setup workflow result/progress | S145-05 | ordering/progress tests | PLANNED |
| REQ-145-05 | Failed branches retain original context; dependent phases are skipped/blocked with clear reasons; completed independent branches retain evidence. | resilience | scheduler result model | S145-05 | branch failure tests | PLANNED |
| REQ-145-06 | Configurable maximum concurrency exists and is tested. | performance | scheduler configuration | S145-03/S145-06 | limit test | PLANNED |
| REQ-145-07 | Duration evidence is produced per phase group, not only as one final total. | performance evidence | shared #152 contract | S145-05/S145-06 | evidence artifact | PLANNED |
| REQ-145-08 | Single-computer and future multi-node/worker registration modes remain compatible. | scalability | plan and scheduler contracts | S145-01/S145-06 | compatibility fixtures | PLANNED |
