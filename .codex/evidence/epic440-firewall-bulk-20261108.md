# EPIC440 — complete bulk Windows firewall preservation snapshot

## Scope and authority

Root authorized the narrow Firewall-only correction after independently reading
the actual read-only diagnosis. Isolated branch
`fix/epic440-firewall-bulk-20261108`, base commit
`08541b3f9588369619e88222565d8424bc9c748a`. Initial four-file scope was
subsequently expanded by explicit Root approval to the seven-file shared typed
asset candidate below. Earlier candidate/gate descriptions are historical;
the final superseding typed contract is the active handoff. No
resource, guest, daemon, service, profile, WSL, firewall, hosts or PortProxy
mutation is authorized by this source change. DF30 host sources stay immutable.

The prior unchanged production Snapshot timed out in its Firewall child at
120018ms (exit124); the task child succeeded in1429ms. Full actual source
verification passed before/after. Private diagnostic artifact SHA256
`7ddfc077b43cc85539a760d6cee5822e48ddd134c456d758abe326168d8515bf`.
The timeout proves the aggregate firewall command exceeded120s, not a measured
specific inner CIM call, output size, or malformed cmdlet parameter.

## Provider contract and actual read-only evidence

Microsoft documents complete ActiveStore enumeration of each NetSecurity
family and automatically managed one-to-one filter/rule relationships. Rule
and filter InstanceID is their real unique identity within the PolicyStore;
explicit provider associations link the genuine rule and genuine filter.

- https://learn.microsoft.com/en-us/powershell/module/netsecurity/get-netfirewallapplicationfilter?view=windowsserver2025-ps
- https://learn.microsoft.com/en-us/windows/win32/fwp/wmi/wfascimprov/msft-netapplicationfilter
- https://learn.microsoft.com/en-us/windows/win32/fwp/wmi/wfascimprov/msft-netfirewallrule
- https://learn.microsoft.com/en-us/windows/win32/fwp/wmi/wfascimprov/msft-netfirewallrulefilters
- https://learn.microsoft.com/en-us/windows/win32/fwp/wmi/wfascimprov/msft-netfirewallrulefilterbyapplication

Two bounded task-owned read-only provider probes retained only finite counts,
identity-equality/association booleans and error categories. DF30 controller
hash checked before/after; no production source or runtime state changed.
Probe1 artifact SHA256
`a600076b39eb062e10bc6c9c08968fdefd6579bf8713d519061eaeb876b99dcf`:
543 rules and543 filters per each of seven families, all actual InstanceID sets
unique and equal. An exploratory .NET CIM/WQL association query did not qualify
(QUERY_EXCEPTION); the speculative PolicyStore query-option assumption was not
confirmed. This path is NOT used by the implementation, and there is no
unscoped/PersistentStore fallback or claim that the provider lacks associations.

Probe2 artifact SHA256
`8ffdcee2775bf90da00558bcf59cd78305590eb8ed0361738988eacecb2e3822`:
actual supported `Get-NetFirewall*Filter -PolicyStore ActiveStore
-AssociatedNetFirewallRule <genuine-row>` on first/middle/last rules returned
exactly one filter with the same actual InstanceID for every family (21 actual
native association observations), while all complete bulk identity sets still
matched543 rules. Whole probe completed in about3.2s. This is evidence for the
bounded current provider identity model, not a universal Windows version or a
newly qualified full snapshot performance claim. Explicit associations are
proven through supported NetSecurity commands, never an invented same-key join.

## Implemented comparison representation

`Get-WslMaintenanceFirewallCommand` is a pure source getter. The exact same
child script runs in production and fixtures. Production uses the existing Run
process adapter with unchanged120s per-child limit,14680064-byte output limit,
aggregate command/time/byte bounds, same source/owner/host/registration gates.
No new source import or external helper/deployment dependency is added.

The script performs one complete ActiveStore enumeration each for rules,
profiles, global settings and all seven prior filter families: address,
application, interface, interface_type, port, security and service. Every
returned property, including foreign/unknown properties and actual provider
identity/metadata, is retained. It recursively canonicalizes property names and
sorts top-level entity rows by exact native identity (full canonical row for
global settings without an assumed identity field); property-array ordering is
preserved. Rule/filter rows stay independent complete arrays: no per-rule
subset, reconstructed edge or dropped foreign entity.

