# Requirement Matrix — Issue #151

Source: [GitHub Issue #151](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/151)

Status at workflow authoring: `PLANNED`.

| ID | Requirement | Type | Planned implementation area | Slice | Verification/evidence | Status |
|---|---|---|---|---|---|---|
| REQ-151-01 | Normal `./install.sh --confirm-reset`, `--update` and default flows do not print raw JSON blocks to stdout. | UX | `__main__.py`, installer/reporters | S151-03 | CLI/installer output tests | PLANNED |
| REQ-151-02 | Setup/reset/deployment/verification results use compact readable line-based summaries. | UX | console summary formatter | S151-02/S151-03 | renderer tests | PLANNED |
| REQ-151-03 | Summary retains workflow, phase, status, verified/failed/blocked counts where available, final status and evidence directory. | observability | formatter/result projection | S151-02/S151-05 | output assertions | PLANNED |
| REQ-151-04 | Full structured result data remains persisted to evidence/log files where required. | evidence | installer/evidence writer | S151-04 | evidence persistence tests | PLANNED |
| REQ-151-05 | Explicit machine-readable/debug JSON mode remains available. | compatibility | `--json`/`TSW_DEBUG_JSON` path | S151-04 | flag/env tests | PLANNED |
| REQ-151-06 | Output works in WSL2, native Linux and LXC-native setup paths. | platform | console adapters | S151-03/S151-06 | deterministic adapter tests | PLANNED |
| REQ-151-07 | Success/reset output tests reject raw JSON object dumps and assert important phase/status lines. | quality gate | `tests/test_package_entrypoint.py`, installer tests | S151-06 | focused unittest | PLANNED |
| REQ-151-08 | Errors retain recovery actions and evidence paths without hiding failure details. | resilience | summary/error formatter | S151-05 | failure fixture tests | PLANNED |

