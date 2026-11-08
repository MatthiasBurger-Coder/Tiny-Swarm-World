# Integrated R3: original creation completion recovery and fixture assets

Root authorized this R3 correction in the isolated integration worktree after
independent static S04/S05 interaction review of R2 manifest
20e4d6ee246fc14a1e412468aa8ebc5fde2aef79363af200d18d14884f790e8c.
All82 R2 asset pins matched during review. This author authored S06 earlier;
that independent review was explicitly limited to merged S04/S05 and their
interaction. Root independently reviews S06 and these newly authored bytes.
No host, test, runtime import or commit by this author.

## Concrete interruption defect

The actual CLI writes the adopted manifest with `state.commit()` and only then
calls the original profile operation's `commit_installation()`. A crash or failed
final readback between those two durable writes leaves a real manifest and an
uncommitted creation checkpoint. Existing preparation routed an existing
manifest into profile-change recovery; there was no change checkpoint, and
normal retry rejected the uncommitted creation history. Reusing fresh preparation
would also reject the original pre-adoption manifest token. No runtime failure
or live deployment of this source is inferred from this static finding.

## Narrow continuation and binding

An optional internal profile-checkpoint `installation_manifest_sha256` binds the
complete validated final candidate, canonicalized including component observed
versions, owner identities, source/credential references and policy. It is saved
under the existing lease and journal CAS BEFORE original adoption. Once set,
the real journal refuses changing/removing it. Older absent fields serialize
unchanged; this is not a product manifest schema or version-support change.

Only explicit recovery of an existing adopted scoped installation whose original
creation is not marked committed enters the new typed creation-completion
continuation. It requires the original completed checkpoint/no pending action,
exact candidate digest/current plan token, requested/resolved policy, complete
verified owner history, original profile/installation/checkpoint/source identity,
capability admission and fresh original manager/worker/listener/preservation
proofs. Source cleanliness/revision is checked through the original transport.
A partial older checkpoint without the write-ahead digest is never guessed.

Read-only current deployment verification uses the existing actual Swarm observer
and guarded Portainer API. Managed owners require the exact saved IDs,
ResourceControl, file/Env fingerprint before and after all member task checks;
Swarm owners use the canonical source/manifest image projection. This path has
no deployment method. Unavailable or changed proof blocks completion safely.
Only then the original InstallationProfileService marks its original creation
checkpoint committed under the existing exclusive lease/journal. Public CLI
returns a completion-only result before building runtime setup services. It does
not adopt, initialize, start, redeploy, reconfigure or rewrite the saved manifest.
The original service's final proof/digest check remains mandatory, and marking
an already committed checkpoint is idempotent. No legacy guard or capability
matrix is relaxed; no alternate runtime executor is introduced.

## Authored regression and actual R2 evidence

Root reports the R2 focused run executed174 tests in30.885s with exactly three
Catalog/native-asset errors, full quality NOT_RUN, retained log SHA
44cd54a003779e77400ae7687465d60b2eeedf20a349174ab5745e354b96c5dd.
Those were the two new managed delivery tests and the public read-only profile
observation test. Their temporary repository roots had only state/capability
files; NativeComponentCatalog legitimately requires that root's real infra
assets. Fixtures now copy the authoritative source infra tree before writing
their private capability fixture. No guard or catalog validation is mocked away,
and source files/capability matrix remain unchanged.

The new recovery regression adopts through the real writer/profile/manifest
path, leaves the original checkpoint uncommitted to represent interruption,
then invokes the real public selective CLI and preparation with a fresh lease.
Only host/provider/Git/HTTP/Incus/Docker transport boundaries are fake. It refuses
changed live managed Env, then completes unchanged saved state with no second
POST/PUT, node effect, setup deployment or adoption and exact manifest bytes.
Additional regressions reject changed manifest/policy/UUID and immutable digest
replacement. Existing full management delivery/read-only tests remain intact.
These regressions are authored, NOT_RUN by this author.

Author validation: AST parsing of changed/new Python and `git diff --check` only.
Root must independently review exact R3 pins and execute PC typecheck/focused/all
required gates, preserving R2 nonpass evidence. No live authority, enabled
capability, integration acceptance or EPIC closure is claimed.

## Independent R3 review and R4 correction

Independent review found that the new read-only completion loop covered only
optional ownership entries. Minimal selection had no such entries and could
miss failed mandatory Portainer services/authentication. It also identified
that the replicated-only update observer cannot prove the global agent or
successfully completed Pulsar bootstrap jobs. These are source findings, not
claimed successful runtime behavior; R3 is superseded for acceptance.

R4 reuses the existing ClassicProductRuntime whole-selection inventory and its
real verify_service semantics instead of the update observer. Every selected
container component, including mandatory Portainer server and agent, requires
current desired-image/task proof. Stored observed images, when present, are
also checked without changing them. Incus retains its separate admitted full
client/server/runtime proof and refuses inconsistent supplied host identities.
Authenticated uniquely local Portainer endpoint/actual Swarm identity is checked
before and after even for minimal or Swarm-only policy. Persisted optional
Portainer IDs/ResourceControl/file/Env are still checked before and after tasks.
The global agent additionally must have exactly one current Running task with
the correct desired/observed image on every admitted manager/worker Docker node;
node names, ready/active states, complete membership and before/after readback
must match. A merely nonempty global task set is insufficient. Completed
zero-exit bootstrap tasks use the established one-shot proof and remain valid.

New negative completion regressions cover minimal and Swarm-only policies:
wrong server/agent tasks or disconnected authentication must leave the final
marker false and metadata unchanged. A separate real-read-adapter regression
requires agent worker coverage, admits the successfully completed Pulsar job,
and refuses its failed exit. Fake Docker transport models global and one-shot
responses rather than claiming all services are replicated/running. The new
post-adoption test's second lease is correctly `profile-recovery`; original
creation retains `setup`. No admission guard is mocked away or relaxed.

R4 author checks remain AST and diff whitespace only, with no tests/imports or
hosts. Root independently reviews and executes the frozen successor; no R3/R4
quality or live pass is asserted in this record.