Rule and each family identities must be unique, nonempty strings; complete
family identity sets must equal the actual rule set. Fixed first/middle/last
native association probes require exactly one returned filter, the same actual
identity and complete property equality with its corresponding bulk row. This
explicitly admits the observed automatically managed native identity model and
rejects unsupported/ambiguous/partial/drifting representations. It never
fabricates an association by guessing one field or associates by display name.
The native rule Profile field and complete global profile data remain present.

There are at most31 explicit NetSecurity cmdlet calls regardless of rule count:
10 bulk enumerations plus21 native association admission calls. Small/empty
stores use fewer samples. Per-table finite bounds are8192 rule/filter rows,
16 profiles and128 global settings; maximum canonical depth90 and existing
14680064 output bytes. Unreadable families, duplicates, missing/foreign identity
sets, association mismatch/drift, excessive counts/depth/output fail the whole
capture. Nothing continues after a partial/nonpass snapshot.

## Authored tests and validation status

The fixture executes the actual production child script with only fake
NetSecurity cmdlets. Cases cover all seven foreign filter properties and
unknown nested values; rule/profile/global settings changes; reversed complete
enumeration order; identical31-call count for3 versus30 rules; each individual
provider-family failure; duplicate rules/filters; missing/foreign identity;
wrong native association and actual association metadata drift; null identity;
entity/byte bounds and empty complete stores. Output is only a closed PASS
summary with runtime_mutations0 and live_capability_claimfalse. No production
mock flag or effect callback is added.

Author performed Python AST parsing and `git diff --check` only after source
implementation. No tests, product imports, commits, quality commands or effects
were run by the author. The earlier read-only provider probes are observations,
not execution of this new production snapshot. Root must independently review
exact bytes, run designated PC typecheck/focused/all seven gates, then admit a
separate one-shot actual full read-only Snapshot. Full Windows prestate and
quiescence remain blocked until that actual snapshot passes.

Frozen candidate SHA256:

- controller: `5da2f409d64937cd5dc3b957fb272fe10db01e1cbc64493f4b9fdf895ff357a6`
- PowerShell fixture: `f038368f6846a4163f2374e4de0513b45beee52e5f97475e8be52ebabc46d0d2`
- Python fixture executor: `5820f9dfc9729f63943c1f49c167b08464cbd7a9e75b9ecfa294f9cc6acd54d2`

## R1 designated PC nonpass and fixture-only correction

Root ran Windows parser checks (0 errors) and PC typecheck (919 files, PASS;
log SHA256 `8cf91ee86a297cd5a762f085c2e39915f95965b3fea7c58e9931a0fa6f9978f1`).
Focused checks ran three tests: the two pre-existing controller tests passed;
the new firewall fixture failed with FIREWALL_IDENTITY_AMBIGUOUS. Full quality
was NOT_RUN. This is preserved as a nonpass, not production acceptance.

The mock `Ordered` helper had returned an entire array as one pipeline object.
Production correctly rejected that nested array's missing identity. Genuine
NetSecurity cmdlets emit individual CimInstances. The correction removes only
the fixture's unary comma, restoring genuine command enumeration; no payload,
assertion, expected refusal or production identity guard is changed.

Superseding PowerShell fixture SHA256:
`3aee32a1ac435140fea443e83f8d50d14380b69e784f2b1587a69ad2f0303867`.
Controller5da2f409 and Python executor5820f9df remain byte-identical.
Author ran diff whitespace inspection only, no tests or host effects. Root must
run fresh designated PC checks. A separate bounded actual read-only getter
repeat (twice, raw data only in RAM) is being prepared but may run only after
Root reports the corrected unit fixture PASS. Actual complete CIM serialization
and stable digest/performance remain unqualified pending that separate phase.

## R2 designated checks and mandatory R3 UTF8 boundary

