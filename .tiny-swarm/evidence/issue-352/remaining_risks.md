# Remaining risks — issue #352

S352-01 through S352-03 are accepted. Remaining implementation is OPEN: Compose/service catalogue validation, activation of stable provider/Compose/operator inputs, and validation before setup/reset/pre-apply mutation. See configuration-surface-inventory.md for exact source evidence. S05 installer validation requires a reviewed two-file adapter/test scope amendment; user approval is pending before those writes. Runtime-dependent credentials must retain readiness timing.

S352-02 compatibility note for S06 operator migration documentation: supplied required fields must be YAML booleans, source must be a nonempty string, and supplied scalar fields no longer coerce lists/numbers/null to text. Malformed YAML and duplicate keys are rejected with safe diagnostics. Valid defaults, unknown source strings and YAML yes/no/merge semantics remain supported.

S352-03 compatibility: missing inventory/port files and null whole documents retain defaults; supplied port documents require both list collections. Supported numeric strings remain accepted for inventory/provider/command fields. Boolean-as-integer, float command indexes, non-string text fields, malformed nested metadata, duplicate keys, recursive aliases and invalid supplied collection shapes fail with sanitized diagnostics.
