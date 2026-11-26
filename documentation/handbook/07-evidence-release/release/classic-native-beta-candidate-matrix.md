# Classic Native Linux beta candidate and test matrix

**#514, 2026-11-24 — RC-6 draft recorded, qualification pending.** The [beta epic #513][513] requires one target revision for guided fresh installation, product upgrade and interrupted upgrade recovery. The draft records the version and initial source baseline. The revised candidate and final artifact inventory remain open.

| Baseline | Version and revision | Established source capability |
| --- | --- | --- |
| Published RC-5 | Release `0.5.0`, `b3de7fa16e24c5702d61f855851c6c3255871489` | Only admitted product upgrade target. The published checkout predates the guided setup and does not ship the newer upgrade controller. |
| [RC-6 GitHub draft][rc6] | Intended tag `0.6.0`, `eaf1bdb28779a1e6c4b217d8d36907dde5fc4739` from `main`, package metadata `0.2.0` | Includes `./setup_linux.sh` and the controller for the historical transition. GitHub confirms draft status, the full target SHA and zero uploaded assets. The tag is absent from origin. |

The proposed RC-6 source sets the package and fresh installation manifest version to `0.6.0` and implements an upgrade path for directly installed RC-5 on native Linux. The GitHub draft still points to the earlier commit above. Bind the draft to a committed and verified replacement revision before using it as a release record.

The documented prepared-Git product path is **0.4.0 → 0.5.0**. Its legacy source is official `0.4.0` at `346f4a43dbdc43380e7bc703ab185bc06746965b`. The controller requires an official GitHub release, rejects draft and prerelease records, and checks the resolved tag against the pinned target SHA. An arbitrary checkout or beta prerelease tag cannot enter this path. The release decision must cover how the candidate is resolved for testing. Component updates and setup reconciliation use separate operator paths. See the [product upgrade guide][upgrade], [target admission code][admission], [release resolver][resolver], [native setup guide][setup] and [RC-5 publication][rc5].

## Source and artifact identity

The source distribution for guided setup must retain Git metadata. Use an official Git checkout at the full SHA above to review the draft. The final operator distribution must identify its verified Git ref and commit. GitHub-generated ZIP and tar archives omit the required metadata. Record the SHA-256 of any distributed package or Git bundle from its actual bytes, and the observed service-image digests in each live run. The following hashes identify draft and historical inputs. Release artifact checksums remain pending.

| Exact input | Recorded identity |
| --- | --- |
| Native setup Git tree at `eaf1bdb2` | `c60edadeadf728f7ea2b59b1d801a50efb8437f7` |
| Native setup root `setup_linux.sh` SHA-256 | `7500e7ce599fa85efbfc723228b021028f3d67f56022ac2e0cc1215d8722b8c6` |
| `requirements.lock` SHA-256 at RC-5 and at `eaf1bdb2` | `ac9474784f50b87087e5e24a5a3163118aaf1f2845597d07f7dfa86eb713ff08` |
| Official `0.4.0` `requirements.lock` SHA-256 | `0b491230b9d4630bf34d36f70d1489a04d7c563472369788ee5c392bc56a2767` |

## Open release decisions

1. Assess published RC-5 (`0.5.0`) as the proposed source for RC-6. Verify how a supported, healthy `service-access` installation at that revision is obtained and inventoried. [W09][449] records an empty-install apply limitation at `0.5.0`. If fixture provenance requires the historical `0.4.0 → 0.5.0` transition, verify and document that prerequisite with the full Classic selection. The historical narrow fixture only covers Incus and Portainer.
2. Verify the RC-5 → RC-6 [upgrade commands][upgrade] on the replacement revision. RC-6 resolution requires an official published release or prerelease whose target commit SHA matches the tag. A draft is ineligible. Record the management checkout by SHA and Python environment.
3. Verify the configuration migration from `infra/` to `modules/tsw_core/infra/` on the direct prepared-Git RC-5 fixture. The migration carries explicit memory overrides by node identity, uses target defaults in the configuration for unoverridden nodes and rejects unrelated overrides. Compare the migrated YAML and the live Incus `limits.memory` of each overridden node separately. Test preflight, migration, interruption, resume and repeated verification without changing service images, effective credentials or unrelated state. RC-5 installations with an existing managed activation remain outside this path.
4. Record the final target SHA, ref and distributed artifact checksums. Rebind the draft to the verified SHA and attach its applicable green checks before handing off to #516. #513 owns release scope. [#440][440] supplies lifecycle evidence and [#488][488] supplies setup evidence.

