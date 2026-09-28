# Acceptance checklist

- [x] Every removed path is proven unused or superseded: the private no-op group helper had one product call and is superseded by `_run_phase`; the simple-installer secret-name helper is superseded by the shared domain selector, with bootstrap handoff tests.
- [x] Canonical ownership exists before deletion: `_run_phase` owns explicit group switching; the domain configuration contract owns Traefik defaults; other candidates and owners are recorded in the audit.
- [x] No supported CLI/configuration behavior was removed: entrypoints and config keys are intact; installer, bootstrap, and final full gates passed.
- [x] Regression tests cover retained canonical paths: mocked phase command, direct installer defaults, and absent/custom/empty bootstrap handoff cases.
- [x] Remaining legacy compatibility code is documented in the ARCH-03.17 audit.

Independent completion audit: PASS; see `completion_audit.md`.
