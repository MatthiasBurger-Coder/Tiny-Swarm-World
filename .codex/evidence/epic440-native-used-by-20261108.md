# Native API reference ordering and causal startup ambiguity

Base128c5e622e5fd445c5a292728c1784b667a12e1d, isolated five-lock stream:
fixture+fixture test, maintenance+maintenance test, this record. Root approved
exact plan before implementation. No hosts/tests/commits by worker.

Actual NativeR6 created three own objects, then rejected unsorted project.used_by.
Cleanup removed all three; original LXD restore briefly encountered typed startup
ambiguity and Root separately recovered. Historical attempts remain failed.

| Requirement | Bounded implementation/test |
|---|---|
| API order is not authority | One pure raw used_by validator requires list, all strings, <=10000, exact uniqueness, then returns sorted COPY. Project/list/detail/profile/default/own/base/cleanup raw boundaries reuse it. Unknown fields, null/mixed/duplicate refs still refuse. |
| No consumer loss | Compare complete canonical consumer sets against unchanged expected refs; no union, inferred refs or omission. GO.default_profile_used_by remains sorted canonical consent. |
| Actual API-shaped full flow | Project fixture now emits grouped instance/image/profile references, deliberately unsorted after first own profile; complete success/cleanup and unchanged foreign route inventory still required. Permutations equal; duplicates/types/cap/edge changes refuse. |
| Ambiguous is unknown | Add exact CHILD_AMBIGUOUS to same own-start raw typed ProvenanceError/direct same-code ProvenanceError-cause gate. Unchained InventoryError/fake cause/other codes refuse. Persistent ambiguity times out25+5; only later full unambiguous binding permits node restore. |

Primary pinned source: https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incusd/api_project.go
projectUsedBy223–295 appends grouped resources and returns without global sort;
projectsGet and projectGet both use it. DTO describes a URL list, not a sort order:
https://raw.githubusercontent.com/lxc/incus/v6.0.5/shared/api/project.go .
Canonicalization is local identity comparison, not a new ordering claim about API.
All existing command/entity/byte/time budgets, fresh full reads, UUID/spec checks,
shared parser/provenance and no-force effects remain unchanged.

## Frozen source handoff

All raw route/project/profile/default/own/base/cleanup API consumer boundaries now
share the exact bounded unique-string canonical-copy validator. Complete expected
consumer equality is retained; canonical consent still requires ordered uniqueness.
Profile returned rows keep every original field and only canonicalize used_by in a
copy. Project refs retain validation without becoming a new exported route field.
Unordered inputs are not accepted by dropping invalid/duplicate/extra consumers.

The full synthetic transport now returns actual grouped Project DTOs (including
new instance/image/profile URL membership) rather than name-only list rows and
missing detail consumers. After own creation these are deliberately not URL-sorted.
The existing complete success/budget/cleanup suites inherit that shape; explicit
success verifies unchanged foreign data/routes and zero own remainders. Additional
unit and actual-transport regressions cover permutation/full-row digest identity,
raw-input immutability, default/own/base/cleanup consumers, duplicate/null/mixed/
limit refusal and list/detail project duplicates denied before any effect.

CHILD_AMBIGUOUS uses the identical gated typed-cause predicate as the other three
codes; no new exception-as-state path exists. Real inventory wrapper/full original
binding tests now cover all four codes, including raw/cause/gate denials. Added
persistent causal-ambiguity test proves unchanged25+5 timeout and no node start,
command or synthetic readiness acceptance. Shared provenance/parser untouched.

Worker static AST and git diff --check PASS. Tests/typecheck/quality/hosts/effects/
commits NOT_RUN. Root owns independent exact review and PC gates before any fresh
scenario GO. Actual R6 remains qualification failure; its successful cleanup and
Root separate recovery do not qualify the new source or invent fixture success.

## Root integration and exact PC verification

Independent requirement review approved the frozen source and the Root R2 test-only
post-cleanup inventory mode correction: it matches main's cleanup reserve and
does not reset any counter/deadline or change production bytes. R1 nearest failed
only this extra test read outside cleanup mode; its failure is retained.

PC WSL R2 on clean base30d91f64 plus these five pinned paths: nearest354 PASS
17.685s, type979 PASS, all seven QUALITY PASS,3643 discovery/36 skipped,333.842s.
Focused log d864ebe595b722851c9f7999ae5a7f4bba4df2197231a56d878823ac8308aced;
type ee87d77b040e083e5206f8f8ba02752746d82f0de54fb88655090618f78e3773;
quality6f83ded7822db602c054f717babd44ca8ebe05daf3c5e5915dd2a67bf72923a6.
Private ext4 copies are byte/hash verified. This documentation append follows
those exact executing source/test bytes; no new live PASS or capability promotion.

Historical actual Native R6 on a814 failed project-reference order, cleaned its
three own objects, then initial restore refused ambiguous wrapper children.
Separate reviewed fresh recovery returned RECOVERED with original three Running.
Complete27-member archive SHA40a3f46b845f9db66709a1c86cccdfc8372b78901e7de10ded82642db2fb0f26
and reconciled private ledger retain both failures and recovery; qualification NOT_PASS.
