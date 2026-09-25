# Remaining risks — issue #352

S352-02 typed manifest is accepted. Remaining implementation is OPEN: strict parser contracts, Compose/service catalogue validation, stable provider/Compose/operator inputs, and validation before setup/reset/pre-apply mutation. See configuration-surface-inventory.md for exact source evidence. No out-of-scope edit is currently necessary. Runtime-dependent credentials must retain readiness timing.

S352-02 compatibility note for S06 operator migration documentation: supplied required fields must be YAML booleans, source must be a nonempty string, and supplied scalar fields no longer coerce lists/numbers/null to text. Malformed YAML and duplicate keys are rejected with safe diagnostics. Valid defaults, unknown source strings and YAML yes/no/merge semantics remain supported.
