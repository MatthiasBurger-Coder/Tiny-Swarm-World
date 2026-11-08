# EPIC440 S06 — explicit internal Swagger exposure

## Authority and bounded scope

Root authorized this source-only implementation on 2026-11-08 in the isolated
`fix/epic440-swagger-internal-20261108` worktree based on
`9de8fa1e531da00cb634a0fa2d8611d2ff5ac345`. The operative S06 requirements and
parallel source implementation ordering apply. This record grants no host,
capability, supported-version, fixture or deployment acceptance.

## Implemented contract

`SelectionPlan.service_exposure` is a complete closed map: exactly selected
Swagger maps to `published` or `internal`; a selection without Swagger has an
empty map. Fresh and schema1 policy defaults to published. Planning inherits a
persisted policy unless explicitly supplied. `--swagger-exposure` is accepted
for setup and additions; removal and component-update combinations are denied.
Verified selection commits retain policy, installation identity, component and
credential/configuration references, and existing installation-profile binding.
An unverified schema1-to-internal metadata write is refused.

The canonical `default_setup_manifest(..., service_exposure=...)` is the common
source for preflight ports, bridge mappings, platform exposure and WSL socat
plans. Internal Swagger contributes neither 16080/16081 nor implicit 80/443.
Actual selected Traefik can still require 80/443. Compose transformation removes
Swagger publication and Traefik labels, rejects host-network arrangements, and
preserves other service definitions. The access model has no Swagger public
route or published diagnostic fallback in internal mode.

Internal readiness uses the existing managed-node shell port and the exact four
Swagger Swarm services. It checks namespace, absent desired/actual published
ports and absent Traefik labels before and after requests. One running NGINX
task is selected by its exact service label and full container identifier. Curl
runs inside that existing task against NGINX/API `/status`, UI and Editor, with
HTTP-only requests, disabled proxies, bounded time and no redirects. There is
no host-port fallback or new helper container. A custom NGINX image without
curl fails readiness; no package installation or fallback is attempted.

Desired internal setup requires `profile_operation.admit_desired(plan)` with an
active installation lease before runtime composition. The structural
`ProfileExposureAdmission` port is compatible with S04's complete private
profile context. This source slice alone intentionally refuses internal runtime
setup without that context. S04 integration must bind its actual context before
`prepare_setup_selection_state` calls `state.admit_exposure()`. The existing
legacy-runtime guard is unchanged: inherited/shared manager proxies are not
adopted or silently removed. S04 must verify complete effective route absence;
filtered Compose output alone is not runtime proof.

## Source and integration boundaries

Changes cover exposure policy/planning/verified persistence, CLI selection,
canonical service and ingress manifests, Compose projection, managed Swagger
readiness, composition forwarding, and the explicit pre-effect profile gate.
User documentation describes preview, defaults, persistence and admission.
The new focused test module authors policy, real repository/persistence,
canonical networking projections, composition forwarding, readiness, CLI and
private-admission regressions. The shell regression executes only a temporary
fake Docker binary when the designated test executor runs it.

S04 owns the real profile lifecycle and capability admission. S05 independently
adds stack ownership modes in another worktree. Root must merge the narrow
selection/parser/composition overlaps; this slice does not invent Portainer
ownership or enable a closed runtime matrix. No lifecycle manifest schema or
product-reader support declaration is relaxed.

## Validation and remaining acceptance

Author performed Python AST parsing of all changed/new Python files and
`git diff --check` only. No product imports, tests, shell probe, hosts, runtime
commands or commits were executed by this author. The fake-Docker regression
is authored, not a claimed runtime result. Root must independently review exact
pins, run typecheck, focused tests and all required quality gates, and preserve
any nonpass before integration. Live internal Swagger requires the separately
admitted S02/S04 runtime and end-to-end acceptance; none is claimed here.

Primary command semantics consulted during implementation:

- Docker exec: https://docs.docker.com/reference/cli/docker/container/exec/
- Official full Alpine NGINX image includes curl:
  https://raw.githubusercontent.com/nginx/docker-nginx/master/mainline/alpine/Dockerfile

These references justify the read-only command choice, not an image or host
qualification claim. Actual image authority remains the existing pinned
component inventory and runtime checks.


## R1 correction and actual-network readiness boundary