## Proposed first qualification scope

- Native Ubuntu 26.04 x86_64 on an isolated or restorable physical host, Linux-native filesystem, ordinary sudo-capable operator, interactive terminal, Git and access to package, dependency and image sources. Reserve at least 8 CPU threads, 18 GiB RAM and 120 GiB free space for the guided `service-access` preset, plus any additional planned capacity and the documented upgrade staging space. Ubuntu 24.04 has a documented setup path and needs its own run if included in the release claim.
- The [historical setup audit][setup-audit] records Ubuntu 26.04 with Python 3.14.4, Incus package 6.0.5-8 and Docker package 29.1.3-0ubuntu4.1. The historical upgrade uses a prepared Python 3.12 environment and three managed Incus/LXC nodes running Docker Swarm. Capture exact Ubuntu point release, kernel, setup and management Python, Incus, Docker Engine, dependency locks and image digests before accepting a fixture. Recheck the admitted runtime versions for the final transition.
- Fresh fixture: clean Ubuntu baseline, no prior TSW nodes, Swarm state, service volumes, setup checkpoints or leftover TSW ingress rules. Capture baseline ownership of Incus resources, routes, firewall and ports, disk/RAM headroom and the restore point. Use the public [Quickstart][setup] and an operator outside the implementation.
- Upgrade fixture: clean official RC-5 Git checkout and healthy independently inventoried `service-access` installation, subject to source admission above. Preserve its installation manifest and capture the actual reader/schema and provenance. Propose an owned external infrastructure copy with a typed node-memory override following the historical `provider-memory-v1` policy. Confirm that the new transition admits and migrates it, then verify effective memory on each node before and after activation. Seed a durable Portainer tag and a Nexus repository artifact with a known content hash. Use existing operator-owned test credentials to log in before and after. Record symbolic credential sources and login outcomes.
- Required services: Incus foundation, Portainer, Traefik ingress, Nexus, Jenkins, Pulsar, SonarQube, Swagger, Infisical and Service Access. Check three Swarm nodes Ready/Active, desired and observed task state, Pulsar bootstrap completion, host-side DNS, TLS trust and ingress on 80/443. From the operator environment verify `https://<name>.tsw.local` for `service-access`, `portainer`, `infisical`, `nexus`, `jenkins`, `pulsar`, `sonarqube` and `swagger`, and the authenticated `https://pulsar-api.tsw.local/admin/v2/clusters` request. Open the Service Access links, load Swagger UI and its API definition, authenticate to services with login surfaces, and check Portainer's Swarm endpoint. Use the canonical [service list][services] and RC1 acceptance tooling for exact checks.

## Mandatory live scenarios for #516

All scenarios are pending candidate fixation. Live state for this planning work is `LIVE_CONSENT_MISSING`. Use explicit live authorization, independent restorable fixtures for regular and interrupted upgrades, and approved observation from the operator environment. Keep no concurrent installation writers. Retain redacted evidence per scenario with exact executed SHAs and artifacts, host/profile and versions, baseline/restore reference, timestamps, commands and exit codes, before/after identities and state, evidence hashes, cleanup/recovery and explicit result.

| Case | Procedure and prerequisite | Pass condition and retained evidence |
| --- | --- | --- |
| BETA-02 · Fresh setup | Use the pinned official checkout on the clean host. An independent operator follows the public Quickstart, including plan review and guided apply through `./setup_linux.sh`. Use only documented operator actions. | Setup completes, swarmed services are healthy, all required functional checks and applicable logins succeed. Retain operator steps, setup outcome, resolved selection and digest inventory, endpoint/authentication results and host ownership comparison. |
| BETA-03 · Regular upgrade and repeat | Use the healthy RC-5 fixture, known data and credentials, and admitted override. From the separate management checkout use `product upgrade --to 0.6.0` with `--preview`, then with `--live` after consent. Repeat the completed operation. | Activated product reports the candidate SHA/version and lock; runtime, selection, override, data markers, existing credentials and all required endpoints pass. Repeat returns a verified no-op with unchanged identities and state. Retain preview, successful apply, active launcher identity, fixture comparisons and repeat output. |
| BETA-04 · Interrupted upgrade and recovery | Start from a separate restorable source fixture. For the historical controller use an isolated owned CLI process and a read-only observer of the protected product journal. On the first matching durable `staging` stage, send one SIGINT to the owned CLI. Capture the operation identity and actual exit. A missed stage is inconclusive. Reconfirm the checkpoint and stop mechanism against the selected controller before running. Use documented `--recover --preview`, then consented `--recover --live` from the same management environment; preserve the checkpoint and source. | Prove interruption after upgrade started, recovery to a documented steady version and full service readiness, data and override preservation, and working existing logins. Retain the observer record, retained stage and interruption exit, recovery commands/exits and verification. A supported restoration to the source can satisfy this case with equivalent proof. BETA-03 still requires the target upgrade. |

