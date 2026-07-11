# SBOM Policy

Generate the runtime dependency SBOM from the same hashed lock used by the
dependency audit:

```bash
python3 tools/security_gate.py sbom
```

The default CycloneDX JSON output is written below ignored
`.tiny-swarm-world/evidence/security/`. The tool refuses output outside that
local-state boundary. Release evidence may record a checksum, generator
version, source commit, generation time, and review status. Publication of an
SBOM is a separate release decision; local paths, credentials, environment
values, and raw private evidence must not be added to it.
