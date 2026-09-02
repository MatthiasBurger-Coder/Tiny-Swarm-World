# Architecture Before/After: #282 / CRED-04

## Before

```text
installer CLI
  ├─ generated mode ──> generated local env ──> sync generator/recovery file
  ├─ fixed mode ──────> fixed local env ──────> sync update path
  ├─ infisical mode ──> existing vault only
  └─ internal-test ───> catalog/defaults

all profiles ──> Infisical sync construction
```

The branches duplicated source selection, persistence, validation, and
rotation behavior. Some paths also constructed provider clients before the
selected lifecycle required them.

## After

```text
operator process/file ─┐
                       ├─> centralized resolver ──> installer/setup inputs
internal-test catalog ─┘              │
                                     └─> redacted source metadata

service-access profile ──> validated local Infisical bootstrap
                         └─> post-bootstrap sync/evidence

default profile ─────────> no Infisical sync construction
```

The domain resolver owns precedence and conflict detection. The application
layer owns lifecycle orchestration. Infrastructure composition owns protected
configuration-file loading and validated client construction. The manifest
owns inventory metadata; the catalog owns deterministic values. No layer owns a
second generated credential store.