Root reported R2 Windows parser0 and typecheck919 PASS, log SHA256
`060c677ca0c4c88440e58bf2ffcb538660374e1b1a0f5c78d7d02a8596b11fa0`;
focused3 PASS in15.425s, log SHA256
`a07b93d57fb2c549720888e12ce7ceac1caa26148e7601370a1533598fce6948`.
Full R2 was running when R3 was authorized; no final full outcome is claimed
in this author handoff. Those checks qualify the R2 fixture correction, not the
following source/transport correction.

Root independently authorized the mandatory one-line production UTF8 boundary.
The actual getter now sets Console.OutputEncoding to UTF8 without BOM and with
throwing encoder fallback. This prevents Windows codepage-dependent loss of
complete foreign Unicode rule/filter properties. No identity, association,
comparison, process timeout or byte/entity bound is relaxed.

An additional genuine PowerShell child fixture runs the exact getter with fake
NetSecurity metadata containing umlaut, snowman and CJK codepoints. After the
actual getter sets the process Console encoding, a direct Unicode marker is
written to Console (independent of JSON escaping), followed by its complete JSON.
Python captures actual child stdout bytes, strictly decodes UTF8 and verifies
both marker and nested foreign-property codepoints, absence of replacement
characters and no stderr. This is test-only fixture transport, not a production
mock flag or actual host/firewall capability claim.

Superseding frozen R3 candidate SHA256:

- controller: `8bd4bb15064436b41dee6ec040f87f5f6d0830d715c6dcfe08b467843140f027`
- PowerShell fixture: `cbfb85ba29372c9a2c5703d41460bdfe91507b1a513c40291a64b882d042ea7c`
- Python fixture executor: `83094b27eacf1d33b5ee04bb7b75bfe438e081baec8d9d9ac00380a0fba0cddb`

Root must run fresh R3 designated checks. Author performed Python AST and diff
whitespace inspection only; no new tests, imports, host commands or effects.

## Separate actual getter repeat — authored, NOT_RUN

The task-owned `/tmp/epic440-firewall-getter-repeat-r3.ps1` diagnostic (SHA256
`6761b6c6aabfc391db211e9c01842679a4062dcb61f39aa3b3a2d808b12e8442`)
and own300s PID/StartTime watchdog (SHA256
`7159b8fd1b488b901175254a3ece8ffaeefe055d242e5c7935c57292c9ecbdf3`)
are authored, not executed. It stages the candidate as a separate task-owned
file, verifies exact8bd4 controller bytes and unchanged DF30 source/Preparation
pins/actor ownership/full clean identity before and after, and calls only the
pure getter. It uses the unchanged DF30 Invoke-PreparationProcess twice with
its actual120s child bound;14MiB output policy remains. No maintenance factory
or effect is invoked by this proof.

The original adapter exposes already-decoded strings, not raw stream bytes.
The diagnostic states raw_stream_bytes_proven=false, strictly UTF8 re-encodes
those strings and conservatively refuses every U+FFFD/unpaired encoding. Counts
and hashes are explicitly labelled decoded_utf8_reencoded or production string
digests. It never falsely claims decoded strings are the original raw bytes.
Only complete parsed schema/counts/family hashes and equal complete production
string digests from both successful invocations can produce GETTER_REPEAT_STABLE.
Any first failed capture stops; a second failed/unequal capture remains nonpass.
Raw provider values and stdout/stderr stay only in RAM. This separate read-only
phase may run once only after Root reports corrected R3 unit PASS. It is not
Windows prestate, guest quiescence, maintenance, commit or qualification authority.


## R3 mocked acceptance, actual nonpasses and measured cause

Root reported R2 all-seven quality PASS:3416 discovery tests/36 skipped,
223.297s, full log SHA256
`5f9230bf03ae15925ba40ea66a1b84c50d504238dafa9221a97180f7028d4279`.
Root then reported R3 type919 and focused4 PASS in18.422s and all-seven quality
PASS:3417 discovery/36 skipped,223.708s, full log SHA256
`7998bcab42ec9adb8f430de266523248c55494ddef18b84065674a9ad10effa4`.
These were generic mocked/Unicode-transport acceptance; they did not qualify
full native CIM reflection. Actual R3 stopped at candidate-file ownership before
any getter. Root corrected ownership only on distinct new task uploads and
retained that failure, leaving original source/ACL unchanged.

