# Container Image Scan Policy

Committed Dockerfiles and compose configuration can be checked without
building or pulling images:

```bash
python3 tools/security_gate.py container-config
```

This command requires an explicitly installed Trivy executable and fails on
HIGH or CRITICAL configuration findings. A missing executable is reported as a
missing control, not a pass.

Scanning built images is required before a release claims image readiness, but
it remains outside the default development gate because building, pulling, and
registry access can mutate external or local runtime state. Such scans require
an explicitly approved workflow, immutable image digest, scanner and database
versions, result summary, exceptions, and redacted evidence. Static source
scans must never be presented as proof that a built image is vulnerability
free.
