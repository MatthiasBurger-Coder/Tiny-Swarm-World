# LCM-W09 qualification matrix — issue #449

Status: **INCOMPLETE**, updated 2026-10-28. Historical bounded native Linux and WSL2 installation,
component-update, Portainer recovery and product recovery scenarios have executed
successfully. The WSL four-stage Swagger and two-service interrupted-batch paths
and selective `incus+portainer` fresh installation are verified. Remaining
failure/control variants, WSL override-survival and final-retention evidence keep
aggregate acceptance incomplete. AC1–AC4 remain partial; AC5 and W10 remain open.
Initial failed attempts remain failures alongside subsequent successful attempts.
The [P01–P15 traceability handoff](lcm-w09-ac5-traceability.md) is a draft and
has not received W10 owner acceptance.
WSL Q12 and LIVE-4 remain open; the [Q12 design proposal](lcm-w09-q12-design-proposal.md)
records the current implementation and live-operation NO-GO gates.

All WSL runtime snapshots through Q20 below are historical bounded
qualification evidence.
After the operator-authorized instance replacement on 2026-10-26, the default
Incus project is empty. A new R35 fixture has not been provisioned: fresh
read-only JIT found wildcard PortProxy routes and enabled `Remote-IP=Any`
inbound firewall rules for TCP 80, 443, 16080 and 16081 in addition to the
accepted Portainer route on 10001. Follow-up Requirements, Security and
Test/Evidence reviews conditionally accept leaving the four other paths
unserved. Architecture and DevOps found a differently named manager profile
incompatible with the pinned contract. The expected profile with only 10001 is
supported by the 0.5 verifier, but obtaining it requires a shared Incus profile
change that is not covered by the instance-replacement authorization; the
pinned 0.4 flow's compatibility is unverified. Keep the live replacement
scenario blocked pending the user's decision and source-backed review; the full
issue remains incomplete.