Actual R4 first getter then timed out in120032ms, exit124 PROCESS_TIMEOUT,
stdout0/stderr7 (fixed timeout); source verified before/after. No second getter,
no effect. Private artifact SHA256
`f19978bc6a1dbebf2507c5c1da1a154d359cc5da482066b8e47da616a600e078`.

Root authorized one bounded read-only phase-cost diagnostic, retaining only
counts/timings/fixed categories. It used the same actual31 read queries, source
pins/actor/full clean verification before/after, a finite original one-rule
sample and a typed configuration-data prototype in RAM. Private artifact SHA256
`36367b5151691efcdc7ffe00f3d587942a9b36d890dcef34eb55d1a4b1147af6`.
Observed:543 rules in1193ms,3 profiles34ms,1 global setting20736ms, each full
filter family82–128ms; each of21 supported association reads17–56ms. One exact
original Canonical body plus observation guard visited1603 nodes/depth10 for
one genuine rule in614ms. This is a measured sample, not a claim that every
other row has identical cost. It explains why recursively reflecting provider
class graphs per entity is unsuitable; Rows also erased native type with
Select-Object before reflection.

The prototype retained all4348 CIM instances (543*8+3+1),99453 native data and
111408 adapted data properties, replacing13044 SDK wrappers. Full typed
projection took68783ms and serialized twice in1266ms to9153252 bytes with equal
strings. It deliberately had duplicated native/adapted values and per-leaf
observation overhead and was NOT the final implementation. Its size/runtime
cannot be multiplied into a supported maintenance/fixture budget: repeated
snapshots must still fit unchanged64MiB parent output and applicable240/300s
fixture limits. No timeout/output budget is raised by this change.

## Superseding current contract — shared typed asset, DTO2

Root expressly authorized the shared parameterless static asset
`tools/windows/qualification/windows_firewall_snapshot.ps1`, the typed DTO2
configuration projection and source binding. It is9754 bytes, strict UTF8 without
BOM, with no imports, sourcing, arbitrary arguments or effects. The controller
getter reads only that fixed sibling path using a bounded65537-byte FileStream,
refuses nonregular/reparse/BOM/NUL/overbound sources, checks its exact hardcoded
SHA256 and strictly decodes UTF8. The existing actual child command still has
120s/14680064-byte bounds. Preparation source proof now includes exactly this
additional repository-relative asset; its native UNC/drive source fixture copies
exactly that additional file. No other preparation policy is changed.

Root owns the operative normative and GO amendment. The listener fixture
consumer (separate agent/lock) gains required windows_snapshot_sha256 on both
hosts and binds this exact fixed source in its GO/intent/source pins; old GO
cannot qualify the new source. This author does not edit the listener fixture.
A trusted full-query-to-certificate wrapper is being handled separately by
Root/consumer: no cached or sampled data. Root must qualify all repeated-query
runtime and total-byte budgets before any WSL pause.

The current Canonical passes the original CimInstance, never Select-Object.
It retains EVERY native data property name, CimType, Flags when available and
Value. It retains every adapted/alias DATA property as either an exact-value
reference or complete typed override. Only the three actual SDK Property
wrappers CimClass/CimInstanceProperties/CimSystemProperties are replaced with
finite class/namespace/server/path identity and explicit data tables; the SDK
class-definition/method/object graph is not firewall configuration. Native data
with a colliding metadata name is retained in its separate native table.
Nonframework alias/note properties are preserved even if named like a wrapper;
an actual SDK framework object exposed as configuration data is a named
unsupported blocker, never silently omitted or recursively traversed.

Fast scalar/primitive-array handling avoids per-leaf recursive functions. A
same-name adapted Property value is elided only after equal exact CLR types and
actual scalar equality or primitive-array structural equality. Its name is
explicitly recorded in adapted_equivalent. A real PSAliasProperty is represented
as alias_links only after the same exact-value proof against its actual
ReferencedMemberName. All unresolved alias targets and differing values remain
in adapted_overrides, with member type, CLR type, alias target and value. Enum
views record exact enum CLR type/name only after lossless conversion equality
to the retained native value. No value is dropped because it looks similar.

