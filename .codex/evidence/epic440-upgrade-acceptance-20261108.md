# EPIC 440 S-U1 private upgrade qualification source

Status: SOURCE CANDIDATE; tests, host effects and live
qualification NOT_RUN by author. This record is not compatibility admission,
release publication or EPIC completion.

Root authorized isolated source work on
`fix/epic440-upgrade-su1-20261108`, base
`a57f02e05ec7a3ce041b1e5547707f7fb878adba`, under normative v1.59
`6be886be` and approved plan SHA-256
`698cbdfc9560a882f628c4a5f49c6096d9f2d39ec3f8fe2c6106b04066baf2b4`.
Requirements role implements; Root owns integration, independent review, PC gates
and every live GO. Separate architecture review governs the cache prerequisite.

## Exact locks

- `tools/linux/qualification/product_upgrade_cases.py`
- `tests/tools/test_product_upgrade_cases.py`
- `tools/linux/qualification/preserving_product_acceptance.py`
- `tests/tools/test_preserving_product_acceptance.py`
- `tools/linux/qualification/wsl_product_acceptance.py`
- `tests/tools/test_wsl_product_acceptance.py`
- `tools/windows/qualification/wsl_acceptance_guest_switch.ps1`
- `tests/fixtures/wsl_acceptance_guest_switch.ps1`
- `tests/tools/test_wsl_acceptance_guest_switch.py`
- `src/tiny_swarm_world/infrastructure/adapters/lifecycle/component_transitions.py`
- `tests/infrastructure/adapters/lifecycle/test_native_component_transitions.py`
- `tests/application/services/test_component_updates.py`
- this record.

S-U2's two legacy fixture files are deferred. No domain/runtime/reader/operation
guard changes, capability-matrix edits, source-fixture maintenance edits or
original-host actions belong to this slice.

## Executable private qualification input

The actual NativeComponentCatalog now exposes ONLY the existing pinned Swagger
UI5.32.6→5.32.7 and Traefik3.7.4→3.7.5 policies with executable qualification
literals in this unpublished candidate. No alternate catalog, arbitrary target,
environment admission switch or production engine guard bypass exists.
Those literals are private test input, NOT an assertion that either host or
preset passed. Public promotion is forbidden until exact-source independent
evidence covers every declared host×preset×owner×exposure tuple, singles,
fault/recovery and persistence criteria. Relevant source changes require renewed
applicability review; a prior runner's live results do not qualify these bytes.

The original eight fresh/add recipe objects, fixed commands and budgets remain.
Sixteen new names form the schema2 ordered24-case ledger: two singles, eight
normal batches (default/service-access × Swarm/Portainer × published/internal),
two interrupted batches, Portainer upgrade/recovery, and two official product
names. The official names explicitly return NOT_IMPLEMENTED before mutation
until S-U2 supplies an actual official schema1 installation and Python3.12.

## Scope, sequencing and proof

Each baseline explicitly binds its public setup preset. Update/discovery/recovery
omit the parser-forbidden preset flag and revalidate the persisted preset.
Fixed source image overrides come only from the real native transition policies;
Portainer source server AND agent are2.45.0, not the current2.45.1 defaults.
Only baseline setup/artifact inputs receive source overrides. Runtime writers
consume the actual public services update/recover command and existing journals,
private leases, profile admission and saved-stack writers. Operator input retains
the exact16 credential keys. Recipe images are a separate closed layer; root,
infra, operator/evidence paths and owned TLS root are assigned last.

Source, target, recovered, no-op and persistence proofs use actual production
profile admission plus complete selected task/image/mandatory-gateway checks.
Additional observations bind actual Swarm/node/service/stack/ResourceControl IDs,
mounts/config/secret references, service versions, task IDs, stack update times,
management journals, Portainer backup checkpoint and mounted Swagger file hashes.
The complete retained Swagger bundle is checked, not only the changed UI image.
Inside-container UI/API HTTP remains meaningful for internal exposure. Real
Traefik API/router checks enforce absence/presence of Swagger ingress.

