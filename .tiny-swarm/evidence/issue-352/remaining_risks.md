# Remaining risks — issue #352

S352-01 through S352-04 are accepted. Remaining implementation is OPEN: activation of stable provider/Compose/operator inputs and validation before setup/reset/pre-apply mutation. See configuration-surface-inventory.md for exact source evidence. S05 installer validation requires a reviewed two-file adapter/test scope amendment; user approval is pending before those writes. Runtime-dependent credentials must retain readiness timing.

S352-02 compatibility note for S06 operator migration documentation: supplied required fields must be YAML booleans, source must be a nonempty string, and supplied scalar fields no longer coerce lists/numbers/null to text. Malformed YAML and duplicate keys are rejected with safe diagnostics. Valid defaults, unknown source strings and YAML yes/no/merge semantics remain supported.

S352-03 compatibility: missing inventory/port files and null whole documents retain defaults; supplied port documents require both list collections. Supported numeric strings remain accepted for inventory/provider/command fields. Boolean-as-integer, float command indexes, non-string text fields, malformed nested metadata, duplicate keys, recursive aliases and invalid supplied collection shapes fail with sanitized diagnostics.

S352-04 compatibility: supplied service catalogues require a services mapping and boolean enabled values. Selected Compose files require valid service/deploy/image and consumed member shapes; malformed entries are rejected rather than silently omitted. Missing catalogue behavior, ordinary aliases, extensions, interpolation and supported short/long ports remain covered. Snapshot APIs exist; lifecycle activation remains S05 work.

S05 reviewed scope correction awaiting user approval: add src/tiny_swarm_world/infrastructure/adapters/repositories/installer_configuration_repository.py and tests/infrastructure/adapters/repositories/test_installer_configuration_repository.py. Architect and Requirement Lead accept this narrow boundary adapter with no ADR or import-allowlist expansion. No S05 implementation has started.
