# Implementation summary — issue #445

Read-only `services updates [--services <ids>]` and
`services update --services <ids> [--to <target-id>] --preview` now use the
existing lifecycle manifest/catalog ports. Domain policy validates complete
immutable bundles, explicit source transitions, Classic host/preset compatibility,
deterministic dependency order, observations, desired drift and no-op evidence.
Plans expose per-component identities, selected changes, direct dependencies and
installed dependents, availability impact, backup/migration and recovery limits.

The existing ServiceDefinition owns target/transition metadata; no second catalog
or executor was introduced. NativeComponentCatalog publishes authoritative
installation-baseline references, with zero qualified transitions. Unknown
upstream/digest metadata stays unknown; no registry/network lookup is performed.
Portainer is dedicated-upgrade-only; Incus host packages remain host-owned.
Legacy #297 platform update execution/recovery remains unchanged. W06/W07 own
execution/persistence; W09 owns actual host qualification.

Independent Requirement Lead and System Architect reviewer: PASS. The reviewer
identified a false no-op edge involving extra desired/observed upstream metadata;
the correction and mismatch/unknown regressions passed independent re-review
(14 domain/application tests). Final Tester/completion review is recorded in
completion_audit.md.

Checks use Python 3.14.4 on WSL2 Linux 6.18.33.2. Additionally, the 19 new
domain/application/CLI tests pass with Python 3.12.14 in an isolated temporary
virtual environment installed from requirements.lock with --require-hashes.
The full gate also passes on Python 3.12.14: 2,747 tests, 18 skipped.
The README governing checksum was refreshed in the existing skill registry.
No live installation/upgrade success is claimed.

README documentation also refreshes its single governing hash in the existing
registry cache; no skill inventory or routing behavior changed.