Compact typed tuples remove redundant field labels/values while preserving
meaning. There is no general compression/parser engine, data sampling,
configuration-field allowlist or foreign-rule filtering. Before JSON, native,
adapted, generic dictionary and generic object property maps reject exact or
case-insensitive collisions with FIREWALL_PROPERTY_AMBIGUOUS. Envelope keys are
static unique. Consumers may trust this fixed source/serializer invariant;
PowerShell5 ConvertFrom-Json is not claimed to detect lost duplicate keys.

DTO2 root exact fields: schema_version=2,store=ActiveStore,
association_model=PROVIDER_IDENTITY_ONE_TO_ONE,rules,profiles,settings,filters,
cim_layout. filters has exactly address/application/interface/interface_type/
port/security/service. Each Row is {identity:string,value:Canonical}; rules and
filters use actual native InstanceID, profiles actual Name, settings the full
canonical row string rather than a guessed settings key. All row arrays are
sorted and unique; each filter identity set equals the complete rule set under
the explicitly admitted provider model and supported association guards.

Native Canonical exact fields: provider_identity[4],native_properties map,
adapted_equivalent names,alias_links map,enum_views map,adapted_overrides map.
Layouts: provider_identity=[class_name,namespace,server,path]; native_property=
[cim_type,flags,value]; adapted_override=[member_type,clr_type,alias_target,value];
enum_view=[clr_type,name]. cim_layout also declares equivalent_rule as
same-name exact CLR type/value and alias_rule as native referenced-member exact
CLR type/value. Generic non-CIM fixture values retain full canonical properties.
Count/depth/byte/timeout limits and complete native association guards remain.

## Superseding tests and frozen handoff status

Existing generic coverage follows Row.value without weakening assertions.
New in-memory genuine Microsoft CimInstance SDK fixtures cover provider identity,
all native type/flags/values, null versus empty arrays, array order, exact-value
reference, actual alias identity with same value but changed target, flags-only
changes, foreign changes in every family, adapted-only change, provider-class
change, reserved-name separation and unreadable DATA refusal. No actual provider
query is used by those tests. Generic case-collision tests refuse overwritten
JSON keys. The Unicode raw-byte child fixture still proves the selected
transport. A separate disposable-source fixture proves exact fixed asset bytes,
SHA tampering/BOM/empty/overbound refusal; original source is never modified.

Author performed Python AST parsing of both changed Python tests and
`git diff --check` only after this implementation. No new tests, product imports,
host queries/effects or commits were executed for this frozen typed candidate.
The prior authorized read-only diagnostic is historical evidence, not a test
or actual acceptance of the optimized candidate. Root must independently review,
run nearest parser/type/focused/all-seven checks, and then a separately gated
actual complete getter repeat. Actual optimized size/stability/runtime and
whole maintenance/fixture budget remain UNKNOWN until those checks. No live
readiness, prestate, stop/pause, restart or maintenance authority is claimed.

Final seven-file candidate SHA256 (supersedes all earlier source pins above):

- shared asset: `7f06807a54bce7b447d0da6eaf9c4a77b5cc53c865a525b46dea6b425d554e2b`
- controller: `5b3bcba5be947312aecd9da92fedc0f937e38b90e43b2ca376d4cc5012506907`
- Preparation Adapters: `b2d6f32414c47d5e629eb278cf4e5128a0954a58dcb7de6d0e6224d054a6fcff`
- PowerShell fixture: `1dccce2fa217cc11efc4310e87f015aa982338c8041c6a03349682e9910edd84`
- Python fixture executor: `18f81ddb70286dc4c6e81093c44be1c896fb49f7d9dfa5089116ba9c6474fc2d`
- native-source copy fixture: `4350381c7d5c76309a61f16bfe397bc37f797e9738eb84491ca99c102490b07f`

Primary typed SDK definitions (configuration data versus provider object graph):

- https://learn.microsoft.com/en-us/dotnet/api/microsoft.management.infrastructure.ciminstance?view=powershellsdk-7.4.0
- https://learn.microsoft.com/en-us/dotnet/api/microsoft.management.infrastructure.cimproperty?view=powershellsdk-7.4.0
- https://learn.microsoft.com/en-us/dotnet/api/microsoft.management.infrastructure.cimsystemproperties?view=powershellsdk-7.4.0

