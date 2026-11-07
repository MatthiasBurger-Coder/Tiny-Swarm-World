# Existing Incus bridge coexistence during W06 network readiness

Status: SOURCE_REVIEWED_PC_QUALITY_PASS; HOST_REFRESH_NOT_RUN.
Root independently accepted the two-set design and authorized these exact source/
test locks. Base5084fc93, isolated worktree /home/micro/tsw440-network-coexistence.
No worker host actions, tests, commits or runtime qualification are claimed.

## Observed problem and authority

Root reports WSL tsw-incus-forwarding.service failed while Incus remained active.
Its passive projections show two canonical Incus filter/NAT chain sets and two
actual default-project managed bridge identities: incusbr0 and qualbr447. Only
incusbr0 is a configured TSW target. This identifies a source compatibility defect:
network inventory queried all default networks, but verify_nft/verify_chain and
the persisted guard recognized only configured targets. The legacy_nat branch
also required a single global bridge. The service exit alone is not proof that
this predicate was its exact historical cause; fresh live evidence is required.

Names/table prefixes are not owner proof. No resource is adopted, deleted,
reconfigured or renamed to make this preparation pass. Existing issue447 bridge
and consumers remain preservation scope, with no TSW rule generated for them.
Windows firewall and PortProxy behavior are not changed by this code slice.

## Narrow contract and implementation

| ID | Requirement | Production boundary | Evidence state |
| --- | --- | --- | --- |
| B1 | Separate write targets from observed owners | configuration/inventory resolve configured targets and authoritative managed/kernel owners separately | Authored tests, NOT_RUN |
| B2 | Preserve unselected bridge, no new route/NAT | forwarding/input/UFW/missing-rules/planner remain target-only | Real inspect/renderer fixture authored |
| B3 | Prove all native hooks/rules, not prefix exemptions | firewall_inventory verifies complete owner chains and exact NAT; unknown/partial/mixed effects refused | Positive/negative owner matrices authored |
| B4 | Recognize canonical existing legacy NAT | Explicit full-owner proof admits independent exact per-owner legacy rules | No cross-bridge isolation claim |
| B5 | Same proof at persistence startup | Root-owned embedded guard re-reads active Incus identity/default networks/kernel bridges | Executable mocked-command guard tests authored |
| B6 | Preserve authorization/quality boundary | No runtime invocation by author, no capability/version/host readiness claim | Root review and PC gates pending |

The existing fixed default-network read supplies owner metadata. It is bracketed
by exact already-active Incus unit/MainPID observations. Kernel inventory now
requests detailed link data. managed_bridge_owners requires unique actual managed
bridge names, project=default, Created status, fixed private IPv4 and matching
unique kernel bridge kind/address/prefix. IPv6 is disabled except existing kernel
link-local addresses. Owners have nonoverlapping subnets and cannot be the egress
interface. Existing external interfaces, ACL policy, unknown firewall settings or
explicit SNAT address are unsupported and preserved with refusal. DHCP true/false
is observed without imposing the selected target's DHCP requirement on an
unselected owner; selected target validation remains unchanged.

All selected targets must equal a member of the complete owner set. Only targets
reach missing_rules, forwarding_rules, input_rules, ufw_rules and LinuxPlanner
mutation payloads. Complete owners reach NFT validation and fingerprint state.
API visibility of an unmanaged or non-bridge interface never authorizes a native
Incus chain for it. Unknown/duplicate/incomplete chain owners, wrong hook/type/
priority/policy, ACL/drop/reject/jump or extra effects refuse before writes.

Every observed owner must have its complete canonical four-chain set. Modern
bridge-set/bypass form binds exact unique full-owner set membership. Legacy
Incus6.0.5 form admits exactly one own-source/non-own-destination/masquerade per
owner only when explicit complete owner proof is supplied. Existing direct calls
without that proof retain the old multiple-bridge refusal. No NAT is generated.
Canonical legacy rules can NAT between distinct bridge subnets; acceptance
preserves this existing behavior and does NOT attest cross-bridge isolation.
The admitted NAT subset is exact masquerade, not an arbitrary SNAT destination.

Counter removal accepts only standalone typed packet/byte counter expressions;
a counter key mixed with another effect is rejected. Filter checks refuse
unknown control/mutation expressions. UDP checksum clearing additionally requires
the exact owning input/output interface and IPv4 UDP predicate and must be the
sole final effect, preventing an unscoped checksum mutation being exempted.

Generated guard embeds pure validation functions, no writable source imports.
With explicit owners it rechecks a stable already-active Incus MainPID, makes one
fixed local no-state-saving default-network read, observes detailed kernel links,
and compares the full current owners to the approved embedded projection before
any target-only iptables insert. It removes ambient remote/socket overrides for
that fixed read. Added/removed/changed owner or daemon identity blocks. Normal
iptables/UFW/nft owner, compatibility, routing and existing target address guards
remain. Source hashing already includes all changed production helper files.

## Limits and deployment boundary

This finite shape contract does not support arbitrary OVN/ACL/IPv6/forward/QoS
chains, image capabilities or every conceivable Incus firewall mode. It does not
claim cryptographic authorship of kernel rules: authority combines actual local
Incus managed identity, kernel link identity, canonical rule scope and unchanged
preservation fingerprints. No chain prefix alone grants authority.

LinuxPlanner's existing refusal to overwrite a differing persistence asset is
intentionally unchanged. A previously installed forwarding script needs a
separate exact hash/owner-bound replacement plan and result before restarting
its service. This source slice neither silently adopts that file nor modifies
its protection module outside approved locks. New installation rendering and
read-only plan behavior are implemented; live refresh is not yet executed.

