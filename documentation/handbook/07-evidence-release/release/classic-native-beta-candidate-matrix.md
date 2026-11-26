# Classic Native Linux beta candidate and test matrix

**#514 — RC-6 follow-up qualification matrix.** The [beta epic #513][513]
uses one published target for guided setup, product upgrade and upgrade
recovery. The [0.6.1 release record][rc6] binds the follow-up tag, full SHA
and checksums when published. The sudo repair was integrated in [PR #531][531].

| Baseline | Version and revision | Use |
| --- | --- | --- |
| [RC-5][rc5] | `0.5.0`, `b3de7fa16e24c5702d61f855851c6c3255871489` | Direct prepared-Git upgrade and recovery source. Its historical package version is `0.2.0`. |
| [RC-6 initial candidate][rc60] | `0.6.0`, `0cd3d7b306201fe61ade73241bfbec53c8b8e559` | Guided preflight and dry-run passed. The live attempt stopped during scoped Incus admission when the recorded terminal lacked a sudo timestamp. |
| RC-6 follow-up | `0.6.1`, exact SHA in the [release record][rc6] | Common target for the three #516 cases. The guided recorder now authenticates sudo in its own terminal. |

## Source and artifact identity

Use the official Git checkout for setup. Verify the full release SHA and Git
tree against the release record. GitHub ZIP and tar downloads omit the Git
metadata required by setup. The distribution is the official Git checkout.
Record any supplemental package, bundle or image by the digest of the bytes
actually used.

The documented [upgrade entry point][upgrade] accepts direct native
`0.5.0 → 0.6.1` and retains recovery for existing `0.6.0` targets. It compares
the official release target commit, tag and package metadata, then binds
that identity and dependency lock into the checkpoint. Older
`0.4.0 → 0.5.0` evidence supports the historic transition only.

## RC-5 fixture preparation

Build or identify a directly installed official RC-5 `service-access`
baseline. The published RC-5 empty-install apply limitation is recorded in
[W09][449]. The historical narrow Incus/Portainer fixture does not satisfy
full Classic. Require provenance for the released checkout and the actual
running selection. Preserve the manifest and checkout. A prior managed
activation via `0.4.0 → 0.5.0` is outside the direct-upgrade path.

Prepare an owned protected copy of the RC-5 infrastructure with the
`provider-memory-v1` policy. An example fixture reduces worker 1 from
8 GiB to 6 GiB for 17 GiB total node allocation. Confirm actual host
capacity and measure each live node limit. Seed a Portainer tag and a
Nexus artifact with recorded content hash. Verify the existing logins and
record their symbolic credential source. Take a verified restore point
before exercising interrupted upgrade. Capture the actual fixture results
before marking this criterion complete.

## Native qualification scope

- Native Ubuntu 26.04 x86_64 on an isolated or restorable physical host, Linux-native filesystem, ordinary sudo-capable operator, interactive terminal, Git and access to package, dependency and image sources. Reserve at least 8 CPU threads, 18 GiB RAM and 120 GiB free space for the guided `service-access` preset, plus any additional planned capacity and the documented upgrade staging space. Ubuntu 24.04 has a documented setup path and needs its own run if included in the release claim.
- The [historical setup audit][setup-audit] records Ubuntu 26.04 with Python 3.14.4, Incus package 6.0.5-8 and Docker package 29.1.3-0ubuntu4.1. The historical upgrade uses a prepared Python 3.12 environment and three managed Incus/LXC nodes running Docker Swarm. Capture exact Ubuntu point release, kernel, setup and management Python, Incus, Docker Engine, dependency locks and image digests before accepting a fixture. Recheck the admitted runtime versions for the final transition.
- Fresh fixture: clean Ubuntu baseline, no prior TSW nodes, Swarm state, service volumes, setup checkpoints or leftover TSW ingress rules. Capture baseline ownership of Incus resources, routes, firewall and ports, disk/RAM headroom and the restore point. Use the public [Quickstart][setup] and an operator outside the implementation.
- Upgrade fixture: clean official RC-5 Git checkout and healthy independently inventoried `service-access` installation, subject to source admission above. Preserve its installation manifest and capture the actual reader/schema and provenance. Propose an owned external infrastructure copy with a typed node-memory override following the historical `provider-memory-v1` policy. Confirm that the new transition admits and migrates it, then verify effective memory on each node before and after activation. Seed a durable Portainer tag and a Nexus repository artifact with a known content hash. Use existing operator-owned test credentials to log in before and after. Record symbolic credential sources and login outcomes.
- Required services: Incus foundation, Portainer, Traefik ingress, Nexus, Jenkins, Pulsar, SonarQube, Swagger, Infisical and Service Access. Check three Swarm nodes Ready/Active, desired and observed task state, Pulsar bootstrap completion, host-side DNS, TLS trust and ingress on 80/443. From the operator environment verify `https://<name>.tsw.local` for `service-access`, `portainer`, `infisical`, `nexus`, `jenkins`, `pulsar`, `sonarqube` and `swagger`, and the authenticated `https://pulsar-api.tsw.local/admin/v2/clusters` request. Open the Service Access links, load Swagger UI and its API definition, authenticate to services with login surfaces, and check Portainer's Swarm endpoint. Use the canonical [service list][services] and RC1 acceptance tooling for exact checks.

## Mandatory live scenarios for #516

The initial RC-6 live attempt is retained as `LIVE_BLOCKED_BEFORE_MUTATION` for the guided install. The three scenarios for the follow-up need candidate-specific evidence. Use explicit live authorization, independent restorable fixtures for regular and interrupted upgrades, and approved observation from the operator environment. Keep no concurrent installation writers. Retain redacted evidence per scenario with exact executed SHAs and artifacts, host/profile and versions, baseline/restore reference, timestamps, commands and exit codes, before/after identities and state, evidence hashes, cleanup/recovery and explicit result.

| Case | Procedure and prerequisite | Pass condition and retained evidence |
| --- | --- | --- |
| BETA-02 · Fresh setup | Use the pinned official checkout on the clean host. An independent operator follows the public Quickstart, including plan review and guided apply through `./setup_linux.sh`. Use only documented operator actions. | Setup completes, swarmed services are healthy, all required functional checks and applicable logins succeed. Retain operator steps, setup outcome, resolved selection and digest inventory, endpoint/authentication results and host ownership comparison. |
| BETA-03 · Regular upgrade and repeat | Use the healthy RC-5 fixture, known data and credentials, and admitted override. From the separate management checkout use `product upgrade --to 0.6.1` with `--preview`, then with `--live` after consent. Repeat the completed operation. | Activated product reports the candidate SHA/version and lock; runtime, selection, override, data markers, existing credentials and all required endpoints pass. Repeat returns a verified no-op with unchanged identities and state. Retain preview, successful apply, active launcher identity, fixture comparisons and repeat output. |
| BETA-04 · Interrupted upgrade and recovery | Start from a separate restorable source fixture. Use an isolated owned CLI process and a read-only observer of the protected product journal. On the first matching durable `staging` stage, send one SIGINT to the owned CLI. Capture the operation identity and actual exit. A missed stage is inconclusive. Reconfirm the checkpoint and stop mechanism against the selected controller before running. Use documented `--recover --preview`, then consented `--recover --live` from the same management environment; preserve the checkpoint and source. | Prove interruption after upgrade started, recovery to a documented steady version and full service readiness, data and override preservation, and working existing logins. Retain the observer record, retained stage and interruption exit, recovery commands/exits and verification. A supported restoration to the source can satisfy this case with equivalent proof. BETA-03 still requires the target upgrade. |

## Evidence crosswalk and handoff

| Source | Reuse by case | Remaining gap and owner |
| --- | --- | --- |
| [#440][440], [#449 W09 qualification][449] | BETA-03/04. Q14/Q15 provide historical transition, checkpoint interruption and repeat patterns. W09 documents native `staging` interruption, override preservation and subsequent `no_op` for the historical pair with a narrow Incus/Portainer fixture. | Different target, management overlay and service selection. W09 records source-provenance limits and superseded attempts. Current full-profile upgrade and recovery remain open under #516 for the follow-up. |
| [#450 W10 audit][450] | BETA-03/04/05. W10 audit rows P01, P07–P09 and P11–P15 provide lifecycle, evidence and operator documentation references. | The dated audit records bounded and open items. #517 adjudicates current evidence by exact candidate SHA. |
| [#488][488], [#530][530] | BETA-02. Guided setup contract, bounded post-install setup resume, direct-host NAT preservation, successful preflight and dry-run. | #488 closed administratively. Clean-host walkthrough and complete functional/authenticated acceptance remain #516 work. Setup resume is a separate operator path from product recovery. |
| [#294][294], [RC1 contract][rc1] | BETA-02/03/04. Reuse scenario structure, native verify probes and authenticated Browser/API runner under `modules/tsw_core/tests/e2e/classic/` after checking current routes and assets. | RC1 acceptance applies to its frozen revision and isolated profile. Re-run required checks on the final #516 candidate. |
| [#503][503] | The setup baseline ships root forwarders, `modules/tsw_native_linux` native tooling, and `modules/tsw_core` runtime, configuration and tests. | Verify the final release tree and entry points in #514. Earlier root/infra layouts do not attest this layout. |
| [#516][516] | BETA-02. Existing 17/17 native Browser/API checks show bounded service access on the recorded working copy. | Different revision and operator conditions. Clean guided install, verified upgrade and recovery for the pinned target are outstanding. |

The [release record][rc6] identifies the checks for the released SHA. #517 reviews the candidate-specific evidence and the #516 results before a release Go decision.

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
[rc6]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/releases/tag/0.6.1
[rc60]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/releases/tag/0.6.0
[531]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/pull/531
[upgrade]: ../../03-user-guide/user_guide/product-upgrades.md
[setup]: ../../03-user-guide/user_guide/installation.adoc#native-linux-quick-start
[services]: ../../03-user-guide/user_guide/usage.adoc#open-the-services