## Typed R4 PC nonpass and delegated fake-only diagnosis

Root ran four PowerShell parser checks (0 errors) and typecheck919 PASS, log
SHA256 `268dc9ff9b37a42620a82078ebe6aa1fc3c754d37a12f6cfeb0f83fb65b24a34`.
Focused17 in49.254s failed (one failure, three errors), log SHA256
`a93e557f7fc8d6cb5828c4da22111d797ed67c614bd00a58f88cd36c40cfe77c`.
Full quality was NOT_RUN. The failure and frozen candidate were preserved.
Some Python text-mode UTF8 decoding errors hid the original German OEM failure;
this is not a UTF8 transport PASS or reason to relax the Unicode assertions.

Root explicitly delegated only PC/WSL fake-fixture diagnosis, source correction
once the actual cause was known, and no real firewall/guest/service/quality
execution. Four modes of the exact frozen PC R4 fake fixture were captured as
bytes. All failed at setup Add-Type -AssemblyName Microsoft.Management.Infrastructure:
ASSEMBLY_NOT_FOUND, before any getter. Private fake diagnostic SHA256
`9b29f77680dbc4f144068bb430669a21b45cc6eb6740297436f10079d2cef116`.
Raw source pins on the frozen PC R4 checkout were verified before/after and
never modified. OEM decoding was used only on synthetic fixture errors.

A distinct task-owned fixture copy loaded the SDK through the installed fixed
System32 CimCmdlets manifest (definitions only, no provider command). Generic35
cases, Unicode marker/DTO and source-guard5 cases then passed. The genuine
in-memory CIM mode reached its last assertion and exposed a real producer bug:
a throwing PSScriptProperty getter was silently read as null through PowerShell
property access. Its unreadable-data assertion correctly failed. Private
fake-only diagnosis SHA256
`f17c404b000a22b9f1c9623c9de93425af1a1fe42cea6eb2fb3bbf1d080b5b65`.
No assertion or guard was weakened.

## Current correction — strict CLR value access, same DTO2

The producer now caches four fixed open-instance CLR getter delegates for
PSMemberInfo.Value and CimProperty.Value/CimType/Flags (Flags when available).
These are finite SDK accessor methods, not class-definition traversal, arbitrary
reflection or per-leaf PowerShell recursion. Their Invoke methods propagate
getter exceptions instead of PowerShell silently substituting null. All failed
DATA reads become the fixed FIREWALL_DATA_UNREADABLE blocker; actual null values
remain represented as null. No property is skipped, budget enlarged or DTO
layout changed. Controller hard SHA follows the new shared asset.

The fixture uses the shipped System32 CimCmdlets manifest solely to load the
actual SDK. Python wrappers capture bytes, require strict UTF8 success stdout
and empty stderr, and display byte-safe escaped failure details rather than
raising an unrelated UnicodeDecodeError. The actual Unicode child marker and
nested property assertions remain strict and meaningful; stdout encoding is
still set only by the actual getter, not preconfigured by the fixture.

Root's delegated fake-only diagnosis then used distinct new task-owned source
copies, leaving original DF30 and the frozen PC R4 checkout untouched. All four
actual Windows PowerShell modes passed: generic35 cases, genuine in-memory
CIM24 cases (including unreadable-data refusal), source-guard5 cases, and exact
Unicode marker/full DTO2; all child stderr0. Private artifact SHA256
`96c15dba366aef507136970dc8d9ec986adfca318505afffcb7673bb622183a0`.
After-copy SHA verification of the exact three task files matched the final
source bytes, artifact SHA256
`b9a7ad86370a208de0c69cc2700984235847769d9648611dee7f5e0e433a0d89`.
These were explicit fake/source-scratch tests on the approved PC/WSL runtime,
not any actual firewall provider query, full gate or live getter qualification.
No original source/ACL, service, guest, resources, proxy or hosts were changed.

The SDK getter exception contract is also documented in the primary PowerShell
implementation (supplemental source reference, not a Windows5 version claim):
https://raw.githubusercontent.com/PowerShell/PowerShell/v7.4.0/src/System.Management.Automation/engine/MshMemberInfo.cs
Actual Windows PowerShell behavior above is the decisive evidence.

