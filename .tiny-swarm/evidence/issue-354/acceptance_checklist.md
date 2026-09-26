# Acceptance checklist

- [x] Production execution centralized in three owned process modules.
- [x] Application services do not invoke subprocess; architecture guard enforces it.
- [x] Results and failures explicitly represented with preserved capability mappings.
- [x] Sensitive payloads omitted from runner diagnostics and LXC gateway logs.
- [x] Success, timeout, nonzero exit, missing executable, cancellation and exit races tested.
- [x] Final-candidate full local quality evidence complete: PASS, 2179 tests, 18 skipped.
- [x] Independent completion audit PASS: audit.md.