Root's first designated PC typecheck failed with three errors (retained log
SHA256 `c964a186aafefc5365de8ac61f3eba0baeab63ed7a13b38f8edee28c45f61c9f`).
Focused tests and full quality were NOT_RUN for that attempt. The bounded thaw
adds the explicit variable-length contract tuple annotation, uses the existing
`selection_options` helper in the public artifact builder (also fixes the lost
exposure argument), and passes the actual service-profile enum in its socat
regression. An additional public artifact-builder regression binds both options.

The actual read-only shell now checks all four service TaskTemplate network
sets before and after the requests. Each must contain exactly one canonical
25-character lowercase base36 Swarm network ID, all identical, and network
inspection must return that exact ID, `service_access_link`, driver `overlay`
and scope `swarm`. Empty, additional, malformed, unknown, foreign-name,
host/bridge-driver or local-scope networks fail before the first HTTP request.
The selected NGINX container has its exact full ID, service label and running
state checked before and after requests. Its actual NetworkSettings map must
contain exactly the same named overlay and ID. Host NetworkMode is refused;
`default` or `bridge` mode alone does not imply a host bridge attachment and is
accepted only with that complete actual overlay endpoint proof. The other
accepted modes are the exact canonical network name or ID. Unknown modes fail.
These observations are bounded drift checks, not an atomic runtime claim.

The fake-Docker shell fixture authors positive default/bridge/name/ID modes
with exact overlay endpoints; all four service targets are asserted. Negatives
cover service host/bridge drivers, unknown/malformed/additional/empty networks,
wrong name/scope, task host/unknown mode and wrong/additional/empty actual
endpoints, plus task identity, host-mode and service-network drift after HTTP.
Every initial admission refusal asserts no curl was called. Post-request drift
cannot produce the closed readiness success. No test, shell fixture, product
import or host command was executed by this author. Python AST parsing of the
four changed Python files and embedded fake-Docker program plus diff whitespace
inspection passed; a fresh designated PC typecheck/focused/full gate remains
required before integration.

Primary implementation references for these shape decisions:

- Moby v28.3.3 carries overlay endpoint configuration separately from predefined
  host configuration modes:
  https://raw.githubusercontent.com/moby/moby/v28.3.3/daemon/cluster/executor/container/container.go
- Moby v28.3.3 normalizes an empty container NetworkMode to NetworkDefault before
  applying provided endpoint settings:
  https://raw.githubusercontent.com/moby/moby/v28.3.3/daemon/create.go
- SwarmKit opaque network-object IDs use a fixed 25-character base36 form:
  https://raw.githubusercontent.com/moby/swarmkit/master/identity/randomid.go
- Overlay driver and Swarm scope:
  https://docs.docker.com/engine/network/drivers/overlay/

These references explain a strict admitted DTO shape; they do not claim the
host runs that Moby revision or has passed actual internal Swagger readiness.
No Compose/network creation or new capability declaration is introduced.

Frozen correction assets (SHA256):

- service_stack_contract.py: `bcd19518d4cc4f0835964ce94c9ca44481d8f1011cfb906d9595e7889c25cd20`
- composition_artifacts.py: `b22444cf4331f50aab39326a1e20a948f2a823599880ef5950f1ccfcfa360592`
- swagger_readiness.py: `5bb6daf3ef13cbfe5b1cfecc4584d72bfd4f0d9c3f776ef4e909a5c9b81deb2f`
- test_swagger_internal.py: `7eaed48d8f3d1d6f6598a195ccf254f16997c1bb778caf38880c77b1a49b78c1`

## R2 designated PC outcome and port-policy decomposition

Root's designated R2 PC checks passed typecheck (915 files, log SHA256
`7d74db01632c1ec4cb2c364cb309768f7028d461a6f1cabb9bca8ef123f6a0f0`)
and focused tests (41 in 18.621 seconds, log SHA256
`d2ac9f7749629376e528bedc036e56742e2d37cc1804c6baa949a624c9b93bcc`).
Full quality then stopped at the grown-module-coupling guard for
`compose_file_repository_yaml.py` (retained log SHA256
`09b6d2444d7bdfd95821804349e33f635115eddbd904ecb41efa383d25bc8f7c`).
This was not an all-gates PASS and grants no runtime acceptance.

The narrow subsequent correction extracts the actual host-port projection
responsibility into `compose_port_exposure.py`. `ComposePortExposure` owns
normalized selection exposure, the existing canonical direct-port ID table,
and the unchanged direct-port entry mutation/absence-error rules. It applies
the existing internal Swagger payload transformer for internal Swagger, where
no direct published entries remain. The repository retains filesystem/YAML
loading, structural validation and serialization, and asks that policy whether
the validated payload changed. This removes the port assignment algorithm from
the already large repository rather than moving imports behind a facade. The
existing `swagger_exposure.internal_swagger_payload` public helper remains
unchanged and compatible with its callers. No guard threshold, baseline,
exception, desired port assignment or publication policy is changed.