Superseding seven-file frozen correction SHA256:

- shared asset: `c6cda38ff012ff3d688d529f2f92087977d42a297ce34e03190774d9991943fe`
- controller: `e08f19e56cf2a11b16a4b951d71fd117f584ae2cfc09547625fab294092e4431`
- Preparation Adapters: `b2d6f32414c47d5e629eb278cf4e5128a0954a58dcb7de6d0e6224d054a6fcff`
- PowerShell fixture: `e733c80a6bf6d4215913ad7a19b6cb6e2a6e7e0b1074101d241f3a1eaf86ad0d`
- Python fixture executor: `0fa040b9357bd3466b8e22fce16de21f90307df8e9f20285f712dbe84b53b640`
- native-source copy fixture: `4350381c7d5c76309a61f16bfe397bc37f797e9738eb84491ca99c102490b07f`

Shared asset is11222 bytes, no BOM, within unchanged64KiB source bound. Root
must independently review these corrections, run fresh nearest/type/all-seven
gates, update consumer/GO pins to this exact new asset, then separately admit an
actual complete getter repeat. Actual optimized output size, genuine full-query
stability/runtime and whole maintenance/fixture budgets remain UNKNOWN.
No actual live getter, maintenance, guest stop, commit or release is claimed.

## Release membership correction after Root PC quality observation

Root's complete quality run reported the release ASSETS/source-list membership
mismatch. The builder's fixed ASSETS now includes the exact shared firewall
snapshot asset already required by Adapters SourceList. No assertion or release
verification policy was changed. The previous seven frozen assets remain intact
except this appended evidence; the builder is the eighth source path. No tests or
host actions were performed for this source correction. Actual c6cd getter R6
failed FIREWALL_DATA_UNREADABLE in18.142s with source verified before/after; no
canonical field is omitted and no successful preservation claim is made. A distinct
source-bound read-only diagnostic is required before any producer correction.

## Root-approved exact DynamicTarget conversion descriptor (record before source)

Actual schema observation c70b5eecda25bc59d646bed0325d20ce55f6dbcce0a82bba97197e20879da47b
proved MSFT_NetProtocolPortFilter/PSScriptProperty DynamicTarget fails only in its
derived conversion, while native DynamicTransport is fully captured UInt32,
System.UInt32, flags33554436. Getter-source SHA is
4c13885350db45b07859f387cee1006382074f4271efead21fab12426b2c5bf6;
the exact four-class exception chain is MethodInvocationException,
GetValueInvocationException, RuntimeException, PSInvalidCastException under
System.Management.Automation. No ordinal/value/error message was exported.

Root approved an exact source-bound mapping DynamicTarget→DynamicTransport (NOT
same-name). Only this class/member/getter/native-type/flags/exception-chain case
may retain an explicit versioned adapter-conversion-error descriptor; all native
values/types/flags and other adapted values remain fully preserved. No converted
value is fabricated. Other unreadable/native/generic getters remain fatal. Existing
DTOv2 root/layout/four-slot override shape stays unchanged; value slot carries
explicit descriptor and clr_type=null denotes no converted CLR value. Complete
Canonical payload is still hashed; new shared asset SHA invalidates old GO/pins.

Primary contracts checked: Microsoft MSFT_NetProtocolPortFilter native schema
https://learn.microsoft.com/en-us/windows/win32/fwp/wmi/wfascimprov/msft-netprotocolportfilter
and public DynamicTarget/DynamicTransport[] cmdlet surface
https://learn.microsoft.com/en-us/powershell/module/netsecurity/get-netfirewallportfilter?view=windowsserver2025-ps.
Implementation and real offline SDK/type-definition regressions follow this entry.
No new source candidate PC gates or actual repeat have run; limits unchanged.

### Conversion candidate handoff (source frozen; PC and actual repeat NOT_RUN)

