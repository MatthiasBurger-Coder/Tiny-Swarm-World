# WSL Q12 managed-stack design proposal

Status: **DESIGN APPROVAL RECORDED; IMPLEMENTATION AND LIVE EXECUTION NOT YET QUALIFIED**. The 2026-10-27 operator approval accepts the bounded selection-scoped profile and #318 semantics, now recorded in the canonical arc42 ADR package. This records design policy only; it does not establish runtime support or live GO. Implementation, exact-source quality, supported-version decision, fresh fixture/JIT, required cold `/data` backup and scenario-specific live GO remain open.

## Qualification need

WSL Q12 requires a uniquely attributable Portainer 2.45.0→2.45.1 upgrade with
authenticated access, the local endpoint, Portainer data and an existing
Portainer-managed optional stack retained. The upgrade must perform an
authenticated managed-stack update and observe ready Swarm tasks. The separate
no-op repeat is required by parent AC09 alongside Q12, not by the Q12 row alone.
The Portainer `/data` cold backup remains required. The existing Q02 runtime is
at 2.45.1 and has no optional managed stack, so it cannot be downgraded or
treated as the Q12 fixture.

The current shipped catalog has no portless optional-stack candidate. TSW's
selection path deploys Swagger directly through Swarm and commits its selection
after runtime observation. This differs from lifecycle contract §1, which says
subsequent stacks use Portainer. The proposal closes an implementation/contract
mismatch; it does not introduce a new Portainer ownership direction. The
standard Swagger Compose publishes host ports 16080 and 16081. A direct
Portainer stack without a TSW selection record does
not satisfy the fixture contract; a later `services add` restores those
published mappings. The user's `RemoteAddress=Any` approval is only for the
existing Portainer route on port 10001.

## Candidate direction for review

1. Keep first-time Portainer foundation deployment on the existing direct
   Swarm path. Once Portainer and its local endpoint are ready, route every
   selected optional stack create/update, including Nexus, through a new
   optional-stack use case/composition over the existing
   `PortDeploymentGateway` adapter. `EnsureServiceStack` and
   `EnsurePortainerStack` application abstractions exist, but current composition
   does not wire them for optional setup; `LxcPortainerHttpClient` is currently
   wired for Portainer administration/endpoint operations. This is a new
   executable path, not activation of a supported current path. Preserve
   explicit dependency order; deploy Nexus after Portainer endpoint readiness
   and require Nexus readiness before any selected stack whose image source
   depends on it. Continue to use Swarm service/task observations as the
   readiness authority.
2. Add a typed Swagger exposure choice: `published` remains the default for
   new installations and legacy manifests; opt-in `internal` removes Swagger
   host-published mappings while keeping internal Swarm services. Internal mode
   promises no direct host URL; it is not isolation from other Swarm services.
   It must persist and replay through setup, service addition, update and
   verification. Preserve published-mode Q03/Q04 behavior: direct ports 16080
   and 16081, UI/API/OpenAPI responses, TLS/auth checks where applicable, and
   service-access output. Decide explicitly whether internal mode suppresses
   the Swagger Traefik/customer-facing route when Traefik is selected; the Q12
   fixture must not acquire that route implicitly.
3. Transform Compose structurally and verify the resulting Portainer definition
   and Swarm services have no host-published Swagger ports before committing
   selection. Do not change firewall, PortProxy, host profile, shared network or
   other stack configuration.
4. Before update, bind the TSW selection to the local endpoint ID, stack ID,
   ResourceControl/ownership identity and saved-definition fingerprint. A
   matching name and Portainer Type 1 alone do not prove that it is the selected
   TSW stack. Fail closed on ambiguous, foreign or unmanaged stacks. The current
   HTTP update adapter sets `prune=true`; change or parameterize that behavior
   before this path is usable. Do not prune services during ordinary
   setup/update. Commit installation selection only after required tasks
   converge. Existing optional stacks were deployed through Docker Swarm and
   do not have a persisted per-stack owner in the current manifest. The v1
   migration must record them as `swarm`-owned. Keep those stacks in their
   current path and fail closed if a new Portainer-managed operation is
   requested until a separately reviewed explicit migration/adoption operation
   records verified endpoint, stack and definition ownership. Never take over a
   same-name stack or silently switch deployment owners. Fresh installs may
   record `portainer` ownership only after successful API deployment and Swarm
   convergence.