Root additionally approved fixed private `INFRA/proof-credentials.json`, exact
schema_version1/traefik_username/traefik_password, at most1024B, root0600,
nofollow/stable read and trusted ancestors. Full existing infra hash binds it;
no new public intent field or operator key exists. Schema/user/htpasswd binding
must pass before baseline; plaintext match is proved after actual baseline and
before any upgrade/backup/reapply writer by unauthenticated401 then actual
authenticated200, verified case-owned CA, fixed endpoint, no redirects and
bounded Traefik API/dashboard schemas. Password/header/body remain RAM-only.
Wrong password causes failed-disposed, never PASS. No invented password or
credential hash derivation is attempted. Root has not supplied live inputs yet.
An interrupted cold recovery uses only the same case's actual durable pre-fault
source/auth proof and requires fresh auth after restore, not fabricated pre-restore
API availability. API schema reference:
https://raw.githubusercontent.com/traefik/traefik/master/pkg/api/handler.go
(`rawdata` representation); actual pinned-version behavior still needs live proof.

Fault monitoring reads and type-validates the actual durable engine checkpoint,
installation ID and partial-batch/checked-backup predicate. It durably records
intent, signals only its own known gated Popen process group, and requires group
settlement before recovery or cleanup. A missed window is NOT_EXERCISED and
never a success. No checkpoint, observation, saved stack ID or failure is fabricated.

Separate prepare-engine-recovery / engine-recovery modes bind fresh source/host,
original intent/auth proof, pending typed engine journal, current manifest,
profile/UUID/full graph and own running nodes in an additional engine_binding
GO field. A durable exclusive started marker prevents uncertain replay.
Ordinary900s disposal-only recovery remains cleanup-only. Public engine recovery
uses the original service selection and actual journal; no new fixture is made.

## Budgets and return ABI

Forward component/Portainer case9000 = baseline5400 + exercise3600; WSL containing
10500, native12480. Official reserved case18000 / WSL19500 / native21480 stays
unimplemented. Component/Portainer engine recovery3300 / WSL4800 / native6780;
official reserved10800 / WSL12300 / native14280 stays unimplemented. Containing
GO/phase deadlines are distinct; old fresh cases remain5400/WSL6900/native8880.
No unknown outcome can reset an active operation clock or borrow another phase.

Ledger schema1 still means the eight original names. Schema2 is the exact closed
ordered union of24 names, with actual outcome hashes and run/source/case binding.
Unknown, omitted-declared, duplicate, unordered and unsettled cases are refused.
The Windows consumer rechecks every recorded child process group without ever
signaling JSON-supplied PIDs. Seven-field OWNED_CASES_DISPOSED remains a safety
receipt only. Failure/disposal recovery/unexecuted/unimplemented cases are never
counted as upgrade acceptance. Kernel reset/bridge/original restoration contracts
remain outside this slice.

## Closed cache prerequisite and reconciliation

Root's final code GO and independent architecture acknowledgment extend the source
authority through normative v1.60 `36c45c00`, cache-plan SHA-256
`a8e358e592c7b992383827bbf33f0151fb28f74d060df5f9a8a9f38a996a3bcf`.
The two Portainer recipes use the actual ArtifactPrepareWorkflow and twelve actual
EnsureContainerImage/LxcContainerImagePublisher steps: four immutable source AND
target policy references × three proven case nodes. No Nexus/bootstrap/build/login,
arbitrary image or stack write belongs to this prerequisite. The public scoped
artifacts CLI remains refused; no production guard is relaxed.

The actual same installation lease and private profile runtime context are
admitted before work and each step/verification. Every command rechecks active
lease/current manifest, actual Incus unit/executable/Unix peer/server PID and
version, exact own node UUID/image/markers/full specification. The narrow process
port rejects the publisher's exact host-Docker fallback with ProcessLaunchError
BEFORE execution; only its existing unavailable-host continuation may proceed.
All other unexpected commands refuse. Admitted publisher scripts are rendered
as absolute local Incus exec plus direct absolute Docker, clean environment,
explicit own `/var/run/docker.sock` and no login shell/context inheritance.
There is at most one actual pull per node/reference, bounded streams and an
aggregate900s including admission, calls and final proof inside exercise3600.
Unused baseline time cannot extend exercise. Cachehit causes no pull.
The outer900s deadline includes before/after graph and runtime proof; its absolute
monotonic deadline and boot digest are bound in the private cache intent and
shared with the helper. A child budget cannot restart that deadline. Helper
wall/stream bounds are additionally clamped by the existing owning supervisor.

Initial presence/absence is actual data, including legitimate missing source
server images on workers. Fresh final observations require all twelve real
ImageIDs/RepoDigests, amd64/Linux and identical content IDs across nodes for each
fixed manifest reference. Full before/after case graph, manifest, actual source
runtime/data/ownership and authenticated source proof must remain equal. Public
Portainer apply subsequently consumes its unchanged cached-image admission.
No actual cached-image or live compatibility proof is claimed by this source.

