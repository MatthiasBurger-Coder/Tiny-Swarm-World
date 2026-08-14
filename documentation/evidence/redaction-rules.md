# Live Evidence Redaction Rules

## Never record

- passwords, API keys, bearer tokens, JWTs, cookies, htpasswd entries or
  secret values;
- Swarm join tokens, SSH keys, TLS private keys, raw PEM blocks or credential
  headers;
- complete environment files, process environments or unfiltered command
  stdout/stderr;
- private host paths, usernames, private IP addresses, DNS resolver contents
  or host mutation payloads unless deliberately reduced to an approved
  redacted label;
- browser screenshots containing credentials, cookies, personal data or
  unredacted service payloads.

## Allowed summaries

- policy state, phase ID, attempt count, exit classification and timestamp;
- service name, route label, port class and redacted endpoint label;
- secret reference name and storage class, never the referenced value;
- TLS subject/SAN summary, issuer, validity, key usage, EKU and chain result,
  never certificate private material;
- HTTP status class, authentication outcome and route identity without body
  content or authorization headers;
- artifact name, immutable digest and provenance summary where no credentials
  are included;
- bounded error category, remediation, rollback and cleanup result.

## Review procedure

1. Write the redacted file before generating its checksum.
2. Search the bundle for secret-like keys, PEM markers, token patterns,
   authorization headers, raw environment assignments and private paths.
3. Reject and remove any violating file; do not checksum or publish it.
4. Generate `sha256sum` output for the accepted files and verify it before
   review.
5. Record reviewer, timestamp, decision and any rejected artifact names.

Redaction does not convert an unsuccessful or partial run into success. The
original sensitive data must remain outside the evidence bundle and should be
handled through the operator's secret-management process.
