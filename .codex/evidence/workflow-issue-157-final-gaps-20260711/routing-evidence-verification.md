# Routing Evidence Verification

Status: `NOT_RUN`

Expected target:

```text
.tiny-swarm-world/evidence/solid-typed-evidence/routing/effective-access-model.json
```

Required verification:

- productive application/runtime use case;
- exact required top-level fields;
- `service_profile` and `result: generated`;
- fixed credential label/Infisical reference projection;
- no password, token, secret, private key or environment credential value;
- deterministic route/skip/list ordering;
- parent creation;
- same-directory atomic replace;
- old-target preservation and temporary-file cleanup on failure;
- deployment pre-apply integration;
- ignored target path.

Slice 02 implements the behavior. Slice 05 replaces `NOT_RUN` with exact test
and artifact evidence.