Exclusive durable intent/helper-started/completion metadata prevents cache replay.
Unknown outcomes persistently block later public writers and disposal. Root also
approved fixed READ-ONLY cache reconciliation inside the separately authorized
cleanup recovery phase: actual same source/profile/lease/UUID binding; all twelve
Docker-daemon-ready image observations; no Docker CLI clients on the own nodes;
absent known fixture process groups; empty Incus operations; unchanged complete
graph, manifest and fresh actual source auth/runtime proof. Only then can an
observed-settled receipt authorize safety cleanup. It never reruns ArtifactPrepare,
pulls, resets cache900, renews an expired writer GO or claims upgrade PASS. If
anything remains unknown/missing, explicit Root recovery remains required.

## Qualification still pending

Authored regression scope includes actual fixture orchestration, actual component
executor/runtime/workflow/journals with fake Docker boundaries, fixed public argv,
all tuples, bounded GO variants, actual-checkpoint fault signaling (a committed
unchanged Swagger sibling is insufficient), missed-window refusal, HTTPS
challenge/auth/schema/TLS controls and the actual embedded Windows ledger parser.
The cache delivery regression retains real ArtifactPrepare/Ensure/Publisher,
closed runner/DTO/ownership guards, with fake process/metadata transports; it
checks twelve observations, cachehit/no-pull, single-pull ceiling, manifest/spec
drift, endpoint restrictions and persistent unknown refusal.

AST/diff checks are source-only; no author executed test or host operation.
Root must run nearest PC gates then all seven QUALITY gates on exact frozen
bytes and obtain independent source/security/requirements/architecture review.
Live S02 pairing, genuine matrix admission, operator/proof inputs, routes, resources,
all actual host/preset/writer/exposure transitions, browser/data acceptance and
S-U2 remain prerequisites. No tests, image cache actions or product transitions
were executed by this author; original-host/runtime state was not touched.

Freeze handoff: exactly thirteen allowed files; ten Python files plus four
embedded guest-switch Python probes parsed successfully; `git diff --check`
passed. PowerShell parser, unit, type, architecture and full QUALITY checks remain
NOT_RUN by author. GuestSwitch's original-driver/source constants remain unchanged;
Root will separately integrate the frozen R3 driver pin/API correction. In
particular this source slice does not qualify or implement official0.4.0→0.5.0,
prepare operator inputs, admit the empty matrix, or run any live recipe. A missed
fault window and any unknown cache/execution outcome remain visible non-passes.

R2 independent architecture P2 correction: actual protected manifest raw-byte
SHA/token and component-update checkpoint raw-byte SHA (strict absent/present)
now participate in repeated-operation equality. Initial successful transitions
may commit these fields. Portainer repeat requires its real literal no_op; the
actual component contract emits completed/recovered after live revalidation,
so those exact existing statuses remain accepted with unchanged protected bytes
and all runtime/task/stack counters. No production contract or guard relaxed.
Nearest/full tests remain NOT_RUN by author; Root executes the frozen R2 gates.

R3 essential serial Original-driver integration: Root-frozen external driver
SHAe49744db6992b621fc9410620122536369e9ec04a2ff71ee542f1eac9d3e428e,
SOURCEcb8c0e27c5890c39c03c45502423f2b8bf372ecc, fixed namespace
/root/tsw440-wsl-r5-20261108. Only the three Original-driver path occurrences,
two driver-hash occurrences and its read-only probe ABI changed. The probe
now calls verify_observation(baseline,current,journal,restored=...) with its
already constructed real journal; no veth receipt is inferred or discarded.
New-guest source/parameters and unrelated pins remain untouched. Old driver
artifacts remain immutable. Root owns Driver20/PC-union tests; author AST/diff
only, no tests, hosts, commits or new source scope.

R4 actual PC focused failure correction (Root-authorized production-helper
repair, not a fixture filter): scoped route_device explicitly emits nat=false
and proxy_protocol=false. The generic inventory device whitelist rejects both,
so using that DTO inside the scoped cache guard was incompatible with its own
real manager specification. Cache guard now consumes existing strict product
instance_rows, requires exactly its requested node, and retains unchanged exact
owned_instance/worker_state, UUID/spec/marker/image/provenance/lease/manifest
checks. Actual fixture fields remain intact; no generic inventory whitelist or
production contract was weakened. Root reruns the PC gate; author AST/diff only.