No new daemon initialization, network/profile/pool/instance/Windows rule mutation,
service execution or arbitrary callback is added. External writers are not made
atomic by these checks; fresh observation/preservation comparison remains required.

## Verification and handoff

Authored cases include two literal canonical owners with one selected target,
exact legacy/modern positives, retained no-owner-proof and incomplete-set
negatives, a real preparation inspect/render path with no qualbr447 rule, kernel/
API/owner/subnet/IPv6/ACL/NAT mismatches, hidden counter effects, checksum scope,
and execution of the complete generated guard with mocked commands. Guard tests
include missing/new owners, kernel kind change and MainPID drift before effects.
Existing tests use real explicit bridge/project fixtures rather than fabricating
those observations inside production code. Secure file tests remain unchanged.

Worker performed AST syntax parsing only, without imports or test execution,
and git diff --check; both PASS. Typecheck, focused tests and full gates NOT_RUN.
Root must independently review exact bytes, run approved PC WSL checks, integrate
normative records and review committed-source host plans. No live forwarding or
Epic acceptance is inferred from this implementation.

Primary source: Incus6.0.5 drivers_nftables_templates.go defines per-network
in/out/fwd policy-accept chains and pstrt priority100 own-subnet masquerade;
drivers_nftables.go NetworkSetup applies them per network. Both were inspected
read-only during design review:
https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/firewall/drivers/drivers_nftables_templates.go
https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/firewall/drivers/drivers_nftables.go

## Frozen source/test SHA256

- src/tiny_swarm_world/infrastructure/adapters/network_preparation/configuration.py: `9dcec812efff6a0e11d6803c6487119cf1f3d5dde975275cf77fc67cc858c90d`
- src/tiny_swarm_world/infrastructure/adapters/network_preparation/inventory.py: `3c41e1f9c3df5676c0d3ac236d5fdca543313f38691a4295326850f9045376b4`
- src/tiny_swarm_world/infrastructure/adapters/network_preparation/firewall_inventory.py: `df232f7099b0413f010f830d3c01e96ffd274b74761767c64d4e85ddc0dd765d`
- src/tiny_swarm_world/infrastructure/adapters/network_preparation/nat_policy.py: `1c541431d36d5ee13d3a925192f7ced2316f1e2999a99c5ef8dbd3533727bffa`
- src/tiny_swarm_world/infrastructure/adapters/network_preparation/persistence_guard.py: `0e44343b081cdf61596213165e97644a49795c0ea72678ebe39766322e0c57e5`
- src/tiny_swarm_world/infrastructure/adapters/network_preparation/forwarding.py: `98568f460272963641d9b67bc716aadf42432b3d6f08d7e914774e23de10dc3f`
- tests/test_network_preparation.py: `591d1d44de3c15a114bc91598ec13c3a147bf0aeb9f0c137c143d34ba387a5a4`
- tests/test_network_preparation_compatibility.py: `5b164d9d206d6ec22c1b3676644e38bee9a3ef0c35713c4c3ddca4faf24c7821`

## Independent static closure correction before PC verification

The independent automation reviewer found that importing the two owner-proof
helpers into the renderer module did not include their definitions in the
root-owned generated script's inspected-function tuple. The explicit-owner
startup path would therefore NameError before effects. Root has not run this
candidate on hosts and no successful persisted-guard execution is claimed.

The embedding tuple now includes both managed_bridge_owners and
incus_owner_identity. Their dependencies are already closed: standard-library
local imports, the embedded NetworkPreparationFailure and Bridge=SimpleNamespace.
The existing whole generated-guard positive/drift exec fixture exercises this
actual path when root runs it; no weaker duplicate-only test replaces it.
No owner/effect policy, tuple, command, test literal or other source changed.
Source/test verification remains AST/diff only; PC gates NOT_RUN by worker.

Superseding persistence_guard SHA256: `69753c12fa1992e0d7626e38185af27cd99e8c15815cdc67a38022ee7ab1fef7`. Other seven source/test pins above remain unchanged.

## Root integration verification

Root independently reviewed the exact eight source/test files; independent automation review caught and closed generated-helper embedding before execution. Exact nine assets were staged into an isolated ordinary-user ext4 checkout on pc@192.168.178.58 Ubuntu WSL, HEAD5084fc93, Python3.12.15. Typecheck901 files PASS; focused42 tests in4.232s PASS; all seven QUALITY gates PASS, architecture43 and discovery3317 in205.665s with36 skipped, exit0. Private0600 logs remain on PC. Typecheck SHA2566f6a32a73808ce122fc98eec372609559796b467ca1ac47982c877de0facb418; focusbf33a07a8b826c10affe8b70d48af8d0b3bb3e00904b1a12f38c0b1737a70515; quality36b9031355f64fd340083cc257b089574653faafb1193734d053eff6517e590e. No live readiness or firewall effect inferred.

Fresh read-only fixed asset observation and structural recognition of the actual WSL persisted script confirm root:root0755,23797bytes,SHA2566f44e10ef441aa4bec0987f85758bf2272c757d6a0f84710c9881a0876a000bd. Parsing its embedded parameter literals as data and re-rendering with the unchanged5084fc93 template produced byte-identical content, unique absent-UFW/nonrestricted-input match, one target bridge/two ports, parameter digestfe1f1ba83a998e2436500bf9c631d855af7005b576c24e5fdceb3be4f2f0598d. Existing service equals the canonical326byte0644 root-owned service SHA2569ad8118a112ca102b5a61379e464df01f77258aa7a2bd4120bb6e7bb269438d1. Existing sysctl/module assets also exactly match the committed canonical bytes. No file or service was changed. A preserving, exact-old-hash-bound replacement plan remains required before restarting the failed unit.
