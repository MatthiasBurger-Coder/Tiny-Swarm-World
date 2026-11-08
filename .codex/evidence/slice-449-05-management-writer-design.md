# S449-05 bounded management writer implementation

Base: c4ca086a38131c26cb416243bfc70862f22103d4. Root authorized S05 implementation; no live qualification or closure is claimed. Source work only; tests are authored but executed by root on PC WSL.

Requirements: S05-01 explicit new-stack management mode, existing ownership invariant; S05-02 authenticated local Swarm endpoint, unique stack ID, ResourceControl and exact saved definition/environment binding; S05-03 durable pre-write intent, CAS immediately before request, no pruning and preserved environment; S05-04 readback plus actual task convergence before verified ownership/selection commit; S05-05 interrupted/uncertain writes fail closed and resume from checkpoint identity without same-name adoption; S05-06 owner-aware setup/add/component/product recovery dispatch, with direct-Swarm legacy compatibility.

Locks: CLI parser/selection transport, selection planner and selection service (coordinate additive exposure changes with S06); focused application management port/service, infrastructure guarded Portainer adapter/journal, optional-stack composition and tests. Setup profile intent/commit wiring coordinated with S04 owner; no shared ownership model rewrite. Root integrates overlap in composition_setup/lifecycle/setup_state.

New planned mode is separate from post-create verified PortainerOwnership. A fresh intent never fabricates endpoint, stack or ResourceControl IDs. Existing v1 stacks remain Swarm. Portainer credentials and Env remain RAM only; journal stores fingerprints and verified identity, never values. HTTP success is receipt only; readback/task convergence must complete. No implicit ownership adoption, pruning, removal, credential rotation or external route change.

Readiness: canonical ownership ADR accepted, root requirement review and S3D serial integration authorization supplied in task. Production code must keep existing profile admission guards; supported Incus matrix remains empty until S02 evidence. Independent architecture/security and final quality remain root gates.

## Additive delivered-path regression — 2026-11-08

Root requested the real writer-to-manifest proof before gates. The added
`test_managed_stack_delivery.py` uses real EnsureManagedStack,
ManagedDeploymentWriter, GuardedPortainerStackApi, ManagedStackOperation,
LxcUpdateRuntimeObserver, ScopedProfileSetupOperation.record_stack_ownership,
SetupSelectionState.commit and private JSON repositories/operation locks. Only
HTTP and Docker/Incus transport state plus the convergence timer are fixtures.
It requires the coordinated S04/S06 sources after root integration. Assertions
cover pre-write durable intent, no invented IDs, saved definition/Env and actual
parsed tasks before callback, no competing Swarm writer, durable verified owner
then manifest commit, old-task failure, and restart with original returned IDs
without another POST. The managed journal holds no component/product claim while
calling the real profile callback. This is authored coverage, not executed
evidence; PC WSL execution and independent review remain root responsibilities.

## Integration union — 2026-11-08

The integration candidate retains S06 service exposure alongside S05 planned
stack management modes in selection preview, validation, CLI transport and
composition. Both documentation sections remain. Runtime helper builders
forward the explicit profile operation only when provided and preserve the
canonical selection/exposure options together. The delivered-path restart
fixture uses the dedicated profile-recovery lease. Text diff and AST inspection
are source checks only. S04 real consent binding, scoped operation factories,
locked wrapper support and verified ownership-to-manifest commits are now
combined from its independently frozen source; no substitute profile admission
or fabricated ownership is introduced here.

## S04/S05/S06 final source union — 2026-11-08

The S04 44-file input manifest was verified at SHA256
`81a6d208eebf76251f4c96a0c7fbaabaa70cce4afdecbb4037389dea5843ff94`
before the three-way merge against `9de8fa1e531da00cb634a0fa2d8611d2ff5ac345`.
Five conflict files were reconciled: CLI combines both policies and scoped
recovery validation; selective setup retains the matrix-aware legacy fallback
and both preview arguments; setup state uses the actual typed private operation
and one desired-policy admission method; lifecycle preparation passes accepted
consent and original recovery manifest before exposure admission; platform
composition carries exposure into canonical manifests alongside the admitted
private operation or the read-only persisted observer. Existing public
functions and their parameters from the pre-S04 integration remain.

Fresh verified IDs flow through the real profile checkpoint to the manifest
and installation commit; additions retain their separate before/target journal
and checked ownership inventory. Existing owner identities and first verified
new IDs remain immutable except for their definition fingerprint. The
capability matrix is still empty. AST, duplicate-definition, public-API and
whitespace inspection are source checks, not executed delivery evidence.

## Combined PC type-check R1 correction — 2026-11-08

Root executed the first combined type check on PC WSL. R1 failed with seven
errors in two files; log SHA256
`cadffbc5658d772ff171f5726f7d522fb1ed4e4652a81cce0534233da96cd965`.
The domain ownership loop now names its string key `service_id`, preventing
reuse as the subsequent typed service plan. The internal-exposure fixture
uses a scoped patch for its explicit test double; its awaited admission checks
the active lease itself, matching the concrete S04 operation boundary. The
missing-context diagnostic assertion matches that integrated boundary. No
production admission or type contract is broadened. R1 did not run focused or
full tests. R2 and delivery gates remain unexecuted by this author.