Existing real repository regressions cover assigned port-registry remapping,
missing mappings, absent external ports and internal versus published Swagger;
the authored readiness/fake-Docker tests are unchanged from the R2 candidate.
Author performed only Python AST parsing of the two changed/new source assets
and `git diff --check`, both PASS. No tests, product imports, hosts or commits
were run. Root must independently review the decomposition and run a fresh
PC typecheck, focused suite and all seven gates; R1 and R2 nonpasses remain.

Frozen R3 delta assets (SHA256):

- compose_file_repository_yaml.py: `ccdcc39a79fb8ca83f5003ce507b0c2fb0c41537c7951cb8e9cf2e7913be135e`
- compose_port_exposure.py: `066b74dd4bcfa3547008ca020fa453fd36ac5dac866463b09638f67d08c0c038`

The four R2 correction hashes above remain unchanged. No live readiness,
deployment, runtime matrix or capability acceptance is claimed.

## R3 nonpass and conditional-route compatibility correction

Root reported the R3 source-complexity guard, typecheck and focused checks
passing. Full discovery ran 3394 tests in 205.164 seconds and failed with one
error and one failure (retained full log SHA256
`608b91786acd7df71650e4d80a30f1305f50d537e4df96565f93d3a3cb698f27`).
There is no all-seven-gates PASS for this attempt.

The error exposed conditional route IDs being incorrectly submitted as service
stack IDs. Both HTTPS and direct-access ingress projection now iterate the
complete service-profile contract set, as before this slice, passing its complete
Swagger exposure map (`published` when Swagger was not selected). The existing
explicit stack selection filters and conditional-route handling remain in place.
Strict `service_stack_contracts_for_profile` validation is unchanged: conditional
IDs are route inputs, never falsely admitted as supported stack IDs. A focused
regression covers the actual selected grafana/Traefik route combination and the
same conditional ID without Traefik; only Portainer receives a direct endpoint.
Existing internal/public Swagger regressions continue to bind the exposure map.

The failure was the stale README governing hash. Only the existing README entry
in the persistent `skill-registry.json` cache is refreshed from the file's actual
uppercase SHA256, following the existing hash-invalidated cache convention and
`test_governing_hash_cache_matches_repository_files` contract. New README hash:
`8B304732AB3BE714D82A313A036DE9C505A39B5970015383DA737FE31E9F9DDD`.
No governance verification rule, registry counts, baseline or exception changes.

Frozen R4 correction SHA256:

- desired_state.py: `6314b2097ab5f4af5268ce591663e91f6dd93040798da7f2e32be2fb2cbebb1f`
- test_swagger_internal.py: `c260fd2c0c048f51395089a95c6d66f084978e5d00c0b11e40748011a5778463`
- skill-registry.json: `d8af154c0d01285b5987113737c7b77b761c8e75ec080b540df4a3a03b01c95c`

Author performed Python AST/JSON parsing and diff whitespace inspection only,
PASS. No tests, product imports, hosts or commits. Root retains the failed logs,
reviews the narrow delta over its integrated S03 base, and runs fresh designated
PC typecheck, focused Swagger plus ingress and all seven quality gates. No live
acceptance or capture authority is introduced.

## Root final independent source review and PC R4 qualification

Root independently reviewed original exposureplanning/persistence/CLI/Compose/network/readiness/composition, actual network/taskbefore+after proof and genuine ComposePortExposure extraction. Strictstackvalidation retained; conditionalroute regression fixed through original fullcontractiteration, READMEgoverningcache onlyactualhash changed. Earlier R1typing/R2coupling/R3conditional+cache failures retained. Exact32pins PCc4base type916 PASSda06f118d3ca307fc9c9bfb45bb70534ff3f38bd8d739b77cf5d470ed697ba73; focused62/17.912s PASS64aefb177df029654cf810014a638914f3330633f2efcf8633904ffb8ee798f3; all7 QUALITY PASS3395/234.306s/36skips, quality87acb342c1643884f47c55725d64740e7983c43436879a0ce05395e914d40825. Logs stayPCprivateext4. Exactsource/test Rootintegration only after gates; this resultprose appended afterward. No S04matrix/runtime/Swaggerlive/EPICcompletion inferred. S04/S05 actualcomposition merge andfullcombinedgates stillrequired.
