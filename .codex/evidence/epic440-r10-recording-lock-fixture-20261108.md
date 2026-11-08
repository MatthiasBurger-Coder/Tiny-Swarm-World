# Integrated R10: recording composition lock retains real private journal reads

Root authorized a test-only correction after actual PC R9 discovery. Input is
96-pin R9 manifest9507ec13c2d52535618f172d591ef1f212d6b83fb86ad6d9cf915a708f536ce4.
All96 R9 source/test pins matched before edits. Production modules, source
admission/private filesystem guards and the node suite remain unchanged.

Root reports actual R9 architecture43, focused181 and type970 PASS. The full
run passed policy/complexity/lint/architecture/mypy before discovery3517 tests
in217.753s had three errors and36 skips. Retained log SHA256
eced82a95a69a1e3dc11f65d6f320cd7e7821bca6727fbd4eece880e4b7ef906.
This is not full-quality PASS.

## Actual cause and narrow seam correction

The existing unit helper use_fake_composition_locks globally replaced the
concrete adapter class as well as the public composition factories. That was
sufficient when only fake workflow leases called it. New real fresh-legacy
eligibility reads JsonProfileLifecycleJournal/JsonProfileChangeJournal; their
private reader uses the same adapter-class address for _directory(create=False).
The application-port FakeInstallationLock correctly has no such private method,
so the overly broad test patch caused AttributeError before real eligibility.

The shared test helper now uses a dedicated RecordingCompositionLock shim.
It retains the injected recording workflow lease behavior but delegates the
private directory operation to the original concrete JsonInstallationOperationLock
captured by the test module before patches. FakeInstallationLock itself is
unchanged. The delegate really opens and validates that test root's filesystem;
it does not return a fake absence or swallow any exception. Production readers,
ACL/ownership/descriptor checks and private path semantics are untouched.

A focused regression runs under the exact composition patch context, reads
actual private checkpoint bytes, then verifies unsafe directory and file modes
still refuse and the retained bytes are unchanged. This exercises the specific
mock-boundary error rather than loosening production admission or making every
checkpoint disappear. Existing node tests and callers require no edits.

Author validation is Python AST and diff whitespace inspection only, with all
unaffected R9 hashes retained. No project imports, tests, hosts or commits.
Root must run the nearest affected modules and the full required PC gate.
