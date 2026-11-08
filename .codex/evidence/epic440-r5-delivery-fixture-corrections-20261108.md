# Integrated R5 focused delivery fixture corrections

Root authorized only the two affected test fixtures and this record. Input is
R4 86-pin manifest b03594371dd9c7f644b1d0340b3d53fc4dd74f889211077c41f9748637e20039.
All unaffected input pins were compared byte-for-byte before this correction.
Production source and every admission guard remain unchanged.

Root's actual PC run: typecheck PASS963 source files; focused179 tests in35.290s
had one failure and two errors, log SHA256
ca743009520c467fac6c829c0e166f46380a190e5c3faf91b1eee2cb8a56cb84.
The full R4 gate was not run. These failures remain evidence, not passes.

The public profile observation fixture retained the domain-only manifest helper,
which intentionally has only an Incus component. It cannot pass NativeCatalog
validation for an actual Incus+Portainer installation. The fixture now fills its
complete selected component inventory from the real copied native catalog and
calls actual validate_manifest before saving; no validator is replaced.

The Swarm-only completion fixture selected published Swagger but its operation
helper reused the minimal template's10001-only profile binding. The actual desired
route guard correctly refused. The helper now derives routes from the canonical
SetupManifest and exact SelectionPlan exposure, with its original loopback listen
scope. Planned modes were already constructed before the original intent; they
are not rewritten during recovery.

The public creation-completion recovery test's remaining BLOCKED result cannot
be uniquely attributed from the available top-level failure. Its success
assertion now includes the actual sanitized reason/message and bounded transport
effect/readback event trace. This is diagnostic coverage, not a claim that the
third failure has been resolved. Root should run the corrected focused cases on
PC and inspect that precise remaining guard cause before any production change.
No admission/readback/task proof is mocked away to force success.

Author validation: AST parse of both changed Python tests, original pin retention,
and diff whitespace inspection only. No tests, runtime imports, hosts or commits.

## R6: actual operator input and honest temporary repository markers

Root ran the nearest eight PC tests in6.082s on R5: one failure and one error,
log SHA2563a3fbc9f2b10d190adacce4a0b5404d221883f80420c70ae8509cff15d041886.
Typecheck and full quality were NOT_RUN. The improved failure assertion identified
the real public-preparation refusal: Required operator secret is missing:
TSW_PORTAINER_ADMIN_PASSWORD. The test now supplies its existing in-memory
RAM_VALUE through the scoped actual operator environment for the whole public
preparation. The later composition function mock is removed; ordinary input
validation and lookup remain real. No credential file/value is persisted.

The remaining public observation error came from the real repository-root
classifier. The temporary root had infra/state but lacked AGENTS.md, QUALITY.md
and the package path. It now copies those two actual source documents and the
actual tiny_swarm_world/__init__.py into its minimal package directory. The
state-path classifier and NativeCatalog remain unchanged and unmocked.

Only these two test fixtures and this record changed from the R5 pin tuple.
All other pins were retained. Author AST/diff inspection only; no tests, hosts,
production edits or commits. R6 execution and acceptance remain Root's gates.