The exact narrow helper now implements the above Root-approved descriptor. The
controller hardpins the new complete shared asset. The offline SDK contract imports
NetSecurity type definitions without querying providers, binds the actual installed
DynamicTarget GetterScript hash, and uses genuine synthetic CimInstance/CimProperty
objects. It preserves an unknown synthetic UInt32 backing value and its flags,
asserts the explicit descriptor and stable complete hash, and detects backing-value
changes. Wrong class/name/native type/getter/flags/exception chain still refuse.
Direct exact-helper checks use the real getter ErrorRecord for missing backing,
wrong member kind and same-name collision; missing data is not falsely assumed to
throw from the actual getter. Existing generic unreadable DATA denial remains.

No local or host tests were executed for this candidate; Python AST and diff check
only. Real Windows parsing, nearest PC tests and all seven quality gates are
pending Root execution. Genuine full getter repeat remains pending and is required
after those gates; schema-only diagnostics are not preservation success. All earlier
failed getter results remain retained; no source or live result is overwritten.

## R8 SDK type-data interop correction and proven alias extension

R8 PC parsing/typecheck passed; focused20 failed only because the installed SDK
type data already owns DynamicTarget (CannotRemoveTypeDataMember). Full gate was
NOT_RUN. Root delegated bounded fake-only Windows SDK diagnosis with all8 frozen
R8 source hashes verified before/after, no provider queries, and separate task
fixtures/results. The corrected fixture reuses the real installed typed property;
negative getters receive unique process-local type names removed in finally,
without changing the installed type definition. Only the investigated port object
is genuine typed CIM; unrelated rule/profile objects keep the existing POCO model
so importing NetSecurity does not accidentally activate unrelated missing getters.
The synthetic native port fields are complete, and public IsValueModified=false
models read-state NotModified flags (33554432|Property4); CimProperty.Create alone
marks a new property modified and returns flags4. Production flags guard unchanged.
Microsoft SDK semantics: https://learn.microsoft.com/en-us/dotnet/api/microsoft.management.infrastructure.cimflags
and https://raw.githubusercontent.com/PowerShell/MMI/master/src/Microsoft.Management.Infrastructure/Internal/Data/CimPropertyOfInstance.cs.

This genuine SDK test exposed an additional production path after DynamicTarget
was handled: native type data also exposes DynamicTransport AliasProperty pointing
to DynamicTarget, invoking the exact same failing converted view. Pure installed
type-definition observation (no provider calls) proved the alias reference and
exact target getterSHA4c138...; private artifact
f9826a6bb6b5b8b2e0beb67f43f08d921dc69cad7080b497a75b0c9368a505df.
Root explicitly approved the narrow alias extension before these source edits.
Only exact MSFTport/DynamicTransport AliasProperty/ReferencedMemberName DynamicTarget,
known target PSScriptProperty getterSHA, complete nativeUInt32/flags33554436 and
exact4-chain may carry an alias conversion-error descriptor. Existing override
slot2 retains DynamicTarget, memberCLR is PSAliasProperty; no converted value is
fabricated. Unknown aliases and every other data failure remain fatal. Earlier
failed fake-diagnostic artifacts are retained; none is a successful live getter.

### Final SDK interop correction verification and refreeze

Delegated fake-only SDK interop r8 on the approved Windows runtime passed all21
cases using the exact candidate asseta6a5aee14f32ada47cd14b58f59372fc0ba21ceaef64401d93b94822932c19e5
from a new task-only file. All8 immutable R8 source pins and both task hashes were
verified before/after. Result5436abd0d7bdaa4c9a9b8345c18227f9033238e95dcec73c2a400d260de13baa
reports exit0, genuine in-memory CIM, installed actual getter-source bound,
provider_queries=false/runtime_mutations=0/live_capability_claim=false.
The module-definition-only alias proof was independently retained. Earlier fake
r1–r7 diagnostics are preserved including failures; they are not quality passes.

The final test fixture reuses installed DynamicTarget rather than overwrites it;
uses unique per-object process type definitions only for negative getter cases
and removes those definitions in finally; models full native port fields and
SDK provider-read modification flags through public API. It verifies both explicit
script/alias descriptors, complete backing data/type/flags and hash changes, plus
all previously approved drift/error denials. The actual producer has no test flag
or synthetic exception hook. Python/PowerShell source checks still require Root's
full parsing/typecheck/nearest/all-seven gate execution on these exact bytes.
No genuine getter repeat or live effect ran for this candidate.
