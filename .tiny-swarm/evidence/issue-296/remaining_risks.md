# CRED-09 limits

Supported Jenkins startup consumer only. No generic rotation API, unsupported
external-provider mode, password-only/global session revocation or power-loss
claim. Matching-input history retains its original candidates. Protected
migration/source-volume keepers remain operator-owned; no secret values or
credential-derived hashes enter this wrapper. Current-scope applicability is
[explicit](../issue-302/credential-applicability.json).
