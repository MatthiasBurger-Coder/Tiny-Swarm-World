# Issue #218 Workflow Ledger

All FR workflows are serialized. Each next branch starts only after the
previous PR is merged, `main` is fast-forwarded, and its full gate remains
green.

| Order | Workflow | Branch suffix | Status | Dependency |
|---|---|---|---|---|
| 01 | FR-1 Host detection | `fr01-host-detection-20260712` | DONE / PR #220 MERGED / MAIN GREEN | baseline main |
| 02 | FR-2 Filesystem policy | `fr02-filesystem-policy-20260712` | WORKFLOW_CREATED / PUBLICATION_PENDING | FR-1 merged green |
| 03 | FR-3 Host resources | `fr03-host-resources-20260712` | PENDING | FR-2 merged |
| 04 | FR-4 Service resource profile | `fr04-resource-profile-20260712` | PENDING | FR-3 merged |
| 05 | FR-5 Incus limit validation | `fr05-incus-limits-20260712` | PENDING | FR-4 merged |
| 06 | FR-6 Memory pressure | `fr06-memory-pressure-20260712` | PENDING | FR-5 merged |
| 07 | FR-7 WSL network preparation | `fr07-wsl-network-20260712` | PENDING | FR-6 merged |
| 08 | FR-8 Host path/command cleanup | `fr08-host-paths-20260712` | PENDING | FR-7 merged |
| 09 | FR-9 Workflow observability | `fr09-observability-20260712` | PENDING | FR-8 merged |
| 10 | FR-10 Separate live steps | `fr10-separate-live-steps-20260712` | PENDING | FR-9 merged |
| 11 | FR-11 Outer timeouts | `fr11-outer-timeouts-20260712` | PENDING | FR-10 merged |
| 12 | FR-12 Check timeouts | `fr12-check-timeouts-20260712` | PENDING | FR-11 merged |
| 13 | FR-13 Hang diagnostics | `fr13-hang-diagnostics-20260712` | PENDING | FR-12 merged |
| 14 | FR-14 Native isolation | `fr14-native-isolation-20260712` | PENDING | FR-13 merged |
| 15 | FR-15 Installation evidence | `fr15-install-evidence-20260712` | PENDING | FR-14 merged |

No parallel group is approved because the workflows share evolving host,
preflight, composition, setup, CLI, evidence, tests, and architecture contracts.
