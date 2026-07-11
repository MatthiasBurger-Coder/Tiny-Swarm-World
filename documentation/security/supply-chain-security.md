# Supply-Chain Security

Tiny Swarm World keeps supply-chain checks explicit and separate from the
non-mutating default quality gate. Runtime dependency ranges are declared in
`requirements.txt`; exact resolved versions and artifact hashes are committed
in `requirements.lock`.

Local audit commands are:

```bash
python3 tools/security_gate.py dependencies
python3 tools/security_gate.py sbom
python3 tools/security_gate.py container-config
```

The first two require the development tools in `requirements-dev.txt`. The
container configuration check additionally requires an explicitly installed
Trivy executable. No scanner is silently installed, no image is built or
pulled, and no external static-analysis CI is introduced by this policy.

A failed audit, missing scanner, incomplete dependency collection, or missing
image evidence is not a pass. Security exceptions require an identified
vulnerability or rule, owner, rationale, compensating control, review date, and
release-impact decision.