## Evidence crosswalk and handoff

| Source | Reuse by case | Remaining gap and owner |
| --- | --- | --- |
| [#440][440], [#449 W09 qualification][449] | BETA-03/04. Q14/Q15 provide historical transition, checkpoint interruption and repeat patterns. W09 documents native `staging` interruption, override preservation and subsequent `no_op` for the historical pair with a narrow Incus/Portainer fixture. | Different target, management overlay and service selection. W09 records source-provenance limits and superseded attempts. Current full-profile upgrade and recovery remain open under #516 once #514 fixes the target. |
| [#450 W10 audit][450] | BETA-03/04/05. W10 audit rows P01, P07–P09 and P11–P15 provide lifecycle, evidence and operator documentation references. | The dated audit records bounded and open items. #517 adjudicates current evidence by exact candidate SHA. |
| [#488][488], [#530][530] | BETA-02. Guided setup contract, bounded post-install setup resume, direct-host NAT preservation, successful preflight and dry-run. | #488 closed administratively. Clean-host walkthrough and complete functional/authenticated acceptance remain #516 work. Setup resume is a separate operator path from product recovery. |
| [#294][294], [RC1 contract][rc1] | BETA-02/03/04. Reuse scenario structure, native verify probes and authenticated Browser/API runner under `modules/tsw_core/tests/e2e/classic/` after checking current routes and assets. | RC1 acceptance applies to its frozen revision and isolated profile. Re-run required checks on the final #516 candidate. |
| [#503][503] | The setup baseline ships root forwarders, `modules/tsw_native_linux` native tooling, and `modules/tsw_core` runtime, configuration and tests. | Verify the final release tree and entry points in #514. Earlier root/infra layouts do not attest this layout. |
| [#516][516] | BETA-02. Existing 17/17 native Browser/API checks show bounded service access on the recorded working copy. | Different revision and operator conditions. Clean guided install, verified upgrade and recovery for the pinned target are outstanding. |

The setup baseline already has [Quality][quality], [Compatibility][compat] and [SonarCloud][sonar] results. #517 must bind the applicable green gates to the final selected SHA and independently review the #516 runs before a release Go decision.

[513]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/513
[516]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/516
[440]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/440
[449]: ../evidence/lcm-w09-qualification.md
[450]: ../evidence/issue-450-epic-audit.md
[488]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/488
[setup-audit]: ../evidence/issue-496-native-setup-acceptance.md
[530]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/pull/530
[294]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/294
[503]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/503
[rc1]: ../evidence/classic-public-beta-rc1-scenario-contract.md
[rc5]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/releases/tag/0.5.0
[rc6]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/releases/tag/untagged-b64683cc867a928f8368
[upgrade]: ../../03-user-guide/user_guide/product-upgrades.md
[setup]: ../../03-user-guide/user_guide/installation.adoc#native-linux-quick-start
[services]: ../../03-user-guide/user_guide/usage.adoc#open-the-services
[admission]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/blob/eaf1bdb28779a1e6c4b217d8d36907dde5fc4739/modules/tsw_core/src/domain/lifecycle/product_upgrade.py
[resolver]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/blob/eaf1bdb28779a1e6c4b217d8d36907dde5fc4739/modules/tsw_core/src/infrastructure/adapters/lifecycle/product_source.py
[quality]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/actions/runs/45453197492
[compat]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/actions/runs/45453197459
[sonar]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/actions/runs/45455605948
