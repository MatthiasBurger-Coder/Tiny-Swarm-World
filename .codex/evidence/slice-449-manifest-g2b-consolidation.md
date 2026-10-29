# S449-MANIFEST-G2B consolidation

Status: IMPLEMENTED AND LOCALLY VERIFIED; CHECKPOINT PENDING.

This candidate routes only `services migration-preview` through an early,
read-only manifest/catalog composition and emits a fixed sanitized policy
projection. Invalid argument combinations and unexpected failures return a
fixed BLOCKED_UNKNOWN result. The candidate does not persist or accept schema
2, adopt identity, construct runtime services, or establish host support.

Preflight at `5b40fdb5e4ac3e15d3ff4d560425c8e6d8efdb54` and planning role
reviews are recorded in `slice-449-manifest-g2b-distribution.md`. Final
independent implementation reviews and exact-source designated SSH PC WSL
verification are recorded below. No local tests or native host operations were
executed by the implementation stream.

## Revised bounded-reader candidate

The operator-local source marker is emitted on success and blocked results.
A shared preview-only reader pins a project-root descriptor, reads only the
fixed manifest and nine Compose inputs with directory/file no-follow flags,
caps reads and file count, revalidates held file/directory bindings before
output, and closes descriptors on success or failure. The preview manifest
adapter cannot save; the existing catalog supports an injected bounded
text-reader while its default remains unchanged. The selected root comes from
the existing repository-root policy only; alternate infrastructure root is
not evaluated. These checks establish neither authority nor protection
against hostile privileged actors, hardlinks or ABA.

The integration owner reports six role design GO and an S3/S3D EXECUTION_PLAN
for expanded locks at `8b6017098f949b7a119d43a248f2211288c9b74e`;
see distribution for the precise reviewed contract and overlay hashes.
Final Security, Architecture and Tester review GO and exact-source SSH PC
WSL targeted tests, Ruff and full quality were reported by the integration
owner. The detailed final source tuple is in the distribution record.

## Final verification and corrections

For the candidate based on checkpoint `c557cb8e957e23557e3ab091883de9dcddaa78de`, the
integration owner reports independent Security, Architecture and Tester GO
for the final candidate and six planning roles plus DevOps S3/S3D as recorded
in distribution. On the designated SSH PC WSL test host with Python 3.14,
exact-source focused suites ran 118 tests successfully, direct Ruff passed,
and `python3 tools/quality_gate.py quality` passed with exit 0: 3,354 tests
run, 37 skipped, 205.624 seconds. `git diff --check` passed. Python 3.12 was
not tested in this slice.

An earlier targeted run found that the package-entrypoint registry expectation
did not contain the newly declared command; the existing expected tuple was
updated at the registry position without removing legacy assertions. A later
full quality run failed the complexity gate for dispatcher, parser and catalog
growth. The scanner and early routing responsibilities were separated into
the existing preview and workflow routing modules, and Compose reading into a
catalog helper. The last dispatcher coupling finding was addressed by moving
both registered read-only early routes behind the workflow route. The final
full gate passed after these corrections; no complexity baseline was weakened.

The preview labels its fixed operator-local assets unverified. Its no-follow
FD checks do not establish trusted catalog provenance, host safety, runtime
capability support, persisted schema-2 adoption or live qualification.

## CP_RECORD

- sliceId: S449-MANIFEST-G2B
- workflowVersion: 1.55
- sliceTitle: Read-only operator-local migration preview
- responsibleRole: Senior Python Automation Developer; root integration owner
- changedFiles: the 17 code, test and user-guide files listed with SHA-256 in
  `slice-449-manifest-g2b-distribution.md`, plus that distribution and this
  consolidation record
- qualityCommands: designated SSH PC WSL targeted 118-test suites; direct Ruff
  on changed Python files; python3 tools/quality_gate.py quality; git diff --check
- qualityResult: PASS on SSH PC WSL Python 3.14; targeted 118, Ruff, full
  quality exit 0, 3,354 tests run, 37 skipped, 205.624 seconds
- rollbackReference: c557cb8e957e23557e3ab091883de9dcddaa78de
- arc42Updated: false
- adrUpdated: false
- commitSha: pending checkpoint commit
- limitations: Python 3.12 not tested; no schema-2 persistence or adoption,
  no authority/provenance claim, no host qualification or runtime support.
