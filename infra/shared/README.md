# Shared Infrastructure Boundary

This directory marks the target home for reusable infrastructure helpers.

Current shared assets remain in their existing locations for compatibility:

- `infra/utils.sh`
- shared shell helpers that are not specific to platform, artifacts, or
  deployment

Do not move shared helpers into this directory without a dedicated migration
slice and compatibility handling.