## Contract and compatibility work required before implementation

- `InstallationManifest` is strict schema v1. Persisting exposure requires an
  explicit schema-v2 contract and reviewed v1→v2 migration that maps existing
  state to `published` and `swarm` ownership, preserves identity/provenance, and
  does not silently mutate during reads. New installs may persist `portainer`
  ownership after verified deployment. Coordinate this model ownership with
  issue #318; do not introduce a parallel service-option schema or confuse
  manifest schema with product configuration schema.
- Review all manifest readers, product-upgrade checkpoints, restore paths,
  selection previews, route/access output, readiness, desired Compose snapshots
  and future reconciliation. Older/unsupported readers must not replay a
  canonical definition that reopens ports. If the default product's
  `ProductIdentity.config_schema` or product-upgrade migration/recovery contract
  also changes, version and validate that migration separately from the
  installation-manifest v2 migration and update the supported release matrix.
- Use one effective selection/exposure snapshot across `infra/config/ports.yaml`,
  `infra/config/services.yml`, `ServiceStackContract.port_ids/endpoints`,
  setup-manifest and selection previews, effective-access output, preflight port
  availability, readiness/host-port observers, Compose generation and later
  reconciliation. Internal mode must remove published-port expectations from
  all these surfaces, not only the Compose `ports:` entries.
- Resolve the accepted service-access ADR's `published port 8084` statement
  against current Compose/port registry values 16080/16081 before documenting
  published compatibility. Port 8084 is a container target in the current
  Compose contract.
- Add regression coverage for migration/defaults/rejection, selection preview
  and replay, internal Compose and route output, Portainer ownership/endpoint
  checks, no-prune behavior, async deployment completion, Swarm readiness and
  commit-after-convergence. Run the applicable architecture and full quality
  gates on the mandated SSH/WSL test host.
- Bind Portainer API requests to the local WSL route; never send credentials or
  JWTs through an external client or record them. Keep the cold `/data` archive
  private and mode-restricted. Verify that neither the saved definition nor
  live service specs contain published Swagger ports.
- Update the approved ADR and arc42 only after the decision and compatibility
  contract are accepted. Keep existing ADR history intact.

## Historical review gate results at R60 (2026-10-26)

The following decisions are the pre-approval R60 snapshot; the 2026-10-27 operator decision below supersedes the product-policy and route-scope questions. Live qualification remains separately gated.

| Review | R60 result | Open condition at R60 |
|---|---|---|
| Requirements | NO-GO | Confirm whether `internal` is supported product behavior or a private qualification-only fixture; preserve existing published behavior and customer routes. |
| Architecture | NO-GO to implementation | Accept the proposed manifest v2 ownership/migration contract and explicit legacy-adoption boundary; reconcile the accepted ADR's 8084 wording with the current 16080/16081 contract; approve the new optional-stack use-case/order and no-prune/readiness semantics. |
| Security | Conditional fixture acceptance only | Swagger 16080/16081 must remain unpublished; Portainer 10001 remains the only approved route. |
| DevOps | NO-GO for current candidate fixture | Need a supported provisioning path with both persisted TSW selection and Portainer Type-1 ownership. |
| Live operation | NO-GO | Requires accepted design, implemented and quality-gated candidate, fresh isolated 2.45.0 fixture, new Q12 Three-Amigos GO, cold `/data` backup and immediate JIT. |

No host operation, firewall rule, PortProxy, network or profile change is
authorized by this proposal. Q12, WSL LIVE-4, AC5 and #449 remain open.

## 2026-10-26 route approval and Amigos re-review

