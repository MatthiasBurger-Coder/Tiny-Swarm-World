# Threat Model Rules

## Required Fields

- protected asset
- actor
- entry point
- trust boundary
- threat
- mitigation
- residual risk
- owner
- verification

## Security Review Areas

- API Security
- gRPC Security
- Authentication / Authorization
- Secrets Handling
- Logging Safety
- Container Security
- Dependency / Supply Chain Risk
- Repository Processing Risk
- Runtime Trace Data Risk

## Evidence Integrity Threats

Treat evidence poisoning, fabricated traces, tampered source artifacts and untrusted generated output as security-relevant when they could alter forensic findings.

## STOP Rules

Stop when a protected asset, trust boundary, mitigation or residual risk is unknown for a security-sensitive slice.
