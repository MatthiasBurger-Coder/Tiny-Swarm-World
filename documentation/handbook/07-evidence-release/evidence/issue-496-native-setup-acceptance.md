# UX-08 native Linux release acceptance

**Decision: BLOCKED.** The checkout quick start is available for candidate use.
Keep the [one-command setup EPIC #488][488] open until all required live results
are attributable to the release candidate. This audit covers runtime baseline
`8d79007a2768c2119f1fcd19dc9851755ade3dd3` and its documentation. Release
`0.5.0` does not contain the guided entry point.

## Evidence reviewed

- [UX-04 #492][492] shipped the root handoff to native preparation and ordinary
  installation. [UX-05 #493][493] closed as not planned. Presets
  `service-access` and `default` can apply. Minimal and custom are
  selection previews. The [lifecycle contract][lifecycle] remains the catalog
  and selection authority, including the separate [#440][440] operations.
- [UX-07 #495][495] closed as not planned. Its retained local audit recorded
  18 targeted tests passing and the full QUALITY.md gate passing on the
  exact runtime baseline above (3,984 tests, 19 skips). Its native Ubuntu
  26.04 x86_64 host reported Linux 7.0.0-44-generic, Python 3.14.4, Incus
  package 6.0.5-8 and Docker package 29.1.3-0ubuntu4.1.
- UX-07 recorded `./setup_linux.sh --preflight --profile service-access`
  exit 2 for insufficient free disk, `--preflight --profile default`
  exit 2 at network inspection, and `--preflight --profile minimal`
  exit 2 for an unavailable guided profile. `--dry-run --profile minimal`
  exited 0 with the Incus and Portainer selection. The host had an existing
  Incus environment and insufficient spare capacity for a qualifying
  isolated guest. No live apply ran under UX-07.
- [UX-06 #494][494] recorded a bounded live recovery case on an isolated
  native Ubuntu 26.04 Incus VM at
  `fc1e930c33e3bd1767f6b86266590ffabb913457`. With `service-access`, the
  installer exited 0 before the wrapper was interrupted (exit 130).
  `./setup_linux.sh --profile service-access --verbose --resume` exited 0
  without another apply. Recorded journal, manifest, Incus and Swarm identities
  and a PostgreSQL marker matched across resume. Portainer login and marker
  readback succeeded before and after. The runtime files match those in
  [merged PR #528][528]. The result covers the
  post-install checkpoint recovery boundary.
- Historical [#363 behavioral evidence][363] and [#452 bootstrap work][452]
  concern their own source and workflows. [#313 architecture boundaries][313]
  remain applicable to the guided handoff.

## Parent acceptance matrix

| Criterion | Implemented contract | Evidence and disposition |
|---|---|---|
| AC02 | `setup_linux.sh` drives preparation and installation on native Ubuntu. | **Open.** UX-07 lacked a clean qualifying target. The UX-06 isolated fixture used a developer-host registry mirror and tested a specific recovery boundary. A clean operator walkthrough remains `LIVE_PREREQUISITE_MISSING` for the claimed candidate matrix. |
| AC03 | Root forwarding script delegates to the native wrapper. The wrapper uses existing preparation, installation and lifecycle planning. | **Satisfied by source inspection.** The existing preparation and installer entry points, service catalog and infrastructure owners supply the implementation. |
| AC04 | Preflight and dry-run use read-only inventory paths. Apply requires scoped consent and unsupported options or profiles are refused. | **Partial.** UX-07 automated checks, insufficient-disk refusal and profile controls are recorded. Live port-conflict, insufficient-RAM and full refusal/preservation controls remain open. |
| AC05 | Existing network preparation owns bridge planning, ownership guards and backups. | **Open.** The UX-07 default-preset probe stopped at network inspection. Conditional changes, preservation and applicable reversal plus DNS, published ports and browser access need qualifying observations. |
| AC06 | Ordinary install reconciles. Resume verifies checkpoint and scope, then re-observes pending work. | **Partial.** UX-06 proved bounded post-commit interruption recovery and preservation. Ordinary repeat, login or host restart and other interruption boundaries with preservation of managed and unrelated state remain open. |
| AC07 | Guided output separates preparation, installation completion and service access. Normal completion references the credential source and reports service access as unverified. | **Partial.** UX-06 observed Portainer and PostgreSQL within its fixture. The guided report still needs per-service health and verified URL output. Recovery of an already completed install reports completion only. Qualify the resulting report, including the protected credential reference, in the release walkthrough. |
| AC08 | README and installation guide use the shipped commands. | **Partial.** The root scripts and arguments match source. UX-07 targeted tests and full quality passed on the runtime baseline. Exact-source fresh-host, repeat and recovery results for the release matrix are incomplete. |
| AC09 | Guided setup uses the local Classic installation path. Upgrade and component updates have separate commands. | **Satisfied by source and documentation review.** The documented scope excludes upgrade, runtime replacement, destructive reset, generic multi-host provisioning and production or HA guarantees. |

The remaining release evidence includes a clean or restorable, capacity-qualified
native Ubuntu host per claimed version and preset, and an approved run recording
the exact SHA, versions, commands, exits, redacted before/after state and service
observations. Guided minimal and custom apply remain outside the shipped scope.

[488]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/488
[492]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/492
[493]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/493
[494]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/494
[495]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/495
[528]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/pull/528
[313]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/313
[363]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/363
[440]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/440
[452]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/452
[lifecycle]: ../../01-product/contracts/lifecycle.md