The user explicitly approved a WSL minimal Portainer setup using the existing
TCP/10001 route with its `RemoteAddress=Any` rule, with no firewall or
PortProxy edits. That approval resolves use of the existing Portainer route;
it does not authorize enabling the four other wildcard relays in the attached
`docker-swarm-manager` profile. A fresh Architecture review found that the
pinned `--minimal` flow still attaches that profile and that `platform expose`
does not remove stale relays for unselected ports. Recreating the manager
would therefore restore routes on 80, 443, 16080 and 16081. Requirements and
Test/Evidence also confirmed that a minimal installation cannot satisfy Q12's
managed optional-stack, 2.45.0 source, ownership and `/data` preservation
evidence. The three Amigos disposition is **NO-GO for live setup or Q12** under
the currently approved scope. No host operation was run. Reconsider only with
a source-backed isolation path that preserves the pinned profile contract or
explicit acceptance of the additional route scope, followed by a separate
Q12 fixture and review.

## R53 route-consent revalidation — 2026-10-26

The operator accepted the existing WSL Portainer route's
`RemoteAddress=Any` setting for this run. Requirements, Architecture and
Test/Evidence reviewers independently confirmed that this accepts use of the
already configured Portainer API path on port 10001 only. It authorizes no
firewall/PortProxy edits, Swagger host-port publication on 16080/16081, or
Traefik/customer route changes. It does not decide whether persistent `internal`
exposure is a supported product option or a fixture-only override.

The revalidated gate is **NO-GO for Q12 implementation and live execution**.
The current 2.45.1 fixture has no selected Portainer-managed optional stack;
current Swagger selection publishes host ports, and a Portainer-created stack
does not persist the TSW selection. The design still needs an explicit owner
decision on persisted versus fixture-only exposure semantics and route behavior,
followed by reviewed manifest/ownership migration, implementation, quality gates,
a fresh 2.45.0 fixture, cold `/data` backup, immediate JIT and a new scenario
Three-Amigos GO. No Q12 host operation was run for this revalidation.

## R60 shared-contract ownership gate — 2026-10-26

Three-Amigos design follow-up confirmed that every current optional Compose
stack publishes at least one host port; the mandatory Portainer foundation is
not an optional managed-stack substitute. A manually created Type-1 Portainer
stack or one-off Compose edit is not representative because current TSW
selection persists direct-Swarm deployment and may reapply the published
definition. No supported path currently satisfies both Q12's selected
Portainer-managed optional-stack proof and the approved 10001-only route.

The product-valid direction remains an opt-in persisted Swagger exposure mode
with `published` as the behavior-preserving default and `internal` suppressing
all host-published ports and implicit Traefik/customer routes. This is a shared
installation lifecycle contract, not a fixture-only override. GitHub #318 is
open and owns the logical service contract: MR05-01 covers schema, ownership
and migration; MR05-08 covers lifecycle semantics; MR05-10 covers migration
and documentation. The proposed boundary is installation manifest v2, with a
reviewed v1→v2 migration defaulting existing installations to `published` and
`swarm` ownership. Product `config_schema` stays separate unless product-owned
configuration changes.

At the R60 checkpoint (2026-10-26), implementation/live Q12 was **NO-GO** pending the product-policy and route decision, #318 owner acceptance, accepted ADR/arc42 updates and a new implementation Three-Amigos GO. The operator decision recorded below resolves the product-policy and route-scope questions; it does not itself authorize implementation or live execution. Canonical ADR review is now recorded as accepted design policy. Implementation and live execution remain gated on exact-source implementation and quality, a fresh fixture/JIT and scenario-specific live GO. Profile-policy approval does not close Q12 or R35. See the private `three-amigos-r60-q12-contract-review.md` for the historical R60 decision.


## 2026-10-27 approval disposition

The operator approved selection-scoped Incus profiles and the bounded #318 manifest/optional-stack semantics. This resolves the previously open product-policy question in R60. It authorizes no host route beyond the already approved WSL TCP/10001 path and makes no change to Windows firewall or PortProxy rules. The selected internal Swagger fixture must not publish ports 16080/16081 or an implicit Traefik route. Canonical ADR design policy is recorded. Source implementation, full quality gate on the exact candidate, supported Incus-version decision, fresh host JIT, cold Portainer /data archive required by the upgrade contract, and a new same-hash Q12 GO remain prerequisites. Q12 and aggregate #449 status remain open until those checks pass.