Sources: [#449](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/449),
parent #440 and [W01 scenarios LCM-S01–S12](../contracts/lifecycle.md).
Management baseline: `6d2f25ee843a01066fcdcfe4855666849513ff06` plus the
recorded candidate file hashes. This publication records no new live runs.
The generic component transition runner has changed since its historical live
run; see the transition proposal for both source hashes and the applicability
limits. #449 remains incomplete.

## Executed native boundary

Classic Linux → Incus/LXC → Docker Engine → Docker Swarm. The measured native
host has eight CPUs and 20,111,052,800 effective RAM bytes. Its default 19 GiB
plan remains correctly rejected. The supported private infrastructure input uses
10/6/1 GiB across the same three unprivileged nodes: 18,253,611,008 bytes.
CPU, disk, topology and admission/security guards remain unchanged. This qualifies
only the exercised minimal, Swagger and Swagger/Traefik selections. Heavy Java
stacks and sustained load were not part of #449/#440 acceptance and are not
claimed. Resource records include worker-2
reclaim at its 1 GiB ceiling; earlier measured episodes had no OOM or node swap.

Native Ubuntu 26.04.1, kernel 7.0.0-38, Incus 6.0.5 and node Docker 28.5.2 were
inventoried. Product-transition execution uses Python 3.12.15. The current
Swagger/Traefik campaign explicitly selects distribution OpenSSL 3.5.5 through a
private PATH selector and `/etc/ssl/openssl.cnf`. The host's custom OpenSSL 4
failed two earlier fresh attempts; those failures remain recorded. No OpenSSL 4
compatibility claim follows from success with the distribution toolchain.

The operator authorized disposal of the current native installation and waived
further optional backups. The guarded reset and fresh baselines were verified.
One earlier manager export remains private; no complete original-installation
backup or restoration is claimed. Product capture and the Portainer lifecycle's
required cold recovery archive remain part of those upgrade protocols.
Unrelated resources and the stopped historical incident project are retained.
The operator separately authorized replacing all three WSL2 TSW instances and
confirmed that no further optional backup was needed. The guarded reset removed
only the three `default` project instances; the historical `issue447-20261024`
manager remained running. The deleted WSL installation data is not claimed
preserved or restored.

## Cross-host execution matrix

`VERIFIED` means the bounded operation and independent observations in the cited
run records. It does not imply all variants or full issue completion. `PARTIAL`
retains explicitly missing controls. WSL2 is no longer globally blocked on
replacement consent or standard ports; each remaining cell reflects its own
executed evidence or open scenario.

| Scenario | Operation / W01 trace | Native | WSL2 |
|---|---|---|---|
| Q01 | Product/configuration/manifest/runtime inventory; S01 | VERIFIED for each new admitted native baseline | VERIFIED initial reset inventory and Q02–Q05 manifests; old three-node installation intentionally disposed |
| Q02 | Fresh minimal foundations and actual authenticated access; S08 | VERIFIED corrected retry; initial failure retained | VERIFIED BOUNDED: fresh minimal Incus+Portainer setup on synthetic source HEAD `933925e61f3d3153060950acb6afacbeb335e207`; exit 0/completed; three Running nodes, Swarm 3/3 Ready/Active, authenticated Portainer and local endpoint HTTP 200. Private post-state SHA-256 `CD601B79BF652D3D28699420317AB00E1F9B1FF4475F6F526B44D06F6E6AF0FB`; synthetic source does not qualify release ancestry or upgrades. |
| Q03 | Fresh Swagger, selected/omitted services and actual UI/API; S08 | VERIFIED separate fresh installation | VERIFIED Swagger selection, Portainer foundation, Swagger API/UI; no Traefik stack in Q03 |
| Q04 | Fresh Swagger/Traefik, routes, strict TLS and authentication; S08 | VERIFIED bounded fresh selection and strict HTTPS | VERIFIED tag-based Q04, then pinned-source fresh Q05 with strict CA, UI/API and auth checks |
| Q05 | Add Swagger, preserve foundation/data/auth/identity; S09 | VERIFIED | VERIFIED: Swagger and Traefik added to existing fresh minimal install; Portainer foundation retained |
| Q06 | Repeat setup/add, compare metadata and runtime; S09,S11 | VERIFIED reconciliation; no blanket literal-no-op claim | VERIFIED for Q06 add/update/repeat records |
| Q07 | Discovery/read-only previews and exact bundles; S04 | VERIFIED bounded catalog controls | VERIFIED exact single/batch source admission and target no-op previews on pinned Q05 |
| Q08 | Actual single update, task convergence and pin persistence; S05 | VERIFIED Swagger and Traefik new single intents | VERIFIED Swagger UI v5.32.6→5.32.7; target digest persisted and observed |
| Q09 | Actual explicit batch update and unrelated services; S06 | VERIFIED interrupted batch, forward resume and preserved unrelated state | VERIFIED: explicit batch changed Swagger UI and Traefik; other Swagger pins and managed identities remained stable |
| Q10 | Repeated update and subsequent normal setup preserve targets; S05,S06 | VERIFIED bounded single/batch repeats and later setup | VERIFIED bounded Swagger single update: target no-op preview and measured live repeat; manifest/journal hashes, Swarm service/task IDs, target digests, Portainer stack ownership, auth and UI/API availability stayed unchanged; subsequent setup retained the target |
| Q11 | Partial batch, stop/resume and original-plan recovery; S06 | VERIFIED bounded one-service and two-service selections | VERIFIED BOUNDED: four-stage Swagger selection and two-service Swagger+Traefik selection each interrupted at durable checkpoints, resumed, repeated and recovered; Q09/Q06 also cover ordinary batch failure/recovery. |
| Q12 | Portainer 2.45.0→2.45.1, protected data/admin/endpoint/managed stack; S07 | VERIFIED bounded W07 fixture | PARTIAL: protected candidates include one plausible completed wrapper, but it lacks run exit/time/source identity; the claimed second success is represented by a blocked preflight and a byte-identical wrapper. WSL Q12 needs uniquely attributed result and before/after evidence; LIVE-4 remains open |
| Q13 | Portainer SIGINT and API-down cold recovery; S07,S11 | VERIFIED BOUNDED; repeated recovery/no-op | PARTIAL pending artifact attribution: earlier summaries report SIGINT at `upgrading`, API-down cold recovery to 2.45.0 and repeat `no_op`, but R45 found malformed upgrade output and only an unlinked watcher stage label; recovery/verify/repeat files lack command/process linkage |
| Q14 | Actual prepared-Git 0.4.0→0.5.0 code/env/config/runtime; S02,S03 | VERIFIED BOUNDED: official-source provision, independently derived legacy inventory, live transition and direct completion proof | VERIFIED BOUNDED: official 0.4.0→0.5.0 prepared-Git transition, direct after-state and repeated live `no_op` |
| Q15 | Product interruption/recovery and literal repeat no-op; S03,S11 | VERIFIED BOUNDED: durable-staging SIGINT, recovery to 0.5.0 and repeated `no_op` | VERIFIED BOUNDED: attempt 3 captured SIGINT at `staging`, resumed the exact checkpoint to `completed`, verified target/runtime state and returned literal `no_op` on ordinary live repeat; earlier no-checkpoint failures remain preserved |
| Q16 | Source/runtime drift, dirty/moved/unknown sources and old/mixed tasks; S01,S02,S05,S11 | PARTIAL: actual Swagger drift refusal/recovery plus native dirty-checkout and nonofficial-origin product preview refusals; source/runtime variants and old/mixed tasks remain | PARTIAL: tag-only Q04 refused upgrade; Q05 exact source observations admitted; R52 verified bounded dirty-checkout/official-origin and clean/unofficial-origin preview refusals. R54 is a relocated-checkout characterization whose output is consistent with source admission before the missing-adoption-manifest block, but its omitted `TSW_REPOSITORY_ROOT` value and runner prevent independent path binding. R61 adds current-candidate native and WSL2 previews of dirty+official-origin and clean+unofficial-origin refusals with the same retained source archive and separate run indices. No moved-path refusal or full upgrade preview was proven. Moved-source meaning, other source variants, runtime drift and old/mixed tasks remain open. No runtime-preservation claim is made. See [R52 evidence](lcm-w09-q16-wsl-r52.md), [R54 characterization](lcm-w09-q16-wsl-r54.md), and private `r61-native-current-q16-source-guards.md`. |
| Q17 | Foundation removal and unsupported targets/downgrades/deselection; S08,S10 | VERIFIED bounded foundation/downgrade/refusal and preview-only deselection controls | PARTIAL: candidate-controller 0.5.0 run verifies foundation removal, unsupported target, downgrade refusal and read-only selection previews; R63 adds a synthetic schema-v1 Swagger removal-impact preview on native and WSL2 with foundations/data retained. No installed optional-stack removal or live behavior is established; broader variants remain open |
| Q18 | Every mutation's help/input/preview/consent controls; S11 | PARTIAL: 42 actual LCM help/input/preview/consent controls; checkpoint-specific coverage open | PARTIAL: candidate-controller top-level/setup/add/remove/update/product help, syntax and EOF/declined consent across setup/add/remove/update/product; R62 adds refusal without checkpoint state; R65 adds one `n` refusal each for component/product recovery with strict-model-valid synthetic checkpoint files present, before journal lookup. Semantic checkpoint eligibility, accepted recovery and broader variants remain open |
| Q19 | Setup interruption, unchanged manifest and supported retry; S09,S11 | R38 live retry VERIFIED; original UI hang retained as failure | VERIFIED bounded setup interruption/retry; broader variants remain open |
| Q20 | Explicit final retention, health and W10 handoff; S12 | VERIFIED native target retention and independent bounded audit; cross-host handoff open | VERIFIED BOUNDED: final snapshot confirms three running Incus nodes, three Ready/Active Swarm nodes and two healthy Portainer services. The Docker stack was directly operator-provisioned; authenticated Portainer `/api/stacks` is empty as expected for this unmanaged stack. Cross-host W10 handoff remains open |

All rows trace to parent LCM-01–05 through lifecycle.md §7. Unit or mock results
do not fill live cells. Passing Selenium against the native host from WSL proves
native browser behavior; it does not qualify a deployment hosted inside WSL.

## WSL2 records and fixture distinctions

### Current WSL Q15 verifier diagnosis — 2026-10-25

The latest product-upgrade attempt used the clean official 0.4.0 source
`346f4a43dbdc43380e7bc703ab185bc06746965b` and candidate controller
`0349e18dcdd7ab13aae744fff9aba3530a42f394`. It exited 1 before creating a
product checkpoint; the watcher sent no signal, no product manifest was
committed, and no product upgrade mutation occurred. The retained CLI log SHA-256
is `77f82bf4f5b5579bbd4799a063d063bda0597db35a9aa4581b1b15823545af23`. The
initial diagnosis isolated `platform.verify` preflight, where
`SECRET-TSW_PORTAINER_ADMIN_PASSWORD` was absent from the controller process
environment despite an existing protected credential file and successful
Portainer API authentication.

The credential source was compared in memory with both the exact 0.4.0 and
candidate internal catalogs; neither matched. The adoption inventory was
corrected to `external_user_secret` (SHA-256
`ec42a95946e8b7d5d431542e11093a4675efcdd105da1a0ee36a58573bbee55e`). No
credential value or hash was recorded. The corrected read-only preview exited
0, remained `status=preview` with `adoption_required=true`, and has raw SHA-256
`7d92e14847f17a31922cbc1a3ab7de709052c1da61ee3d0ccc8632daa8c078aa`. With the
protected credential held in memory and passed only to the verifier process
environment, a subsequent read-only aggregate platform verify completed all
six targets; selected Portainer deployment readiness completed as well. These
checks did not run product upgrade or create a checkpoint. A later attempt-2
driver exited 1 at `2026-10-25T14:10:09Z` because the unauthenticated GitHub
core API quota was exhausted (`remaining=0`, reset
`2026-10-25T14:18:24Z`). It created no product checkpoint, sent no signal and
made no product/runtime mutation; retained log SHA-256 is
`e234b8f227373b932282087f409aeab16b1992051742116c3239e155df958247`. A new
attempt-3 driver changes only private output paths. At
`2026-10-25T14:22:27Z`, it sent one SIGINT to its owned product-upgrade process
at the exact `staging` checkpoint. The process exited `-2`; the checkpoint hash
remained `95b686bd2f5dc7e7cf8df1b68a9edd37af5218135b82c1636ee4f7ac45d8ab8b`,
the installation/source/target lineage matched, and no product manifest was
committed. Event/result/log SHA-256 values are respectively
`c68b33ae031d1fb484e07d4a4e5ba87e29f228ea8805634d74bdb2dd1120bfc2`,
`7642ea79afffa4b3411b2e7aeff7e6da090f174faf6c4a4f6e01ff32c8d83237`, and
`d8359d5b8170d96890df3467fe907e539d41227d4510a494175c30fc875ce31c`.

Fresh read-only post-interruption checks passed against the same checkpoint and
live runtime. Both the pending clone and target release were absent; the
candidate staging implementation recreates the same pinned clone when both
paths are absent, so no path was manually recreated. The cause of the pending
path's absence after interruption is not established. Recovery preview exited
0 with `status=preview`, `checkpoint=staging`, source 0.4.0 revision
`346f4a43dbdc43380e7bc703ab185bc06746965b`, target 0.5.0 revision
`b3de7fa16e24c5702d61f855851c6c3255871489`, exact target lock, and selection
`incus+portainer`. Its SHA-256 is
`e541b8cae65bc92a3cc805ee4910833f81b51dd5f25a8279d4b5be417876a8d1`; the
post-interruption baseline SHA-256 is
`7f56778090f08215f34758a4a1bf4f05b6670d66d00c1a14ac7d02bdda9f9469`.
Private sanitized byte-for-byte copies and the complete artifact hash index are
under `.tiny-swarm/evidence/issue-449/`. The read-only GitHub core quota check
reported 32 requests remaining; the final pre-mutation check reported 48. The
three independent requirement, architecture and quality reviews approved
exactly one `--recover` operation. Recovery exited 0 without the adoption
argument or another signal; the exact checkpoint advanced from SHA
`95b686bd2f5dc7e7cf8df1b68a9edd37af5218135b82c1636ee4f7ac45d8ab8b` at
`staging` to SHA
`16c4fe8b11c68784cb5e9eac6955429b348b37a3ce4461fe598387ad72082af7` at
`completed`, and the target manifest records release 0.5.0, revision
`b3de7fa16e24c5702d61f855851c6c3255871489`, and the exact target lock. The
isolated target environment passed `pip check`; the active product/code and
configuration pointers, launcher, selected config captures, service/task/image
identities, Portainer auth, endpoint, tag, volume and overlay were verified.
The ordinary live repeat, without recovery or adoption arguments, exited 0 and
returned literal `status=no_op`; checkpoint and manifest hashes remained
unchanged, and a second post-repeat runtime verification passed. Q15 is
VERIFIED BOUNDED for this WSL host and this selective `incus+portainer`
transition. This does not close the other Q16–Q19, W10 or AC1–AC5 obligations.

### Historical WSL retained state after Q15, before authorized replacement — 2026-10-25

A fresh read-only inventory at `2026-10-25T14:38:45Z` recorded the completed
Q15 target manifest SHA-256
`6291b175ba708f1baaaea151e4beece2578f4cff261a3e682acd111420ff7e123` and
completed product checkpoint SHA-256
`16c4fe8b11c68784cb5e9eac6955429b348b37a3ce4461fe598387ad72082af7`. The
target is official 0.5.0 revision `b3de7fa16e24c5702d61f855851c6c3255871489`;
the current source/controller are `346f4a43dbdc43380e7bc703ab185bc06746965b`
and `0349e18dcdd7ab13aae744fff9aba3530a42f394`.

All three authorized default-project Incus instances remain Running with UUIDs
`ee6c73bb-7413-4d78-aef4-733dddf465f4`,
`fd3b74cf-d163-4a02-81f1-302eed94bbf2` and
`416a6c4c-7676-43fb-91d7-b728abc238d4`; all three Swarm nodes are Ready/Active.
The Portainer service is 1/1 at 2.45.1 with task
`jcby4xv6x9ena6d4r6avfywkt` and image digest
`sha256:4d616db18cfeb5dd41a69c0958bc825c84483ea9cde1106eb82a5d26f3bd8b0e`.
Portainer Agent is 3/3 at 2.45.1 with the three expected task IDs and image
digest `sha256:38bc1dc7b8470eecbd979d444aa5d0a187dacf1245f2b54466f0f25f4c6d9a7c`.
Exact four task rows, node IDs, mount specs, secret names and API stack-list
response are captured in the private service-detail record SHA-256
`4ea7635a0a4763d9ed58f4957ae1f6b82071a74e17e8065baa4ecb660d9d8527`.
The `portainer_portainer_data` local volume remains mounted at `/data`; the
Portainer service references only `tsw_portainer_admin_password` from the four
listed Swarm secrets; the `service_access_link` overlay remains the same ID and
subnet. Portainer 2.45.1 authentication, local endpoint ID 1 and the Q15 marker
all pass. The same 24 Windows PortProxy mappings still target the current WSL
host; their private exact mapping snapshot SHA-256 is
`98960b54871d3dd86b6d2ba3ce2740f9ee7ddb7c4698b69fbcaf9ac3965a93e1`.
The separate Incus project `issue447-20261024` remains present and excluded.

The Docker stack `portainer|2` was directly provisioned by the operator with
`incus exec swarm-manager -- docker stack deploy -c
/tmp/tsw-q15-portainer-040-compose.yml portainer` (exit 0). Its two service IDs
in the provision record match the Q20 retained-state detail. The authenticated
Portainer API reports an empty `/api/stacks` list because this fixture was not
created through Portainer's managed-stack API. Treat this as VERIFIED BOUNDED
Docker/Swarm retention and health; do not claim Portainer-managed stack
ownership. Exact private snapshot and port-rule copies are indexed under
`.tiny-swarm/evidence/issue-449/`: the operator-provisioning record
`wsl-q15-baseline-and-preview.md` SHA-256 is
`35fde5753afc47957516a74a4668e1509dc939e591eb9970a3ccf55ef7e87507`; Q20
service detail SHA-256 is
`4ea7635a0a4763d9ed58f4957ae1f6b82071a74e17e8065baa4ecb660d9d8527`; and
the combined final inventory SHA-256 is
`1a7e78b3964713d035c15166bc9d802e5193b5cafd440d01b065ff0fd241cf85`.
W10 and cross-host handoff remain open.

The inherited W07 handoff in issue #449's comment record also remains an open
AC1/AC2/AC4 item. Its 2026-10-24 WSL run failed after mutation while preparing
the image; it reports the two original workers changed from Stopped to Running
and their Incus config hashes changed, with the cause unverified. The old W07
project is still inventoried separately. The later user-authorized replacement
of the three default-project TSW instances does not explain or restore that
distinct W07 worker/config drift.

### WSL Q17/Q18 read-only controls — 2026-10-25

The qualifying 22-case run used the clean management checkout at controller
revision `0349e18dcdd7ab13aae744fff9aba3530a42f394` with Python 3.12.15 against
the current WSL 0.5.0 installation. Every child process records cwd, PYTHONPATH,
the separate installed-source `TSW_REPOSITORY_ROOT`, and the resolved candidate
module path. Help
succeeded for top-level, setup,
services add/remove/update and product upgrade. Conflicting update syntax was
rejected; the Portainer 2.45.0 request was blocked as an unsupported catalog
target, and product target 0.4.0 was rejected by the product target contract;
these do not separately exercise a semantic downgrade guard. Incus and
Portainer removal requests returned the mandatory-foundation
diagnostic. Swagger add and setup selection returned read-only previews; setup
resolved to existing Incus+Portainer with no removal, so it is not optional-stack
deselection proof. EOF and
explicit `n` consent for setup, services add/update and product upgrade all
returned refusal with exit 2. No command included `--approve-live`.

Before/after captures at 14:50:26Z and 14:50:58Z have identical target manifest
and checkpoint hashes, adoption inventory hash, Incus/Swarm node identities,
service/task/image identities, volume/mount, secret references, overlay,
Portainer version/API endpoint/tag/stack count, Docker stack list and all 24
PortProxy mappings. The compared state has no changed field across those 14
items. The per-case raw record SHA-256 is
`075ec9347e6704863e55ca269d150e01fe7074d8fb62caeec4a003b2cc7f0095`; the
independent state/artifact index SHA-256 is
`1410f608ab7f17b14507b7ae8b9ecc6bfc9cbefaa3fcfb2c19a91633c4c251be`; its
version-identity companion SHA-256 is
`bad85835e96eb24607f1950dd885c6414defbb59b055c1058dcf406c0fdc9685`.
Exact-byte local copies are under `.tiny-swarm/evidence/issue-449/`.

An earlier exploratory run accidentally invoked the installed 0.4.0 launcher,
which does not implement `product upgrade`; its parser-invalid product cases are
retained as non-qualifying evidence and excluded from this result. The first
management-checkout run also lacked per-case import-context evidence and is
retained only as diagnostic. The qualifying run uses the current controller
checkout and records the resolved module path per process. This is still partial Q17/Q18: the
current manifest contains no optional Swagger stack, so the preview does not
prove installed-stack removal. The completed product checkpoint makes active
recovery-consent coverage inapplicable, and broader argument/control variants
remain open.

Historical evidence state before the 2026-10-26 Q02 result: raw operational
records remain private on the WSL host under
`<private-wsl-root>/tsw-qualification/issue449-wsl2-20261025/`; credentials, TLS private
keys and logs are not copied to the repository. In that earlier snapshot, Q02's
index contained only a pre-reset baseline and its fresh-install completion was
unverified. This statement is superseded by the Q02 live result below. Q03/Q04
retain their distinct installation/browser evidence. Q04 was preserved as a
successful installation/browser record, then closed by the authorized guarded
reset.

The separate `controllers/q05-pinned-swagger-traefik` fixture was genuinely fresh.
Before first setup it received all four exact Swagger plus Traefik `linux/amd64`
child digest pins already admitted by the transition catalog. Its setup observer
recorded matching desired and live task observations for all five components.
Both single and batch previews were admitted. Swagger UI v5.32.6→v5.32.7 single
update completed; the explicit Swagger+Traefik batch completed with Traefik
v3.7.4→v3.7.5 while Swagger was already at target. A subsequent batch preview
was `no_op`; the repeated live command and a normal setup repeat completed without
changing the manifest or Swarm service IDs. The manifest SHA-256 was
`92e2470a57cf8e27e53e6ec9ef6dfe2f21bb2dc69292023589dce81db19a3248` before and after
the repeated live command; target digests remained committed. Portainer 2.45.1, its
authenticated API and local endpoint ID 1 remained available. Strict TLS CA
verification returned 0, `/status` returned HTTP 200, and a WSL-local Selenium
run rendered the API title and `/status` operation.

SHA-256: single live `218291b19b4953d71b44191f39a4a272c7014bc60baecc5da4aa98db543bf3aa`;
batch/repeat live `ff0028f6629ccdbfb6aa97f796ac35db2e0c3db287299bbb905129cb5cef1120`;
target no-op preview `a69aeb67124a8f0afada63ee10aa2430d59081eb77a80e0d98b24f289996e486`;
repeat setup `4e985768252c1c0c27d85865403a367d2d62c8537c17118931e5f12e2680b7ef`;
browser proof `abeaacde08ce8408f0b84113afe2906c2191bb8feb29da59501dbee35572bfe3`;
Portainer API proof `7bba5182b5bc57b776454415b6b7ca8677802dd4ffaeba4f80498c4119b25b5e`.
The repeated live output hash matches the first batch result; task/service and manifest
observations are separately retained. The Q05 batch began with Swagger already at
target and therefore does not prove two-component batch change.

The separate `controllers/q06-addition` fixture started from a new minimal install.
Swagger and Traefik were added to that existing install with complete source child
digest pins. Their exact desired and observed source identities matched. The first
actual `swagger,traefik` source-to-target batch committed Swagger's four stages and
then failed at Traefik; its retained result is `q06-batch-live.json` (SHA-256
`3797955e9d7dd6bab2f6dfc76008402c9a74490980162d6849edf7e852daefe1`). A recovery
preview and the original-plan recovery were run. The first recovery command was
blocked before mutation by process-local source image overrides; after unsetting
those overrides, retrying the same original selection recovered all five stages
to their source pins. The successful retry record hash is
`2d4e1c2edb971ea67560990a89d3d3ccb6f7e093ecc3860dd37e514e1b60b380`. Separate
Swagger and Traefik single updates then both succeeded; their record hashes are
`218291b19b4953d71b44191f39a4a272c7014bc60baecc5da4aa98db543bf3aa` and
`1ca16d5a63cc02cab14aea1939172a1122cb2e5e9898a739e74cb4e67618775c`. The subsequent
two-service preview was `no_op`. Repeated setup retained manifest and Swarm service
identities. Strict TLS verification returned HTTP 200, the WSL-local Selenium
browser verified the Swagger UI/API, and authenticated Portainer API access returned
the local endpoint. Q06 provides actual add-from-minimal and partial-batch recovery
evidence, but does not cover stop/resume, Portainer upgrade/recovery, product
upgrade/recovery, or the remaining failure/control variants.

### R449-29–31 setup-observation source linkage — 2026-10-25

The Q06 live setup/add and repeat records are now tied to the exact observation
implementation. Its clean WSL controller checkout was commit
`51065016d7b507590c9c70ea6a8cea7a79d68a58` with zero dirty paths. The Q06 and
verified-candidate SHA-256 values match for `setup_observations.py`
(`605a31660c1d1ebebaf0101b222a83080eb4b086ad6aa7e01afedb38dcad32c9`),
`setup_state.py` (`ad7032f2cac1266b2eca7c1a401e6d5c5d9149f3259f4e9b50b01c9326835e16`),
`composition_lifecycle.py` (`44eb505e7c67888616fd62c98c3258901f0e79cda3fd2e770f9d0bc4a264bf65`),
`selective_setup.py` (`e6ead63e9507af9e1d08ed3708ea9c29b50c21cdd3d48cecf576583f97911039`),
and the three corresponding regression files. The current full candidate archive
SHA-256 is `2e36d0aac53f579de18baf4664b9e30c3b2d24e4289a7b6c4157a2a91cf13bcd`
with source manifest SHA-256
`6896c4e8ac9e663b104170d2ce64fcc6a071217e4b85d64366667cf121569683` and all
seven required quality gates passing.

Q06 completed minimal installation, added Swagger and Traefik with complete
desired/observed digest identity, and repeated setup while preserving the
manifest and runtime identities. Its before/after repeat manifest record files
both hash to `ec0906c56023ffbc6348f869edcb99e838d3930cc9b3fd5ff109541daf818f87`.
The private source-link index
`<private-wsl-root>/tsw-qualification/issue449-wsl2-20261025/r2931-q06-source-link.json`
has SHA-256 `6388d29a9cae88bcc262f97d95c04528179e8024ccaf780bd916f47effc3dc5db`.
Three-Amigos and independent quality review accept R449-29 and R449-30 as
VERIFIED BOUNDED WSL. R449-31 is VERIFIED CURRENT-CANDIDATE LOCAL: injected
observation failure, cancellation, redaction and no-commit/no-reset invariants
are covered in the indexed regressions and full gate; a destructive live failure
was not required. These bounded rows do not close Q15 or #449.

The separate `controllers/q07-portainer-source` fixture was prepared with source
digests before setup, then Portainer 2.45.0's cold-backup upgrade to 2.45.1 completed
all five recorded stages, including API verification and reapplying the existing
Portainer-managed Swagger stack. The protected journal records the source server
and agent digests, prior service IDs, volume, endpoint and ownership fingerprints,
the cold-backup digest, and `stage=completed`; its mode is 0600. Direct post-upgrade
observations returned Portainer 2.45.1, authenticated API access, local endpoint ID
1, Swagger stack ID 1 with resource `1_swagger`, and all four pinned Swagger services
at 1/1. Upgrade record SHA-256 is
`36490ae66c55c0e8f48f32b7137c3ffe18e670c9ad5e8d0ee2991eb14f519162`.
The process completed before a planned SIGINT could reach it, so this run does not
qualify recovery. Preview was correctly `status=preview`, `checkpoint=completed`,
and its recorded source members already contained target desired/observed digests;
the displayed transition label is static. Two subsequent consented live repetitions
returned `no_op` at 2.45.1. Between the second repeat's before/after captures, the
manifest SHA-256 remained `51dca0c529c7043755e1a87bd9c4ec8817d4f8dfdaef8c1dd2d1ca94f463c865`,
the completed journal remained `d8685d80e0785d62076b306661b23469ecb2b81b573450307b02c5064d9eb085`,
Portainer/Agent service IDs and target digests were byte-identical, endpoint JSON
hash remained `585a8ccad82c9990f2b41dd8886080146490c16dba116b3fd713349b92e7176e`,
and stack/ownership JSON hash remained
`4a6f07aa44f6ff833fa14224a803986024da5eb528cc330bf0a93164e9b597bf`. The live
repeat record SHA-256 is
`2d456d027e69553284b7ae98e2261d42adddccde0750777b425f8e74e6db36da`; API
authentication succeeded before and after, endpoint 1 and Portainer-managed
Swagger stack/resource 1/`1_swagger`
were unchanged. That settled checkpoint remained ineligible for recovery; Q13 was
later qualified on a separate fresh 2.45.0 fixture below.

A second fresh WSL fixture (`q08-portainer-recovery-source`) was then prepared
after the authorized reset of the three instances in Incus project `default`;
the protected `issue447-20261024` project remained running. Its initial upgrade
preflight safely failed before creating a checkpoint because the target
Portainer server and agent images were not cached on the manager. Those target
digests were pulled on the manager, and the retry upgraded the source fixture
from Portainer 2.45.0 to 2.45.1. The resulting protected journal records
`stage=completed` and cold-backup digest
`sha256:0e5c1c10edc78fa24d95da19419091a7c0f23c5881ab74f77c78708cf51ee4b2`;
the redacted upgrade result SHA-256 is
`36490ae66c55c0e8f48f32b7137c3ffe18e670c9ad5e8d0ee2991eb14f519162`.
The R46 read-only candidate review found that the `q08-portainer-upgrade.json`
candidate is a blocked preflight and is byte-identical to its preflight-failed
copy. Its `q08-portainer-upgrade-interrupt.json` wrapper is byte-identical to
the q07 completed wrapper and lacks a run exit, event time and source identity.
It therefore does not establish a distinct second q08 success. The one q07
completed wrapper remains a plausible result but does not uniquely bind its
source, command or exit to a scenario. Keep WSL Q12 **PARTIAL** pending
uniquely attributable command/result and before/after evidence. Neither wrapper
qualifies Q13 interruption. A separate fresh 2.45.0 fixture was reported for
Q13 on the current candidate, as detailed below; R45's later artifact review
keeps Q13 partial because its stage attribution is missing.

### Current-candidate WSL Q10 and Q13 records

The current candidate was transferred as a source archive with SHA-256
`5d6ed72d535cc7d46aa03e1289c1043ccbb26df878e9fdc3a9ed7b937dd7736d`; its
temporary snapshot HEAD was `0349e18dcdd7ab13aae744fff9aba3530a42f394`. This is
candidate provenance, not a published project revision.

Q10 used a fresh minimal setup (`q10-minimal-source.json`, SHA-256
`2793574984089d2678e943a9e37adc84188f40c8b30c4dcc2f98924f6018ef49`), then
added Swagger (`q10-add-swagger.json`, SHA-256
`aa174b218386d4e073cc58ec0408587eafd84123af54c3f3e7b6a6a59ad26f44`). Swagger
was recreated as Portainer-managed stack ID 1 on endpoint 1 with ResourceControl
ID 1 / `1_swagger`; the Compose SHA-256 was
`8a1e90f5cbfd807d9e5ea5d54b1f46a6cbc0e20485938232c668642dc5db8750`. The
authenticated API returned 200, endpoint 1 was present, all four pinned Swagger
services were 1/1, and ports 16080 and 16081 returned HTTP 200. The redacted
stack verification SHA-256 is
`2ca4bdfd56dd2b2c656dc85b1521c286f7d9bcd31cfeabb28880e577c86c6c17`.

The bounded Swagger UI transition v5.32.6 → v5.32.7 completed with the catalog
target digest `sha256:b96d57e3c8c658b2c83ce11e0d87a7ccc7aedcdc20eccd7e83d67dca857a5a27`
persisted and observed (`q10-swagger-update.json`, SHA-256
`218291b19b4953d71b44191f39a4a272c7014bc60baecc5da4aa98db543bf3aa`). A
read-only repeat preview returned `no_op`. The measured live repeat returned
`completed`, while before/after captures proved the runtime effect was a verified
no-op: manifest SHA-256 `3dc70a89a6313183737e10374701e3d3cf09d853ae2aacf9f3c2edb11829f3b5`
and component-update journal hash remained equal; service IDs/digests and task
IDs, Portainer stack/resource IDs, auth and
HTTP 200 UI/API checks also remained equal. Capture SHA-256 values are
`0ae9f20412290e6622eef725281d4e34518d92ea2217c8515ad7b0f77c296d2a` and
`ca272b5ce9a8ca2ecac267007d101f5598e22013e78e99e345bab24204f00f5b`; the
measured repeat result SHA-256 is
`218291b19b4953d71b44191f39a4a272c7014bc60baecc5da4aa98db543bf3aa`.
An earlier invocation with a mistyped UI image override was rejected before
mutation; no product failure is attributed to that operator-input error. The
subsequent normal setup succeeded with the exact target pin from the manifest
(`q10-normal-setup-retry.json`, SHA-256
`a38baea119952fb6d192fb3021b6655cf59962cef131063c1b9bd6dba7309ad7`). Its
before/after captures again showed identical manifest and journal hashes,
service/task IDs, endpoint and stack ownership, authentication and HTTP 200 UI/API
availability; capture SHA-256 values are
`ca272b5ce9a8ca2ecac267007d101f5598e22013e78e99e345bab24204f00f5b` and
`7c36237e7053355462066037240d15000c990b8b1a6cdb374452dfe7ad5c9551`.
This Q10 evidence is bounded to Swagger single update and subsequent setup. Q09's
explicit batch is separately verified in the current-candidate WSL record below.

Two additional Q11 signal attempts were watcher misses and remain non-qualifying.
The earlier Swagger run completed before its background process received SIGINT
(apply record SHA-256 `218291b19b4953d71b44191f39a4a272c7014bc60baecc5da4aa98db543bf3aa`,
exit 0); the supported recovery returned `recovered` (SHA-256
`038d297105eb315d31ff1babdb517a1fd280768f9ff8b744405396cc23f426c1`). The later
foreground Traefik run also completed before SIGINT (apply record SHA-256
`1ca16d5a63cc02cab14aea1939172a1122cb2e5e9898a739e74cb4e67618775c`, exit 0),
then supported recovery returned `recovered` (SHA-256
`5e21d56cd8f42703535389aad394606056fae55f97fefd6f8250bb4544811a15`). Direct
post-recovery capture SHA-256 `c748dd5b27577d5af89860f6b984bf14a405538234333f39af1f85880ecf5f1e`
recorded source Traefik digest `sha256:580f70e21a5b63503dcbd5690b432b0e78b056e931a1738a5ca2d997bd08bc47`,
Portainer authentication/endpoints HTTP 200, Swagger stack and services present,
and Swagger ports 16080/16081 HTTP 200. These runs establish completed transitions
and source restoration only; neither establishes interruption or resume. At that
point Q11 remained open for two-service interruption coverage; the successful bounded
single-service batch stop/resume below covers actual interruption and recovery.

### WSL Q11 bounded stop/resume and recovery

After the two watcher misses above, a process-group controller observed the
four-stage `services update --services swagger` batch while `swagger-ui` was in
`applying` and sent SIGINT to the command's process group. The controller record
`q11-swagger-interrupt-controller.json` has SHA-256
`025b937edcb7b608218bd8efe3c1029a8ef2c01e52c1d268a88aa742bb095a35`. It records
`trigger=applying`, `component=swagger-ui`, `signal_sent=true`, and process exit
`-2`; the journal retained three committed stages and the applying stage. This is
an actual bounded interruption, unlike the earlier watcher misses.

The interrupted CLI result is `q11-swagger-interrupted-run.json` (SHA-256
`5d73bc82704173eec56b22cf68dad966d958da8a3d91675cef62e1894ae86cbb`); the
direct interrupted-state capture is `q11-swagger-interrupted-state.json` (SHA-256
`5c1d7c6c88ce56d7fa5a14715a070083a50e1e53e0cceb1c74cc13170d85366d`). Resuming
the exact same selection completed all four stages. Its run result SHA-256 is
`218291b19b4953d71b44191f39a4a272c7014bc60baecc5da4aa98db543bf3aa`; direct
post-resume capture is `q11-swagger-after-resume.json` (SHA-256
`786cf4f57e9056a0dcdd3655560805e950fea53a9c30281f1a9e11db83ebff30`). The
supported original-plan recovery then returned all four stages to their source
pins. Direct post-recovery observation recorded source manifest SHA-256
`82c1b839ab1b6060a31f1b2381ae33a7b3f3ab676700c5cfc416682024f8747a`, authenticated
Portainer/API endpoint and Swagger ports 16080/16081 at HTTP 200, and source
service digests. A repeated recovery also returned `recovered`; it is not called
a `no_op`. Private run artifacts are under
`<private-wsl-root>/tsw-qualification/issue449-wsl2-20261025/`.

This qualifies actual interruption, same-plan forward resume and supported
recovery for one multi-component Swagger selection. It does not qualify WSL
product-upgrade recovery or the remaining Q14–Q18 variants.

### WSL Q11 bounded two-service interrupted batch — 2026-10-25

The direct runtime baseline and exact preview agreed before mutation; all five
component image override variables and `TSW_INFRA_ROOT` were unset, and no
competing writer or pending component journal existed. A process-group controller
sent SIGINT only after four Swagger stages were durably committed and Traefik was
applying. The CLI exited `-2` and retained the journal checkpoint. The same-plan
forward resume completed, a target repeat completed, and original-plan recovery
and its repeat both returned `recovered` for all five selected stages. The
recovery repeat is not described as a no-op.

Only Swagger UI and Traefik changed image digests in the target direction; the
other three Swagger stages were retained pins. Recovery restored the original
source digests. Both final direct captures showed stable service IDs and running
tasks, Portainer authentication, endpoint and stack API HTTP 200, and Swagger UI
and API HTTP 200. The two captures also had identical installation manifest and
component-journal digests. The private index
`<private-wsl-root>/tsw-qualification/issue449-wsl2-20261025/q11-two-service-evidence-index.json`
has SHA-256 `58505bee547cc9d42076c0032b93c97aaa8a86ba59820f3eadf2b8e466ae2eed`;
the final direct capture has SHA-256
`c2af54bac019c6542917dedcd28aa3bf78718dc95ee93bdd52dc8d94c7cf634a`.
Together with the prior four-stage Swagger result, this closes the bounded WSL
Q11 selection variants. It does not close WSL Q15 product interruption/recovery
or the remaining cross-host controls and acceptance criteria.

### WSL Q14 source-baseline investigation and final restoration (historical sequence)

The clean official 0.4.0 checkout remains at revision
`346f4a43dbdc43380e7bc703ab185bc06746965b`, with lock SHA-256
`0b491230b9d4630bf34d36f70d1489a04d7c563472369788ee5c392bc56a2767` and official
Portainer Compose SHA-256
`6d1573f7b62bf69eeee6e7af645e73f0322eeb182c55a1c5e209cd3aa23d78d8`. Read-only
CLI inspection confirms that 0.4.0 `platform init` provisions Incus nodes only;
Docker/Swarm installation is internal to setup, and `deployment apply` uses the
full profile. Its full-profile preflight failed on missing unrelated service
secrets. The existing `build-q14-adoption.py` is explicitly rejected: it copies
components from the newer candidate's manifest and then labels the product
release/revision as 0.4.0. No such inventory was passed to product-upgrade preview.

The operator authorized replacing all three WSL TSW instances and waived
additional optional backups. During the Q14 investigation, a reset removed the
three default-project instances, then a candidate-root initialization recreated
and verified them. A trial `setup run --minimal` was safely blocked before
mutation because it would implicitly remove the existing Swagger and Traefik
selection. The documented `services remove` path remains preview-only. A second
reset and a clean-checkout init attempt did not produce a reusable source
baseline; the unsuccessful fresh-root init output was empty. A subsequent
supported init through the existing candidate state restored all three managed
instances, and the exact existing `swagger,traefik` setup selection completed.

The final restoration result is `q14-restore-setup-result.json`, SHA-256
`49bbc9e4e2f03d03ed4a6f87c43d90c4881308766d8d72260ff736c477ccc2d9` (status
`completed`). The normalized direct runtime capture is
`q14-wsl-restoration-direct.json`, SHA-256
`9a6c9b4554c7b34726b03064d50497f4a33f46a481c5c4f3ce5acd98f5039c2c`: three
Incus nodes, nine running Swarm tasks across Portainer, Swagger and Traefik, all
selected image digests at their recorded pins, Portainer authentication and local
endpoint HTTP 200, and Swagger ports 16080/16081 HTTP 200. Portainer's managed
stack list is empty after the authorized data replacement. This is a healthy
current-candidate restoration, not an official 0.4.0 source baseline or product
upgrade evidence. The two resets do not claim preservation of the replaced data.
The separate platform observation `q14-final-platform-health.json` (SHA-256
`dcd80e765c0d16b31689812140b6712d83529348e03f6fd398b6110495270b3b`) records all
three Incus containers running and all three Swarm nodes Ready/Active.

### Native Q14/Q15 official-source product transition and recovery (2026-10-24)

The native product scenario was provisioned from the unmodified official 0.4.0
checkout at `346f4a43dbdc43380e7bc703ab185bc06746965b`, lock SHA-256
`0b491230b9d4630bf34d36f70d1489a04d7c563472369788ee5c392bc56a2767`, using
Python 3.12.15 and the official platform/Docker/Swarm/Portainer-only APIs. The
source remained unchanged. Independent live inventory used a separate legacy
adoption file because no canonical manifest existed; it recorded node UUIDs,
Portainer/agent service and task IDs, actual image IDs/RepoDigests, authenticated
endpoint 1, and a read-back preservation tag. It explicitly says the inventory
was independently derived, not retrofitted from a newer manifest.

The prepared-Git preview exited 0. The watcher sent SIGINT to the owned CLI after
observing durable `stage=staging`; the process exited -2 with that checkpoint
retained. Same-installation recovery completed to target 0.5.0 revision
`b3de7fa16e24c5702d61f855851c6c3255871489`, independently verified active code,
Python environment/lock pins and configuration. Manifest, runtime, tasks,
authentication, data and node identities were reported preserved. The repeated
product command returned `no_op` (exit 0). A prior recovery harness assertion
failed after recovery had actually succeeded; it remains a recorded failed
attempt and is superseded by the independent attempt-2 proof. The bounded claim
is limited to this pinned transition and observed `incus,portainer` selection.
The completion proof also records the ADR-governed `external-infra` binding
`effective-infra-d25989163e34494391e7e35b625619d5` under `provider-memory-v1`,
successful reuse of the originally bound authority with ambient `TSW_INFRA_ROOT`
unset, and a post-target active configuration check at 2026-10-24T17:13:26Z with
manager/worker1/worker2 memory still 10/6/1 GiB. This supports R449-35 for this
native transition only; WSL override survival and broader capacity are unqualified.

Private native records under
`<private-native-root>/tsw-qualification/issue449-native-20261024/product-transition-live/`
were inspected over SSH and rehashed. Key SHA-256 values: official source
provision `0563cb58ef2467b83c066a874b0ac7b9333b407babd1174c9531b6e1939fb352`;
independent source inventory `c4b2ab410be520f9042bbf428d4d236db1ba3d24c9db0463582493a996a01534`;
independent live inventory proof `dda27047e110c92d3b39dcb897b558af5376f15aded4f5d1545a43fc9cceb085`;
SIGINT record `7e9d1c41d7e515a830f02091999f4b5f4d3cf3d6b4fe40a224257c494ecef80d`;
independent completed recovery proof
`d0962ad0d48d5f05b3d95533076ccd1d26f1ecc36c215d2d033d537347e513dc`.
The earlier first-attempt harness failure remains preserved. No broad release,
all-service or ordinary target setup-apply claim follows from this bounded run.
The associated management controller is the private checkout at commit
`6d2f25ee843a01066fcdcfe4855666849513ff06` (dirty, 22 modified/untracked paths),
transferred from the tested candidate as a 57-entry overlay archive with SHA-256
`4d83f21af973c24968846c8d1e88d189535d7520ec7458f058cc3414db5febc2`. Its Python
3.12.15 interpreter SHA-256 is
`9b6fd06e487935c92477cb47cabbda8d814cda44823a5159eddf791178afe7d0`. The target
0.5.0 environment independently reports package 0.2.0, lock SHA-256
`ac9474784f50b87087e5e24a5a3163118aaf1f2845597d07f7dfa86eb713ff088`, all
lock pins installed and `pip check` exit 0. This identity is distinct from the
host's later clean main checkout.

### WSL Q14 official-source product transition (2026-10-25)

A later independent fixture closed WSL Q14; it is separate from the preceding
failed source-baseline investigation and restoration. The clean official source
checkout was `346f4a43dbdc43380e7bc703ab185bc06746965b`, with dependency-lock
SHA-256 `0b491230b9d4630bf34d36f70d1489a04d7c563472369788ee5c392bc56a2767`.
The prepared official target was 0.5.0 at
`b3de7fa16e24c5702d61f855851c6c3255871489`. A source/runtime reconciliation
and read-only preview succeeded before live consent was passed to the exact
controller and target. The live result is `completed` (exit 0); direct after-state
observation found 7 services and 9 running tasks, unchanged selected component
digests, Portainer authentication/endpoint/stack API 200, and Swagger API/UI 200.
Portainer's stack list was empty both before and after; this does not claim
preservation of absent stacks or data across the separately authorized resets.
The repeat live command returned `no_op` (exit 0).

Private evidence is on the WSL host under
`<private-wsl-root>/tsw-qualification/issue449-wsl2-20261025/`. The indexed aggregate
`q14-wsl-product-transition-evidence.json` has SHA-256
`3f3a5e0d4fbf0fee3fdcd2f2e972437dcedc210f8a4bda4ef71afecc43534fd1`. Its raw
preview, live result, direct after-state, repeat, inventory, and reconciliation
hashes are respectively `9e306e882cbc039c4b817e28102846bfdb9ed5bf8c183fac228b6efd1f582844`,
`a78f004c511ce390530de7be368fb4a6395dd2dbc4e81111bf59f26506d3b918`,
`1fe351ff233ccf8a0159020c49661c8b5121812cc668ad3d08133dd6903509d6`,
`ddf3b4b05153081bee8f1a2eb8dd9c8583e03725c01369268acba33f4aa63d3c`,
`54974cb0a1625d50bb6cc46bbb69915db2bc9bba6a1eb21a67591b89556fa82ae`, and
`8ab46d6409da12f6315eae919572a87868fc6515e3487d1a0da6b618793200b6`.
The aggregate records the authorized reset limitation, empty-stack baseline,
and still-open Q15/cross-host gaps. Q14 is VERIFIED BOUNDED on both hosts; native
Q15 is VERIFIED BOUNDED, while WSL Q15 product interruption/recovery remains open.

For Q13, a fresh Portainer 2.45.0 fixture used the same candidate and retained
the Portainer-managed Swagger stack. The watcher recorded `stage=upgrading` and
API status `000` at loop 39, then sent SIGINT. The unsettled checkpoint's cold
archive digest was `sha256:979bdd44c9a922368c84f05c960686c356af80e3f91e7b577a3926abae57d19e`;
the archive was mode 0600, size 153600 bytes, and its measured SHA-256 matched.
Recovery returned `recovered` at 2.45.0. Verification then found authenticated
Portainer API 200, endpoint 1, the same stack and ResourceControl IDs, source
server/agent images converged, all four source-pinned Swagger services 1/1 and
both Swagger ports at HTTP 200. Repeating recovery returned `no_op` at 2.45.0.
Private WSL evidence is under
`<private-wsl-root>/tsw-qualification/issue449-wsl2-20261025/`: watcher
`q13-watch.log` SHA-256 `dfca04ae50dc2b14335ee7b7e25d414abca8d2edb6cb5edecb99c223faa65117`,
upgrade result `q13-upgrade.json` SHA-256
`b3c1cef9bd925a8dd5de3e1a4a157ba84b54a47cfd4e7c178e3d12d8cc38494d`, recovery
`q13-recovery.json` SHA-256
`3c1e39f8ec29458de87297d9b66c7506751c714964708ad5150245f23c2c2e05`,
post-recovery verification `q13-recovery-verify.json` SHA-256
`f2df94bf2e771626cdd5849e90a455d5297ef598e89f13263479f7c6d006d469`, and
repeat `q13-recovery-repeat.json` SHA-256
`b13ffd3651020882f32084cddda8aea136e8ac90514850dd5a64f6049b5dc925`.

R45's independent artifact review supersedes the WSL `VERIFIED` summary above.
The sanitized index records only bounded recovery, post-recovery and repeat
fields. `q13-upgrade.json` is malformed as JSON; `q13-watch.log` contains
`stage=upgrading` but is not attributable to a specific process; the cache
logs were unreviewed at R45 (the later R51 redacted review is recorded below).
The recovery, verification and repeat files lack command/process linkage. WSL
Q13 is therefore **PARTIAL** pending attributable upgrade-stage evidence; WSL
LIVE-4 remains open.

## Native records and fixture distinctions

Reviewed redacted artifacts are retained under `.tiny-swarm/evidence/issue-449/`.
Raw journals, credentials, keys, cold archives and operational logs remain private.
The requirement matrix, test results and archive hashes provide the handoff index.

- `native-minimal-retry/`: corrected minimal install, authenticated browser,
  persisted Portainer tag, Swagger addition, single update, later setup, actual
  wrong-image partial refusal and supported recovery. A verified three-stage
  prefix committed before that drift refusal; this was not a pre-mutation refusal.
- Its W07 records: after closing the direct-Swarm case, the operator provisioned
  a separate Portainer-managed Swagger proof fixture through the existing API.
  Its changed Swagger IDs precede the W07 baseline. No automatic ownership import
  or preservation across fixture replacement is claimed. Actual interrupted
  upgrade, manager recovery with API unavailable, retained tag/auth/endpoints and
  managed stack, subsequent upgrade and ordinary setup were independently checked.
- `product-transition-live/` (source-provenance qualification superseded): the
  recorded source checkout was clean official 0.4.0 prepared-Git legacy source
  `346f4a43dbdc43380e7bc703ab185bc06746965b` to clean 0.5.0
  `b3de7fa16e24c5702d61f855851c6c3255871489`, exact Python 3.12 and locked
  dependencies. The record describes operator provisioning through official APIs,
  not an old minimal CLI install, but does not capture argv/resolved profile,
  configuration, environment inputs, rendered stack hash or command/API transcript
  for the Portainer-only apply. Official 0.4.0 `deployment apply` uses the full
  service profile, so this fixture's source provenance is UNVERIFIED. Actual
  interruption/recovery, effective 17 GiB migration, active launcher and unchanged
  runtime/data/auth were observed, but do not qualify Q14/Q15 until source
  eligibility is established. The
  published 0.5.0 empty-apply limitation remains; no successful target setup APPLY
  is claimed. Metadata package version 0.2.0 is distinct from release identity.
- `native-fresh-swagger/`: separate fresh Swagger baseline, actual OpenAPI/UI/API,
  omitted services, repeat reconciliation and unchanged identity/data/auth.
- `native-fresh-swagger-traefik/`: distribution-OpenSSL fresh attempt 3, actual
  five-stage batch interruption after Swagger commits, forward resume, exact source
  recovery and unchanged-state repeats. Strict HTTPS source/target/recovery browser
  records are separate. The original repeated-setup SIGINT hung in LinuxUI;
  R449-38 repairs cancellation status propagation. Attempt 2 exits on SIGINT,
  preserves the previous manifest byte-for-byte and succeeds on ordinary retry.

Earlier completed native fixtures were deliberately closed before the next fresh
installation. Their evidence proves recorded operations, not current availability.
Only the final retained case will establish the host's delivered running state.

## Verification and remaining work

### Current-candidate WSL Q09 batch — 2026-10-25

The explicit Q09 live batch completed with exit 0 from candidate archive
SHA-256 `5d6ed72d535cc7d46aa03e1289c1043ccbb26df878e9fdc3a9ed7b937dd7736d`
(snapshot HEAD `0349e18dcdd7ab13aae744fff9aba3530a42f394`). All four Swagger
components and Traefik were recorded as committed. Before/after captures show
Swagger UI and Traefik moved to their requested target digests; the remaining
Swagger component image digests and source identities were unchanged. All four
Swagger services and Traefik converged 1/1. Portainer authentication remained
HTTP 200, dashboard unauthenticated access returned 401 and authenticated access
returned 200, endpoint 1 and the managed Swagger stack/resource identities
remained stable, and Swagger UI/API ports 16080/16081 returned HTTP 200.

Private artifacts are under
`<private-wsl-root>/tsw-qualification/issue449-wsl2-20261025/`: batch result
`q09-batch-live.json` SHA-256
`ff0028f6629ccdbfb6aa97f796ac35db2e0c3db287299bbb905129cb5cef1120`, before
capture `q09-batch-before.json` SHA-256
`105f655f7a3faaf84994ca299bad6c60dd1ae666a366f943be9cdee16ffe11a4`, after
capture `q09-batch-after.json` SHA-256
`43843a9e5165d4f0f31e81a98ee2bd04794ccb00aa5bf3942f4ff0717c13e8cc`, and
dashboard authentication proof SHA-256
`060de950f21e59e20a13207153d3fd6c8b9fdff9051186b77cce2f78e9fc6326`.
This closes the bounded WSL Q09 batch scenario; it does not satisfy the separate
cross-host ACs or close #449.

### Current-candidate WSL Q19 setup interruption and retry — 2026-10-25

An owned repeated `setup run` was interrupted after the watcher observed
`deployment apply` with `status=started` while the CLI process remained alive.
SIGINT produced exit 130. Before/after interruption captures showed unchanged
manifest and component-update journal hashes, Swarm service/task IDs, Portainer
stack/resource ownership, authenticated Portainer API, and Swagger HTTP 200 on
ports 16080/16081. An ordinary supported setup retry exited successfully and
the same captured state remained unchanged. This qualifies only the bounded setup
interruption/retry path; it is not product-upgrade recovery or general Q16–Q18
variant closure. Private artifacts in the directory recorded above: watcher
`q19-watch.log` SHA-256
`27e7b4df2c01db86aeaf4a7cddf13577019fe78b8e15478e9a039dff59618052`, interrupt
result `q19-setup-interrupt.json` SHA-256
`82c874ab154ee733f01d23b03db1e76157c793df9f191c3cba2c4435ac0dddc6`, exit
status `q19-setup-exit-status.txt` SHA-256
`f5bde7eb9f6c71611dc5726e8aca3eb4eba3e386da49e0a4ed5c295a90a73a0d`, before
capture `q19-before-interrupt.json` SHA-256
`0cf65691cc796d753fe436739d4e8c9883648ee2adbbab6b6d2b406ad31a3b9e`, after
interrupt capture `q19-after-interrupt.json` SHA-256
`a06dcd3ccefcd8347a7d189e8b2d11ec1d9d2d1555990bef9ca18c1efe7438bc`, retry
`q19-setup-retry.json` SHA-256
`51edf5c8482b1c899bc4f69d090686398b840f27f68c40a51d5ed6d4ade03d18`, and
post-retry capture `q19-after-retry.json` SHA-256
`226e51899959e24fbb571b2d6b9ae771e9b3c14dd076685e96b15aa6713344e2`.

An earlier clean isolated source checkout, a different earlier candidate from the
current archive below, passed all seven gates: 2,952 tests, 18 skipped;
43 architecture tests; import-linter analyzed 514 files and 1,544 dependencies;
Mypy found no issues in 895 source files. Quality used Python 3.14.4 and a private
XDG state directory. These historical counts and source/test hashes do not identify
or verify the current candidate archive above. An earlier attempt against a checkout containing live
installation state failed, and the system Python attempt lacked Ruff; neither is
reported as a passing gate. The clean checkout source/test hashes matched this
earlier candidate. These results do not substitute for live runs or external
CI/SonarQube.

### Current-candidate SSH/WSL full quality result — 2026-10-25

The mandatory SSH/WSL host ran `python3 tools/quality_gate.py quality` against
`<private-wsl-root>/projects/tsw-449-candidate-6d2f25ee`, snapshot HEAD
`0349e18dcdd7ab13aae744fff9aba3530a42f394`, from source archive SHA-256
`5d6ed72d535cc7d46aa03e1289c1043ccbb26df878e9fdc3a9ed7b937dd7736d`. The gate
reached the test phase and failed: 2,956 tests in 270.154 seconds,
`FAILED (failures=30, errors=26, skipped=18)`. Log:
`<private-wsl-root>/tsw-qualification/issue449-wsl2-20261025/r449-current-quality-20261025.log`,
SHA-256 `b771eeaa7186f34326ab46eae1be7240d7285d780d7892d224a5477fcf9ddf47`.
One observed error is a composition test raising `ValueError` for unknown update
stack `jenkins`; this representative failure is recorded without assigning a
root cause. This result supersedes any implication that the current archive passed
the full gate. The separate earlier 2,952-test PASS belongs to a different
candidate and is not combined with or attributed to this run. This stateful
checkout is retained as a separate diagnostic attempt, not the clean-copy rerun.

### Current-candidate clean-copy SSH/WSL quality rerun — 2026-10-25

A fresh copy at `<private-wsl-root>/projects/tsw-449-quality-clean-20261025` had no
`.tiny-swarm-world` state before the run. The four critical code/test file hashes
reported for the `jenkins` composition error match the local candidate files. The
full gate still failed: 2,956 tests in 180.241 seconds,
`FAILED (failures=9, errors=0, skipped=18)`. Log:
`<private-wsl-root>/tsw-qualification/issue449-wsl2-20261025/r449-current-clean-quality-20261025.log`,
SHA-256 `56e05b69a04c7d9f6a08ce61baac2ee4b8400e4e0f4cadbc0bf10c0373b1a35e`.
The nine failures comprised five security permission tests, two skill registry
count assertions (expected 132, observed 133), and two composition expectation
failures. The later diagnosis attributed this attempt to umask/environment leakage.
The earlier 30-failure/26-error run remains a separate diagnostic attempt and was
not overwritten. A later four-failure attempt inherited the htpasswd environment
value and stale skill-registry counts. These diagnostics are superseded for current
quality status by the final verified run below; preserve all failed records.

### Final verified current-candidate SSH/WSL quality run — 2026-10-25

The required full quality command completed with exit 0 in the clean test
candidate `<private-wsl-root>/projects/tsw-449-quality-verified-20261025`. Before testing,
that copy had no `.tiny-swarm-world` runtime state; shell umask was `022`, and
`TSW_TRAEFIK_GUI_USERS_HTPASSWD` was unset. All eight locally changed test files
were hash-identical between the test candidate and local workspace. Deterministic
source tar SHA-256:
`2e36d0aac53f579de18baf4664b9e30c3b2d24e4289a7b6c4157a2a91cf13bcd`;
2,638-line file manifest SHA-256:
`6896c4e8ac9e663b104170d2ce64fcc6a071217e4b85d64366667cf121569683`.

Result: all seven gates passed, exit 0. The suite ran 2,956 tests in 178.695
seconds with 18 skipped; architecture tests ran 43 in 3.289 seconds; import-linter
checked 514 files and 1,544 dependencies (7 kept, 0 broken); complexity passed
for 360 modules; Mypy reported no issues in 895 files. Shell recorded
`QUALITY_EXIT=0`. Full log:
`<private-wsl-root>/tsw-qualification/issue449-wsl2-20261025/r449-current-verified-quality-20261025.log`,
SHA-256 `5d596e2e847159e6295336bd70bdd372160df1198eb751129cd61c8455ed54bc`.

This final verified PASS supersedes the failed diagnostic attempts for current
quality status; their logs and results remain preserved. Diagnostic causes were
identified as follows: the initial 30-failure/26-error run used a contaminated
manifest; the 9-failure run had umask/environment leakage; a later 4-failure run
inherited the htpasswd environment value and stale skill-registry counts. The
corrected fixtures and expected test counts were used for this passing run. These
quality results do not close the remaining live scenarios or AC1–AC5.

Independent audit accepted native Q04/Q09/Q11/Q19/Q20 from 27 reviewed native
JSON records and eight browser records. Archive SHA-256 identities are
`3d696870dc72ac629baf353c7224396e2dc7838db3e68d3e408cefed73a47bca`
and `5092fe73749337c84ea44828b870f15ed72d39be9d011ba12d2b4d5eb9cf9f4d`.

An additional native record contains 42 successful CLI control assertions for
setup/add, generic update/recover, Portainer update and product update/recover.
Help, malformed input, read-only previews, missing consent and explicit no/EOF
preserved manifest/journal bytes and all service IDs/versions/images. Gateway
recovery consent needs an eligible interrupted checkpoint; local regressions or
a refusal before its prompt do not establish that live variant.

Remaining: execute and map applicable WSL Q16–Q18 failure and control variants;
complete WSL R449-35 override-survival coverage, AC1–AC5 and W10 handoff; then
obtain the required independent issue-completion audit. Bounded Q19
setup-interruption/retry reconciliation is recorded in
`.tiny-swarm/evidence/issue-449/acceptance_crosswalk.md`; broader variants and
aggregate acceptance remain open.
External CI/SonarQube remain `EXTERNAL_GATE_UNAVAILABLE`; no publication was
requested or verified.

The historical [WSL W07 failure](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/449#issuecomment-6382026747)
remains `LIVE_FAILED_AFTER_MUTATION`, with its original evidence retained.
Volatile-field config hashes alone do not establish corruption or justify a guessed
rollback. Historical retention and new campaign admission are separate decisions.
See [Three Amigos refinement](lcm-w09-blocker-refinement.md) and
[bounded immutable transitions](lcm-w09-transition-proposal.md).

### WSL R449-35 override attempt — unresolved post-SIGINT completion — 2026-10-25

A fresh official 0.4.0 checkout at revision
`346f4a43dbdc43380e7bc703ab185bc06746965b` adopted the existing operator-managed
WSL runtime using a private `provider-memory-v1` external-infra override. The
override changed only `swarm-worker-1` memory from 8 GiB to 6 GiB, giving the
approved 10/6/1 GiB layout. The read-only preview selected `incus+portainer`,
had zero component changes, listed only the two expected Portainer configuration
changes and passed the unchanged resource guard. Preview SHA-256:
`3fef3e46a6ca2f6d454e922a4128c4928f7c9741077325cdb529d1f39bd4057a`.

At `2026-10-25T15:22:50Z`, the owned-process driver observed the durable
`staging` checkpoint (`72a9517e97ccc1e2c59098ade65d2dedc7a0b16a603b3b8834121815bce542a3`)
for the pinned 0.4.0→0.5.0 plan and sent exactly one SIGINT. Its immediate result
was exit `-2`, the same checkpoint hash and stage, and no product manifest at
that instant. Event SHA-256 is
`95d457d89e95fc64d9c348b34d010b747ac5424271f0ee9da5c8a1af34dff255`; result
SHA-256 is `c94ce9544e2946db22a6127ae40fb199be263b3257f045843bfab1f0543a493b`;
captured process-log SHA-256 is
`d8359d5b8170d96890df3467fe907e539d41227d4510a494175c30fc875ce31c`.

Later read-only inspection found the product checkpoint and manifest had moved
to `completed` / target 0.5.0 at `2026-10-25T15:26:32Z`. A protected
`r35-run/product-recovery.stdout` also exists: mode 0600, created at
`2026-10-25T15:26:15Z`, modified at `2026-10-25T15:26:32Z`, SHA-256
`002ab057d25ca13b5a04fd7cdc90230ea2c2a16874bd4d19594d4378236d1c9a`. It
contains a completed 0.5.0 product result. Its bytes exactly match the separately
indexed Q15 recovery log, so this record cannot distinguish a separate
invocation from copied output. It contains no argv, exit code, PID or process
identity. The later R35 recovery-driver script refuses to start if this output
path already exists, so it cannot be its producer. The recovery actor,
invocation and causal link to the state transition remain unverified. The final checkpoint
SHA-256 is `4d3b8db03ff86ae479c44c171c4adf73272407a8e6f02d15b2de218be7e2f455`;
manifest SHA-256 is
`9044a208511a16e4c127d3665dd12467c7403d95739960a3a9c05020b3b2c3c1`.
Structural validation confirms the persisted source path, `provider-memory-v1`
policy, captured source/snapshot metadata and selected files still match; the
private worker override remains SHA-256
`1ec5a3f9b34c5e9e8680569f40ec2a1af68b895ce68834c8f2d1cc3aa4177031`. A
strictly read-only recovery preview with `TSW_INFRA_ROOT` unset returned exit 0,
`checkpoint=completed`, the same external-infra reference, two expected
configuration changes, no component changes and no diagnostics. Preview
SHA-256: `4086c9e7bf349e200dd55bfa92ecc917131887229a1ad9f354344d2928fb4ce0`.

Do not count this as successful SIGINT recovery or a live repeat. Requirements,
Architecture and Security conditionally permitted one ordinary live repeat only
after a fresh JIT and a read-only preview returning literal `no_op`. The recorded
post-hoc preview instead returns `status=preview`, identifies source 0.4.0 and
target 0.5.0, and lists protected-infrastructure and installation-product state
changes. That prerequisite is not met; no live repeat was run. WSL R449-35
therefore remains **OPEN / NON-PASS for interruption recovery**. The observed
10/6/1 GiB runtime and retained binding are bounded current-state evidence only.
Overall #449 remains **INCOMPLETE**.

## R41 native Linux current-state JIT — 2026-10-25

Read-only SSH inspection of native Linux test host (Ubuntu 26.04.1,
x86_64) found the native source checkout clean at commit
`9ee255415abc1c5bac071b16132de1e7ca517213`, tree
`56d5ae690072999c67f4bc7b7a829aafe4fe5352`. Incus client/server are 6.0.5.
The host had 20,111,052,800 bytes total RAM and 15,068,827,648 bytes available;
root filesystem free space was 718,345,187,328 bytes.

The default Incus project contained the three expected TSW instances, all
running, with 10/6/1 GiB limits and root volumes of 20/50/10 GiB. The manager
was Docker 28.5.2 Swarm leader; all three nodes were Ready/Active, with
Portainer and its agent at 1/1 and 3/3, plus Swagger and Traefik stacks at
their recorded desired replica counts. The separate `issue447-20261024`
manager was stopped and retained its two W07 snapshots; it was not changed.

The shared `default/docker-swarm-manager` profile still has five wildcard
listeners (80, 443, 10001, 16080, 16081) and only the current manager as its
consumer. No mutation was performed. This observation identifies the existing
native state and does not qualify installation, upgrade, interruption or
recovery. The captured available RAM is below the 17 GiB allocation; repeat the
resource guard immediately before any live provisioning. Detailed IDs,
resource values and read-only scope are in
`.tiny-swarm/evidence/issue-449/native-current-state-r41.md`.

#### Read-only provenance follow-up

The allowed follow-up inspection found no currently running product-upgrade,
recovery-driver, or related clone/install process. The WSL system journal has no
matching product, Python, package-install, or recovery-driver entries for
`15:20–15:30Z`; the user journal has no entries in that window. The persisted
`.bash_history` was last modified at `15:06:04Z`, before the interruption. The
protected completion stdout above has no verifiable invocation metadata and its
hash duplicates the separate Q15 recovery log. The kernel journal does contain six
`weston` process entries in the same window, including segmentation faults, but
they do not identify or establish a connection to the lifecycle writer. These
observations therefore do not attribute the `staging`→`completed` transition.
The issue remains **OPEN / NON-PASS** for R449-35. The read-only preview is not
a recovery pass, and its planned state changes blocked the conditionally
reviewed live repeat before mutation.

### Native Q16 source-admission refusal previews — 2026-10-25

Three-Amigos conditionally approved two native-only preview controls: dirty
checkout and non-official Git origin. The clean controller was pinned to
revision `0349e18dcdd7ab13aae744fff9aba3530a42f394`, tree
`b0a4680c318db17da94cde6680d83f872fc8e607`, requirements lock SHA-256
`ac9474784f50b87087e5e24a5a3163118aaf1f2845597d07f7dfa86eb713ff08`, and
transfer archive SHA-256
`91650a299e20bc3fdf3c9576a8d3d08851dee63eac4d8ec309201f9e14aeb174`. The
private Python 3.12.15 environment and fixtures were under mode-0700 `/tmp`
paths. `TSW_INFRA_ROOT` and inherited credentials were absent; there was no
adoption manifest or live/recovery flag.

Both ran only
`product upgrade --to 0.5.0 --preview --json`. The dirty fixture had one
untracked sentinel and the official origin; it returned exit 1, status
`blocked`, the dirty-checkout diagnostic, and output SHA-256
`2790b48971d704a0cb27ae348b7f5cca6ddec4df23085049fcf03c21b75516c6`. Its HEAD,
origin and sentinel status were unchanged. The second fixture was clean with
origin `https://example.invalid/tsw-449-q16-origin.git`; it returned exit 1,
status `blocked`, the non-official-repository diagnostic, and output SHA-256
`c27c41bbf2cc92711be8fc8e8ab3f890eab9be981de94173ccfa536b51521579`. Its HEAD,
origin and clean status were unchanged.

Both guards stopped before release resolution, manifest admission and resource
validation. The preview did not call Incus, Docker/Swarm, Portainer or the
product runtime adapter. No runtime-state snapshot or health read was taken;
runtime preservation is not claimed. This adds bounded native source-admission
evidence only. Q16 remains **PARTIAL**: moved-source semantics, additional
dirty/unknown variants, runtime drift, old/mixed tasks and WSL coverage remain
open. The detailed review and fixture record is
`native-q16-source-guards-r37.md` in the issue evidence package.

## R40 WSL R35 fixture readiness gate — 2026-10-25

A fresh, owner-only attempt root and clean detached official source/controller
worktrees were prepared without changing the live WSL runtime. The 0.4.0 source
and 0.5.0 controller commits, trees, lock hashes, official origins and clean
Git states match the reviewed pins. The copied private provider configuration
is mode 0600 with the reviewed 10/6/1 GiB values and exact recorded hash.

The static 0.4.0 `setup run --service-profile service-access --preflight`
reported `setup_profile=full`, `manifest.profile=full`, and thirteen missing
mandatory service-secret sources. It ran no live infrastructure command. The
approved one-off fallback is an operator-built, adopted 0.4.0 Portainer fixture;
it is explicitly not selective-install evidence. The 0.5 adoption path can
consume a runtime-derived manifest without invoking `setup run`, but Docker,
Swarm and Portainer must first be provisioned and read back independently.

Architecture, Requirements and Security reviewed a secure target using signed
Ubuntu Docker packages, a three-node internal Swarm, official pinned Portainer
and Agent 0.4.0 assets, and runtime-derived adoption. The lifecycle client
resolves the manager `eth0` IPv4 address through Incus and connects to
`<manager-ip>:10001`. A direct instance-level proxy is rejected by the product
verifier; omitting the expected `docker-swarm-manager` profile is also rejected.
The verifier-compatible configuration is a single profile proxy on
`127.0.0.1:10001`, with the other four wildcard proxy devices removed from the
shared `default/docker-swarm-manager` profile. Architecture and DevOps consider
that configuration verifier-compatible; Security and Requirements require
explicit user authorization because it changes the shared profile and removes
four existing listener mappings. No reset, profile mutation, package install,
Swarm initialization, Portainer deployment or upgrade has been run under R40.

Read-only inventory found that the manager profile has only `swarm-manager` as
a consumer and currently contains five `0.0.0.0` listeners on ports 80, 443,
10001, 16080 and 16081. The active manager listener is Portainer's host-mode
10001; manager-side services were Portainer and its 3/3 agent only. Windows
PortProxy also has existing wildcard mappings, which were not changed. The
proposed loopback-only profile would not preserve Windows-host access through
those current WSL-IP mappings. The lifecycle Portainer client resolves the
manager's `eth0` IPv4 address through Incus and connects to `<manager-ip>:10001`;
it does not call host `localhost:10001` through the profile proxy. Before using
this route, verify the manager IP is on the private Incus bridge and that no
forwarding exposes it beyond the host. Do not infer approval to edit Windows
PortProxy.

R40 is **BLOCKED BEFORE LIVE RESET** pending explicit user authorization for
the exact shared-profile change, or an approved alternative that satisfies
the product verifier without broader listeners. The old R35 remains a
non-pass. Overall #449 remains **INCOMPLETE**.

## R42 inherited W07 failure-stage re-review — 2026-10-25

Review of preserved W07 logs narrows the observed sequence: the isolated
issue447 project, test-owned bridge, manager and Swarm became ready; the later
bootstrap stopped during `image_preparation` when an `incus exec ... docker
pull` returned exit 1. The wrapper retained the traceback but discarded the
captured stdout/stderr. A later exact source-image pull in the isolated issue447
manager returned exit 0. Incus documents `INCUS_PROJECT` as a client project
override ([official environment-variable reference](https://linuxcontainers.org/incus/docs/main/environment/)).

The preserved default-project records separately show two workers changing
Stopped→Running and their config hashes changing. No retained event establishes
that the isolated pull failure caused those changes; the missing `run_live.py`
and pull failure are not root-cause proof. Keep W07
`LIVE_FAILED_AFTER_MUTATION`, cause unverified, and make no restoration or data
preservation claim. Hashed local evidence pointers and the independent R42
review are recorded in `.tiny-swarm/evidence/issue-449/wsl-incident-diagnosis.md`
and `completion_audit.md`. This narrows failure-stage traceability but closes no
aggregate AC or R449-21.

## R43 native LIVE-4 evidence reconciliation — 2026-10-25

The independent review reconciled the native Q12 run with the captured source
archive. The native result `native-live-result.json` (SHA-256
`e7548d027a63b51a8a363a0f16a60eb668a61e3c66a1ad1de904a5cbb0b00a94`) records
exit 0, authenticated access, stable endpoint and ownership fingerprints, a
completed `managed-update` stage, and post-update Portainer, Agent and Traefik
tasks with desired and current state `Running`. The captured source archive
`candidate.tar.gz` (SHA-256
`e6b8d6d890afa682ffeb63ee17beac0e3a49e314cbea59cbe3305cbc402191dc`) shows the
executed verification path issuing an authenticated Portainer stack `PUT`,
checking HTTP success and waiting for Swarm readiness. Requirements,
Architecture, Test/Evidence and the independent completion auditor accept this
as **VERIFIED BOUNDED NATIVE LIVE-4**. WSL LIVE-4 remains open because the WSL
attempt failed before the adapter update. This closes only the native
subcriterion; AC1–AC5 and #449 remain incomplete.

## R45 WSL route and artifact review — 2026-10-25

Three-Amigos conditionally approved a fresh WSL product-upgrade/recovery
qualification using the existing manager-private API route. A read-only probe
from the authorized native Linux peer found no route to that WSL manager
endpoint and made no HTTP or authentication request. Security permits use of
the WSL-local route only after an immediate-before-write JIT confirms the same
target identity and unchanged profile, listener and PortProxy state. No shared
profile, PortProxy, firewall or host-route change is authorized. This bounded
peer result is not a global isolation audit.

The R40 statement that a shared-profile edit is required is superseded for this
controller route. The existing profile and wildcard listeners remain in place.
The user authorized replacement of only the exact TSW instances in the default
project, without a data-preservation requirement. No R45 instance replacement
occurred. The separate issue447 manager and snapshot remain out of scope.

Q13 now has a partial hash-linked sanitized index in
`.tiny-swarm/evidence/issue-449/q13-sanitized-index-r45.md`. It records bounded
recovery, service/API verification and repeat status fields. The upgrade output
is malformed as JSON; a watcher log contains an unlinked `stage=upgrading`
label. At this R45 checkpoint, the cache logs were unreviewed; R51 later
reviewed them without finding invocation/exit linkage. The upgrade stage is not
attributable and WSL LIVE-4 remains open. The 0.4.0 selected setup
preflight still reports a full profile and thirteen missing service-secret
checks; the operator-provisioned/adopted baseline can support upgrade/recovery
only, not selective-install qualification. AC1–AC4 remain partial, AC5/W10
remains open, and #449 remains **INCOMPLETE**.

## R46 retained-runtime upgrade gate — 2026-10-25

Three-Amigos selected the non-destructive WSL path for the R449-35
product-upgrade/recovery scenario. No R45 instance replacement occurred. The
current Incus instances, Swarm, external network, Portainer volume, Swarm
secrets, profile and Windows PortProxy remain the baseline. A new clean official
0.4.0 product root and a fresh runtime-derived adoption manifest must pass the
admission preview for the exact 0.4.0→0.5.0 transition with the approved
`provider-memory-v1` binding and no component changes. A new independent review
and immediate-before-write JIT are required before credentials or live writes.

This path qualifies product upgrade/recovery only. It does not qualify clean or
selective installation, Q12 Portainer component update, or explain R35's old
unattributed completion. No R46 runtime mutation has occurred; Q13 is PARTIAL,
WSL LIVE-4 remains open, AC1–AC4 remain partial, AC5/W10 remains open, and #449
remains **INCOMPLETE**.

## WSL Q02 selective fresh-install result — 2026-10-25

After the authorized reset of the three TSW nodes in Incus project `default`,
one reviewed `setup run --minimal` was executed on WSL2. The command ran from
`<private-wsl-root>/projects/tsw-449-quality-verified-20261025` with
`INCUS_PROJECT=default`; the protected operator environment file was sourced
for that CLI process with shell tracing disabled. The required Portainer
credential was present in the process environment; its value was not logged.
The unchanged issue447 manager remained in project `issue447-20261024` with
UUID `8db22b4d-51d5-4187-8d23-4317f35f3d83`.

The tested source was synthetic local snapshot HEAD
`933925e61f3d3153060950acb6afacbeb335e207`, matching source archive SHA-256
`C49665FF43FDCE020926E8AC4E68EE2FBBDA3DF9811AEFF653C5D33C4552E90B`. It is
not an official release ancestry or upgrade baseline. The exact-source WSL
quality gate passed 2,977 tests with 36 skipped. The immediate preview exited 0
and selected only Incus and Portainer, with no removals and retained data.

The live CLI exited 0 and reported `status=completed`, `outcome=success`, no
failed or pending operations. Preflight, artifact preflight, host preparation,
platform initialization/reconciliation, Docker cluster bootstrap/verification,
Portainer bootstrap/readiness/apply, deployment verification and final platform
verification all completed successfully. The new manifest is schema 1, mode
0600, installation ID `6d150f0b-9e9a-4f45-87a5-2cd5757fe234`, and records the
synthetic source revision. It resolves `incus` and `portainer` only.

Post-state readback found exactly three new `default` instances, all Running:
`swarm-manager` (10 GiB), `swarm-worker-1` (8 GiB), and `swarm-worker-2`
(1 GiB). Swarm reports all three nodes Ready and Active. The Portainer service
is 1/1 on `portainer/portainer-ce:2.45.1`; its Agent is 3/3 on
`portainer/agent:2.45.1`. Authenticated Portainer login and local endpoint API
readback both returned HTTP 200; endpoint `local` is registered and ready.
Windows `127.0.0.1:10001/api/status` also returned HTTP 200. WSL host address
`172.18.46.221` matches the unchanged Windows wildcard PortProxy target. The
existing Windows allow rule still has `RemoteAddress=Any`; the user explicitly
accepted that reachability for this run. Firewall and PortProxy were not
changed. This run does not qualify Traefik or HTTPS ingress.

The private post-state and invocation summary are
`.tiny-swarm/evidence/issue-449/q02-live-20261025T2259Z/q02-live-20261025T2259Z/post-state.json`
(SHA-256 `CD601B79BF652D3D28699420317AB00E1F9B1FF4475F6F526B44D06F6E6AF0FB`).
The adjacent `run-record.md` and `index.sha256` preserve the summarized
invocation, time bounds and evidence hashes; the raw interactive CLI transcript
was not exported.
Requirements, Architecture, Test/Evidence and the independent completion
auditor accept this bounded WSL Q02 fresh-install result. It does not close
upgrade scenarios, Q12/Q13 attribution,
remaining Q16–Q18/Q19 variants, cross-host AC1–AC5 traceability or W10 handoff.
Overall #449 remains **INCOMPLETE** pending the remaining matrix rows and final
independent completion PASS.

## R47 WSL Q12 evidence gate — 2026-10-26

Independent Requirements, Architecture and Test/Evidence reviews reconciled
the older q07/q08 narrative with `q12-candidate-review-r46.md`. The q07
completed wrapper lacks unique command, process exit, event time,
source/candidate and operation identity. The q08 interrupt wrapper is
byte-identical to q07, while its named upgrade result is a blocked preflight.
The Q12 repeat record and runtime continuity observations remain contextual,
but do not prove the initial 2.45.0→2.45.1 operation or a Q12-specific no-op.
Keep R449-05 PARTIAL CROSS-HOST, WSL Q12 PARTIAL and WSL LIVE-4 OPEN.

The current WSL Q02 fixture is on Portainer/Agent 2.45.1 and has no optional
Portainer-managed stack. A read-only 2026-10-26 check observed three Running
Incus containers and three Ready/Active Swarm nodes, but its interactive output
was not archived and does not count as AC1 or Q12 evidence. A new attributed
2.45.0 fixture, exact before/after evidence, product cold `/data` backup,
managed-stack update with ready tasks, unique repeat, immediate JIT and fresh
scenario-specific Three-Amigos GO remain prerequisites. The subsequent
Architecture and DevOps reviews found no supported sequence in the current
candidate that leaves `swagger` in `resolved_services` and Portainer Type-1
ownership in place without publishing Swagger host ports 16080/16081. Portainer
API creation alone does not commit TSW selection, and the normal TSW add path
deploys the canonical Compose definition with both ports. The existing user
approval for `RemoteAddress=Any` covers the current Portainer route on port
10001 only. A product design/implementation change is required before a new
fixture can run. No live mutation was performed under R47. Details and the full
minimum evidence contract are in
`.tiny-swarm/evidence/issue-449/three-amigos-r47-q12-evidence-gate.md`.

### R51 WSL Q13 read-only artifact salvage — 2026-10-26

A redacted read-only review on the WSL host rehashed all ten existing Q13
artifacts and matched the recorded names, sizes and SHA-256 values. The
malformed upgrade output still contains 52 unparseable lines; static watcher
logic and the cache logs do not establish a linked command, process, signal or
exit. File modification times remain locator metadata. Q13 stays
**PARTIAL / NON-PASS**: no upgrade-stage, SIGINT, API-down, cold `/data`
recovery, same-run verification or no-op repeat was proven. No retry or live
mutation occurred. The sanitized projection is in
`.tiny-swarm/evidence/issue-449/q13-sanitized-index-r45.md`.

## Prior exact-worktree full quality gate — 2026-10-26 (superseded below)

The latest quality run tested the current workspace snapshot in an isolated WSL
checkout at `<private-wsl-root>/projects/tsw-449-active-20261026` on the required host
`approved WSL2 test host`. It used Python 3.12.15 from
`<private-wsl-root>/tsw449-python312/venv` and ran `python tools/quality_gate.py quality`.
All seven gates passed with exit 0: 2,977 tests passed and 36 were skipped; the guard-coverage follow-up below supersedes this run.
The 2026-10-25 clean-candidate gate above remains a separate source identity and
is not overwritten by this result.

Snapshot provenance: source HEAD
`6d2f25ee843a01066fcdcfe4855666849513ff06`; initial full workspace transfer
archive SHA-256
`7ce193d04e9917ff4a4aba63c42a2f1da7c339a91bb4939d3308f93ec6bf2f61`; after
archive extraction, `tests/test_incus_preparation.py` was synchronized to the
current local SHA-256
`a4f1a357d3070f9f39927a21239f6baeabe3f8dfdba66f4056dda6cdb699288b`.
Quality log: `<private-wsl-root>/projects/tsw-449-active-20261026/quality-gate-python312.log`,
46,460 bytes, SHA-256
`6c0e9ca83aae56279f178df5f790691beb08ff9b4bd171b799d08bd7e08cee36`; the
adjacent exit record contains `0`. The log contains test-run output; this is
local quality evidence, not live infrastructure qualification, CI, or
SonarQube evidence.

## R56 predecessor full quality gate before CLI regression — 2026-10-26

After adding deterministic stale-bootstrap-checkpoint refusal coverage, the
full Python 3.12.15 gate reran in the isolated WSL worktree
`<private-wsl-root>/projects/tsw-449-active-20261026` on `approved WSL2 test host`. All seven
QUALITY gates passed with exit 0: 2,978 tests passed, 36 skipped. The focused
`tests.test_incus_preparation.IncusHandoffTests` run passed 3/3.

Snapshot identity: source HEAD
`6d2f25ee843a01066fcdcfe4855666849513ff06`, transferred workspace archive SHA-256
`7ce193d04e9917ff4a4aba63c42a2f1da7c339a91bb4939d3308f93ec6bf2f61`, plus
`tests/test_incus_preparation.py` SHA-256
`b677bcb098b4649a3343544780f19408830be48e06c2baa09a0f3edf39175043`.
Quality log: `<private-wsl-root>/projects/tsw-449-active-20261026/quality-gate-python312-r2.log`,
47,561 bytes, SHA-256
`a1b34e55ed4d2d42c315812e684584265ea7157f8601f7e98ea641e9c3e8f41e`; the
adjacent exit record contains `0`. This result predates the R56 CLI regression
and is superseded by R57 below. The 2,977-test run above is retained as the
preceding pass on the same snapshot before this added regression. Local quality
does not replace live evidence or close AC1–AC5.

## R53 Q12 consent and design revalidation — 2026-10-26

The operator accepted the existing WSL Portainer route's `RemoteAddress=Any`
setting for this run. Independent Requirements, Architecture and Test/Evidence
reviews confirm that this applies to the already configured Portainer API route
on port 10001 only. It authorizes no firewall/PortProxy change and no Swagger
host ports 16080/16081 or Traefik/customer route.

Q12 remains **NO-GO for implementation and live execution**. The current WSL
fixture is Portainer 2.45.1 without a selected Portainer-managed optional
stack; current Swagger selection publishes host ports, while an ad-hoc
Portainer stack does not persist TSW selection. The required product decision
on persistent versus fixture-only portless behavior and its route semantics is
still open. After that decision, Q12 still requires reviewed ownership and
manifest migration, implementation and quality gates, a fresh isolated 2.45.0
fixture, cold `/data` backup, immediate JIT and a new scenario-specific
Three-Amigos GO. No Q12 live operation ran during this revalidation. Details:
[Q12 design proposal](lcm-w09-q12-design-proposal.md) and private
`three-amigos-r53-q12-route-consent-gate.md`.

## R55 WSL post-removal qualification gate — 2026-10-26

All WSL runtime snapshots through Q20 describe historical state captured before
the authorized removal on 2026-10-26. After that removal, the default Incus
project is empty; no current WSL TSW installation, Swarm health, or retained
runtime is claimed.

After the three operator-authorized default-project TSW instances were deleted,
a fresh read-only JIT confirmed the `default` Incus project and its storage
volume list are empty. The independent `issue447-20261024` project remains
outside scope with its manager and existing volumes. No replacement instances,
Docker/Swarm setup, secrets or Portainer deployment have been created; shared
Incus, Windows firewall, PortProxy and host route configuration were not
changed. The initial post-removal port-filtered `ss` check found no WSL listeners
on TCP 80, 443, 10001, 16080 or 16081. A later short listener listing showed
only DNS sockets in its displayed rows and is not independent proof for all
five ports.

The preserved manager profile contains Incus proxy devices for all five ports.
Windows still has wildcard PortProxy mappings to WSL for TCP 80, 443, 10001,
16080 and 16081. The four non-10001 ports each have an enabled inbound TCP
Allow rule on all profiles with `Remote-IP=Any`; the profiles otherwise use
default inbound block. The user's route acceptance identifies Portainer on
TCP/10001 only. Follow-up Requirements, Security and Test/Evidence reviews
conditionally accept a fixture that leaves the other four routes unserved
without changing Windows firewall or PortProxy. Architecture and DevOps found
that a differently named manager profile is incompatible with the pinned TSW
contract. The selection-aware 0.5 verifier accepts the expected
`docker-swarm-manager` profile with only the 10001 relay, but removing the four
other devices mutates the shared Incus profile. The user authorized replacing
instances, not that shared-profile change. Tagged 0.4.0 source has no
resolved-service selection in its platform manifest and verifies the full port
list; a 10001-only profile fails that verification. The gate remains blocked
pending an explicit acceptance exception or a supported source-backed
solution. Do not characterize the four routes as globally isolated based on
the current absence of a listener.

R57 Architecture/DevOps review considered an Incus project-scoped profile.
Incus supports isolated project profiles ([project guide](https://linuxcontainers.org/incus/docs/main/explanation/projects/)),
but current TSW provider configuration and command builders pin the `default`
project, while tagged 0.4.0 verifies the full 18-port `SERVICE_ACCESS` manifest,
including all five observed relay ports. This is not a
supported workaround without broader provider changes, and it does not satisfy
the 0.4.0 verifier. No project or profile was created or changed.

The sanitized post-removal JIT and exact gate are retained privately in
`.tiny-swarm/evidence/issue-449/r35-post-removal-jit-20261026.md` and
`r35-operator-built-fixture-plan.md`. The old installation was not backed up or
restored, per operator direction. This JIT does not satisfy Q15/R35, selective
setup on a newly provisioned official-source baseline, Q12/Q13, or AC1–AC5.

## R56 current host and quality evidence — 2026-10-26

A read-only JIT at 02:16 UTC found the native Linux target's current default
Incus project running three containers with the previously qualified private
17-GiB allocation. The in-manager Swarm query returned three Ready/Active nodes
and seven healthy services. The native controller checkout is clean `main` at
`ca0ce16a0d09464060a79acab64eb630602bb4a5`, not the uncommitted issue
candidate. All five configured relay ports were listening. This supports only
the captured runtime state, not current-candidate scenario qualification.

The WSL JIT at 02:14 UTC still found an empty default Incus project and no
listeners on the five ports; its shared manager profile remains configured for
all five relays. The R56 targeted service-selection CLI module passed 7 tests.
The first R56 full-gate wrapper attempt was interrupted after the test summary
and had no exit record; its network-plan/consent text was expected output from
a mocked network-consent unit test, not a live host-preparation attempt. The
R57 rerun passed all seven gates, exit 0, with 2,979 tests/36 skipped under
Python 3.12.15. The log SHA-256 is
`a51c7373eb04d7713809d998462aaa95d4ac1ff91fb89fd17eee4435a875f528` (49,994
bytes); source archive and test overlay identities are indexed privately in
`.tiny-swarm/evidence/issue-449/test_results.md`. No WSL host preparation ran.

AC1–AC4 remain PARTIAL, AC5 OPEN, and the overall issue INCOMPLETE. Native
bounded live success does not substitute for missing WSL Q12/Q13/LIVE-4, R35
recovery attribution, broader Q16–Q18, W07 cause, W10 acceptance, or final
independent audit. No WSL setup or host preparation was performed in R56.

## R58 WSL route-scope and current-state review — 2026-10-26

The user approved WSL minimal Portainer setup over the existing TCP/10001 route
with `RemoteAddress=Any`, without firewall or PortProxy edits. Fresh Three-Amigos
review found that the pinned minimal flow attaches `docker-swarm-manager`, whose
five wildcard relays include 80, 443, 16080 and 16081 in addition to Portainer
10001. The profile has no current consumers, but a new manager would activate
those four additional relay paths. The minimal setup also cannot provide
Q12's supported Portainer 2.45.0 source, selected Portainer-managed optional
stack, ownership and cold `/data` evidence. The disposition is **NO-GO for the
live minimal setup or Q12 under the current scope**; no host mutation ran.

A fresh read-only JIT found the WSL default Incus project empty, the manager
profile unconsumed, and no listeners on the five relay ports. Available WSL
checkouts do not match the current issue candidate, so no new tests or live
claims are made. See the private R58 route review and JIT under
`.tiny-swarm/evidence/issue-449/`. Q12, WSL LIVE-4, R35 attribution/recovery,
AC1–AC5, W07 cause, W10 and final independent PASS remain open. Overall #449
remains **INCOMPLETE**.

## R59 native Linux resource and runtime JIT — 2026-10-26

At `2026-10-26T02:41:58Z`, the native host had 20,111,052,800 bytes total
memory, 15,051,165,696 bytes available, and 718,345,994,240 bytes free on its
root filesystem. The configured default 19-GiB allocation is
20,401,094,656 bytes, 290,041,856 bytes above host physical memory, so it is
rejected. A previously reviewed private 10/6/1-GiB `provider-memory-v1`
override totals 17 GiB and passed the same planned-limit guard; a new candidate
run must rebind and verify that exact effective config and account for current
active allocations before replacement. The existing 10/6/1-GiB cluster was
bounded healthy at capture with three Ready/Active nodes and seven services,
but no current issue-candidate checkout was verified. A follow-up read found
the previously reviewed private 10/6/1-GiB effective infrastructure tree still
present; its provider YAML hash is recorded in the private JIT. Identity against
a new source operation was not verified. No native operation ran. See private
`r59-native-current-jit-20261026.md`; this does not close native candidate
qualification or any aggregate AC.

## R61 native current-candidate Q16 source-guard previews — 2026-10-26

The current non-private workspace export was transferred to the native host and
rechecked by SHA-256 (`627dae0f…d91632`). On native Python 3.12.15, two isolated
product-upgrade previews refused a dirty fixture with the official origin and a
clean fixture with an unofficial origin, each with the expected `blocked`
diagnostic and exit 1. Fixture Git tree, origin, and working state were
byte-identical before and after each preview. The retained run record and
evidence index bind the source archive, runtime, commands, outputs, and fixture
states. This is bounded current-candidate evidence for two Q16 source-refusal
variants; it is not a successful upgrade, runtime-preservation proof,
moved-source result, or aggregate acceptance pass. Q16 and AC1–AC5 remain open.
See private `r61-native-current-q16-source-guards.md` and its retained evidence
bundle.

## R61 WSL2 current-candidate Q16 source-guard previews — 2026-10-26

The same candidate archive SHA was transferred to the designated WSL2 host and
verified there. Under WSL Python 3.12.15, dirty+official-origin and
clean+unofficial-origin preview fixtures again returned the expected `blocked`
diagnostics and exit 1, with identical before/after fixture Git state. Raw
outputs, command, run record, and hash index are retained privately. The
Three-Amigos Requirements, Architecture and Test/Evidence returned bounded GO
for these two refusal cases. This does not qualify live WSL installation, the
shared profile/route, successful upgrade, runtime preservation, or Q16 overall.
See private `r61-wsl-current-q16-source-guards.md`,
`three-amigos-r61-wsl-q16-review.md`, and the evidence bundle.

## R62 native and WSL2 recovery-consent refusal controls — 2026-10-26

The exact current-candidate archive was run on native Linux and WSL2/Python
3.12.15 with isolated cwd, HOME, checkpoint and repository state roots. Each
host ran component and product recovery commands with explicit `n` and EOF.
All eight invocations exited 2 with `status=refused` and `missing live
confirmation`; per-case before/after tree hashes matched and deny/log runtime
ledgers were empty. The native and WSL bundles retain per-invocation argv,
stdin, timestamps, runtime/source identity and raw hashes. Three-Amigos accepted
only this bounded refusal subcase. It does not establish checkpoint recovery,
accepted consent, runtime preservation or full Q18. Q16–Q18 variants, Q12,
WSL LIVE-4/R35, W07 cause, W10 and AC1–AC5 remain open; #449 remains
**INCOMPLETE**. See private `q18-consent-refusal-r62.md` and the two R62 bundles.

## R63 native and WSL2 synthetic Q17 removal-impact preview — 2026-10-26

The current candidate ran `services remove --services swagger --preview --json`
on both native Linux and WSL2 against catalog-validated synthetic schema-v1
manifests with unique install/product identities. Both exited 0 with
`selection_preview`, `removals=["swagger"]`, Incus and Portainer retained,
`retained_data=true`, and execution marked not performed. Explicit empty stdin,
manifest provenance, raw output, isolated-state hashes and candidate-infra
hashes are retained in the two bundles. Three-Amigos bounded GO covers this
synthetic removal-impact preview only; Swagger in `resolved_services` describes
the fixture, not a post-removal selection. This does not prove an installed
optional stack or live removal and earns no Q05 credit. Q17, AC1/AC3 aggregates,
AC1–AC5 completion, Q12/Q13, R35, W07/W10 and #449 remain open/incomplete.
See private `q17-removal-preview-r63.md` and the native/WSL R63 bundles.

## R64 local minimal Apply verification fix — 2026-10-26

The current candidate now selects the mandatory Portainer admin-access and
local-endpoint checks for minimal empty Apply by stable verification identity,
with fail-closed handling for missing or duplicate identities. Three-Amigos
returned bounded GO and the full WSL quality gate passed (2,981 passed, 36
skipped). This is local implementation evidence only; it does not qualify a
fresh native or WSL installation. Overall #449 remains incomplete. Details are
in private `minimal-apply-order-r64.md`.

## R65 native and WSL2 synthetic checkpoint-present consent refusal — 2026-10-26

The same current-candidate archive ran on native Linux and WSL2 under Python
3.12.15. Both hosts used `services update --services swagger --recover --live
--json` and `product upgrade --to 0.5.0 --recover --live --json`, each with
explicit `n` input and without `--approve-live`. All four invocations exited 2
with `status=refused` and `missing live confirmation`. Strict lifecycle models
loaded separate synthetic in-progress manifests/checkpoints before and after
each invocation; their hashes and the isolated repository trees were unchanged.
Stderr and deny-shim ledgers are empty, and `TSW_INFRA_ROOT` was absent. The
archive SHA-256 is
`5396e028bbad96465790a60c7d9f4769e1b7a308a91e5ef7fb5cb0b0c48d1dd6`; candidate
content-tree and relevant module hashes match across hosts. Full tree digests
differ because they include file-mode metadata after extraction.

Three-Amigos reviewed this as bounded Q18/R449-17 and AC1/AC3 refusal evidence.
The component checkpoint uses test-only `test-next` data, and the product
checkpoint uses synthetic lock and identity data. Consent is rejected before
journal lookup, so this does not prove semantic eligibility, accepted recovery,
runtime/data preservation, or successful mutation. Q18 and aggregate criteria
remain partial/open; #449 remains **INCOMPLETE**. Host JSON and runner details
are retained in ignored `.tiny-swarm/evidence/issue-449/` as the R65 records.

## R66 WSL route consent and current JIT — 2026-10-26

The user accepted the existing Portainer TCP/10001 route, including its
`RemoteAddress=Any` rule, while requiring Windows firewall and PortProxy rules
remain unchanged. That approval does not include 80, 443, 16080 or 16081.
A fresh read-only JIT found the WSL default Incus project empty and its unused
`docker-swarm-manager` profile still configured with wildcard proxy devices for
all five ports. Recreating the manager with that profile would activate four
unapproved routes, so no live mutation was performed. Current 0.5 selective
setup needs a one-port manager profile and another explicit gate; pinned 0.4.0
setup/verification cannot represent Portainer alone. See the private R66 JIT
record for the timestamp, host measurements and independent review findings.
WSL setup and LIVE-4 remain open; #449 remains **INCOMPLETE**.




## R67 selection-aware profile design — 2026-10-26

The current-candidate WSL provisioning gate remains NO-GO. R67 records a
proposal-only path: derive effective routes from persisted post-operation
selection and use an installation-scoped manager profile, with exact
pre-start/post-start device verification. Requirements accepts the route-set
semantics only; Architecture, Security and DevOps are conditionally GO for
formal ADR review, and Test/Evidence is conditionally GO for test design. The
ADR has not been accepted, no implementation or new quality gate has run, and
no host was changed. Fresh native/WSL qualification and final #449 completion
remain open. See private r67-selection-profile-design-proposal.md and
adr-installation-scoped-incus-profile-draft.md.

## R68 native current-state JIT — 2026-10-26

A fresh read-only native JIT confirms the current three-node Swarm runtime and
seven service replica counts. All five wildcard profile ports have IPv6
listeners. This is not a current-candidate installation or upgrade result:
the 10/6/1 override was not re-admitted to source/lock and available memory is
below the plan while the runtime is active. No host mutation occurred. See the
private R68 JIT record. Aggregate acceptance remains incomplete.

## R68 WSL/Windows current route JIT — 2026-10-26

A fresh read-only JIT confirms enabled Windows TCP Allow/RemoteAddress=Any rules,
IPv4 wildcard PortProxy and iphlpsvc listeners on 80, 443, 10001, 16080 and
16081. PortProxy currently targets WSL eth0 172.18.46.221, which matched the
fresh address check. The WSL default Incus project is empty and has no matching
listeners, but its unused manager profile carries all five wildcard proxies.
The user approved the existing 10001 route only and requires both Windows
firewall and PortProxy to remain unchanged. Creating a manager with the current
profile would activate four unapproved routes; the live path remains NO-GO.
No settings were changed. See the private R68 WSL route JIT record.

## R69 native and WSL filesystem classification correction — 2026-10-26

External product-configuration admission now detects the actual host and asks
the filesystem inspector to classify for that host. Native Linux must resolve
to `NATIVE_LINUX`; WSL2 must resolve to `WSL_LINUX`. Unsupported, Windows-
mounted, unknown, or mismatched classifications fail closed. Regression tests
cover native classification, WSL mismatch, Windows-mounted and unknown paths.

The exact combined PC WSL candidate passed the focused module (38 tests) and
the full quality gate under an isolated Python 3.14.4 environment (3,016 tests,
36 skipped, exit 0). Source SHA-256 is
`0d5903e7d96b0c3032f0574fd9b3c75a929a5324bc5efe1d0481a79a7cfe1e93`; test
SHA-256 is
`189d63c1259a29ddf027a3c6988608a0c4e37645c0eba4ba163e43fa1d19e5a5`. The
full-gate log is retained privately at
`.tiny-swarm/evidence/issue-449/quality-gate-r69-wsl.log`, SHA-256
`c6cbfeb6399d992cfb2fa98ddfc19612b7d40081d81b0791e6e9b1d112cdec79`.
Three-Amigos Requirements and Architecture returned bounded GO; Test/Evidence
returned READY for this correction. Independent architecture and quality
reviews confirmed the exact source/test hashes and the local verification
scope.
The candidate was `<private-wsl-root>/projects/tsw-lcm-w09-scope-final2-20261026`;
these results are local verification only and do not establish a live install,
upgrade, or recovery result. Aggregate acceptance remains incomplete.
