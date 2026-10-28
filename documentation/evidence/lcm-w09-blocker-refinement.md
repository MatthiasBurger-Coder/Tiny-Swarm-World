# W09 Three Amigos: blocker disposition and guarded continuation

2026-10-25. Scope: #449 / parent #440, Classic native Linux and WSL2.
Requirement, architecture, Python and tester roles reviewed independently with
DevOps and Security support. No cross-host acceptance criterion was removed.
This records the 2026-10-25 checkpoint and is superseded for current scenario
statuses by the [qualification matrix](lcm-w09-qualification.md), updated
2026-10-26. In particular, WSL Q02 is now VERIFIED BOUNDED based on the later
attributed live result; this document's earlier Q02 partial/open assessment is
historical. The aggregate decision remains **INCOMPLETE**.

## Disposition at the 2026-10-25 checkpoint

| Concern | Native Linux | WSL2 |
|---|---|---|
| Capacity | Default 19 GiB remains correctly rejected; private 10/6/1 GiB passes the unchanged guard | Default capacity passes; not live deployment qualification |
| Standard ports | Scoped authorized disposal cleared collisions; subsequent native fresh campaigns executed serially | User explicitly authorized replacing all three WSL instances; guarded reset cleared default project; issue447 historical manager remained running |
| Fresh component observations | Actual complete new pinned bundle observations are captured before the existing single manifest commit; exercised live | Fresh Q05 pinned setup recorded exact source desired/observed child digests; tag-only Q04 correctly remained ineligible |
| Minimal foundation deployment | Verified empty optional phase repair and selected image forwarding implemented; corrected fresh native minimal passed | At this checkpoint, Q02 was PARTIAL/OPEN because attributable after/setup evidence had not yet been found. The later 2026-10-26 Q02 result supersedes this cell; see the qualification matrix's WSL Q02 record. |
| Product private infrastructure | Accepted ADR implemented and exercised in bounded official 0.4.0→0.5.0 prepared-Git migration | At this checkpoint WSL was unqualified; the later qualification matrix records bounded official Q14/Q15 transition and recovery results, while R35 remains a non-pass. |
| TLS environment | Distribution OpenSSL 3.5.5 explicitly selected; two custom OpenSSL 4 failures retained | Q04/Q05 hosted WSL TLS passed strict CA verification and WSL-local browser checks |
| Setup cancellation | Original real SIGINT UI hang retained; R38 regression and corrected native interruption/retry passed | At this checkpoint WSL setup cancellation/retry remained open; the later qualification matrix records bounded Q19 interruption/retry evidence, with broader variants still open. |

The native probe measured 20,111,052,800 effective RAM bytes against the default
20,401,094,656-byte requirement. Both hosts have eight CPUs; WSL measured
26,260,193,280 effective bytes. Swap or stopping workloads does not increase this
guard's total. The private native plan totals 18,253,611,008 bytes and changes no
CPU/disk/role/security checks. It does not qualify full Java stacks or sustained
load. Measured episodes show worker-2 reclaim at its 1 GiB limit; node swap and
OOM must remain separately reported from host swap already in use.

## Historical failures and operator amendments

The old W07 attempt remains `LIVE_FAILED_AFTER_MUTATION`. Its preservation was
not established and no later campaign turns it into a pass. The old helper hashed
volatile config fields; a changed aggregate hash alone does not prove corruption
or justify restoring an old snapshot over subsequent legitimate state.
Historical project/bridge/manager and private incident artifacts remain retained.
The stopped native historical manager was rechecked with its original UUID.

The operator subsequently required operation on this same native host and
explicitly allowed deletion of its current TSW installation and necessary bounded
extensions. This superseded the earlier spare-native-host recommendation and
native no-reset restriction. It did not authorize WSL disposal or unrelated
resource deletion. Guarded native reset verified ownership and absence afterward;
unrelated services and historical projects were preserved. Deleted original
installation data is not claimed preserved.

The operator waived further optional backups. One already verified manager export
is retained privately. No further exports or recovery imports were initiated after
the waiver. No complete original installation backup/restoration is claimed.
Product frozen-input capture and the required Portainer cold archive are separate
parts of the exercised upgrade protocols.

The first new minimal attempt failed after foundation creation because an empty
optional deployment phase was rejected. It also used 2.45.1 despite requested
2.45.0 pins because selected-stack environment buckets were absent. Both failures
remain recorded. Independently reviewed R36/R37 repairs preserve all endpoint,
authentication, selection and unsupported-contract guards. A separate corrected
fresh minimal installation passed, followed by actual Swagger addition, single
update, partial drift refusal and original-plan recovery.

