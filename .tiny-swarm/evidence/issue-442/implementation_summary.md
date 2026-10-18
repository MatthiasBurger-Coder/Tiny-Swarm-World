# Implementation summary — #442

Added canonical strict logical lifecycle schemas, native-asset-projected version
catalog and installation-instance state behind application ports. This is the
W02 incremental #318 shared model, not a competing logical schema or engine.
Catalog policy keeps Classic foundations and explicit native bundle identities;
existing artifact/deployment/preflight/native packaging authorities stay intact.

Repository uses private same-directory writes, fsync, atomic replace, directory
fsync, advisory writer lock and compare-and-replace token. Read-only operations
never adopt or migrate. Invalid and unadmitted schemas are preserved and blocked.
Explicit application adoption previews, validates complete inventory and requires
local approval; conflicting identity/incomplete/interrupted legacy state is refused.
No operator mutating adoption CLI is introduced; legacy operators receive the
supported actionable blocked path documented in installation-manifest.md.

`product version` and `services list` inspect manifest/catalog before logger,
executable-path setup or runtime services. Desired/observed versions and digest
mismatches/unknowns remain explicit; inspections never assert convergence.

Thirty new deterministic tests cover schema, corrupt/unknown/duplicate input,
atomicity/interruption/CAS/no-op/config preservation, native catalog drift,
adoption approval/ambiguity and read-only CLI/help/flag failures. Existing local
gates preserve #297 and live-consent compatibility. README and contracts explain
ownership, migration/adoption recovery and downstream W03–W09 limits.