Fresh Swagger and fresh Swagger/Traefik used separate clean baselines. Host
profile cleanup removed only canonical TSW proxy devices after proving there were
no consumers, preserving unrelated profile/network configuration. This was
explicit operator cleanup, not automatic deselection or an exposure-isolation
feature. Two failed custom OpenSSL 4 attempts were retained before a separately
verified distribution-toolchain attempt succeeded.

The original repeated-setup SIGINT reached deployment apply but hung waiting for
a nonterminal LinuxUI thread. Owned process cleanup retained the prior manifest.
R38 explicitly marks aggregate cancellation before joining that thread and
re-raises cancellation. The test failed on old code and passed on the repair.
Actual repaired SIGINT exited with -2, retained the previous manifest bytes and
completed an ordinary retry without reset or implicit adoption.

The operator then explicitly authorized replacing all three TSW instances in the
WSL2 default project and confirmed optional backups were unnecessary. The guarded
reset verified and removed exactly those three instances. The issue447 historical
project manager remained running; no unrelated project, pool or network was
disposed. Original WSL data is not claimed preserved or restored.

The first WSL Q04 tag-based installation had healthy Swagger/Traefik services,
strict TLS and browser proof. Its services update preview was correctly blocked:
the manifest had tag-only desired identities and no observations, while the live
registry index digests differed from the catalog's exact linux/amd64 child digests.
No observation fields were fabricated and no guard was weakened. A separately
fresh Q05 controller supplied all five admitted source child pins before its first
install. The existing observer then recorded matching live task facts, enabling a
Swagger single update and Swagger+Traefik batch call. Repeated target preview was
`no_op`; repeated live and normal setup completed with target identities and Swarm
service IDs retained. Portainer authentication and endpoint checks, strict TLS,
and Selenium UI/API checks passed. The full Q05 batch began with Swagger already at
target, so Q05 alone did not prove two-service source-to-target change.

A separate Q06 controller started from a new minimal installation, then added
Swagger and Traefik with their full source digest pins. This verifies WSL add-from-
minimal while retaining the Portainer foundation. The first actual two-service
source-to-target batch committed Swagger's stages and failed at Traefik. A correct
original-plan recovery first blocked before mutation because process-local image
overrides still described the source; after those temporary overrides were unset,
the same recovery selection restored all five source stages. Individual Swagger
and Traefik updates then succeeded, followed by a two-service `no_op` preview,
repeat setup with unchanged manifest/service identities, strict TLS, Selenium UI/API
and authenticated Portainer endpoint checks. This proves partial-batch recovery,
but not stop/resume or a successful batch in which both components change.

Q06 key hashes: add Swagger `178fd0eea4b8f90a17dd026b0ca4a2ce33237a8f7f4b6f44701b1b6a0d335997`;
add Traefik `8c53ac4e1b162396868629fc1898a965a1b41f8ed5540482574abbf5d74cabd7`;
batch partial failure `3797955e9d7dd6bab2f6dfc76008402c9a74490980162d6849edf7e852daefe1`;
successful original-plan recovery `2d4e1c2edb971ea67560990a89d3d3ccb6f7e093ecc3860dd37e514e1b60b380`;
Swagger single `218291b19b4953d71b44191f39a4a272c7014bc60baecc5da4aa98db543bf3aa`;
Traefik single `1ca16d5a63cc02cab14aea1939172a1122cb2e5e9898a739e74cb4e67618775c`.

## Isolation and remaining qualification

An Incus project does not isolate host listeners. Host preparation targets the
default project; profile, bridge, forwarding, preflight, access and browser contracts
must agree. Moving an instance between projects entails copy/deletion and is not
a UUID-preserving relabel. WSL disposal above is based on its own explicit user
authorization, not the earlier native authorization.

The bounded native Portainer fixture was operator-provisioned through the existing
Portainer API after closing/replacing direct-Swarm Swagger services. Changed IDs
precede its new baseline; no automatic ownership adoption is claimed. The bounded
product source was a real clean official prepared-Git 0.4.0 runtime with private
17 GiB input, not an old minimal CLI installation. Published 0.5.0 still has the
empty-apply limitation; its target setup APPLY is not claimed successful.

The accepted [effective-infrastructure ADR](../arc42/09_decisions/adr-product-effective-infrastructure-source.adoc)
preserves clean source, private frozen input, no-follow capture, explicit bounds,
source authority and three-way conflict refusal. Live acceptance remains distinct
from ADR approval and local tests.

Current source passed the clean isolated seven-gate run: 2,952 tests, 18 skipped,
43 architecture tests and typecheck across 895 files. Focused Python 3.12:
125 tests passed. Earlier counts are historical repair baselines. Independent audit
accepted the consolidated native batch, strict HTTPS, repaired setup interruption
and final retention records. WSL partial-batch recovery is now evidenced, but
stop/resume, Portainer/product upgrades and recovery, setup cancellation, applicable
control variants, cross-host AC1–AC5 and independent completion review remain open.
