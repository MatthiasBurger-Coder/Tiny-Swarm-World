# Implementation Summary: #281 / CRED-03

The standard internal-test installation path now uses one credential policy:

1. an applicable secure/Vault value;
2. explicit operator input;
3. the deterministic internal-test catalog default.

The domain resolver is pure and receives opaque values from its caller. The
application service owns lifecycle resolution and transports only safe source
metadata. Bootstrap and post-bootstrap are separate phases. A self-hosted
Infisical value is rejected during bootstrap because that service is not yet
available to provide its own startup inputs. Vault synchronization is a
separate post-bootstrap step.

The simple installer combines a WSL-native operator file, explicit bootstrap
override, and process environment with process values winning over file
values. Explicit credential files require a user-owned 0600 file inside a
user-owned 0700 directory and are rejected on `/mnt/<drive>` paths or through
symlinks. The installer records only key/source labels in context and sync
evidence.

Self-hosted Infisical is constrained to a local HTTP(S) endpoint. An explicit
external provider mode is rejected with an actionable error because external
Infisical support is not part of this self-hosted RC1 slice. Existing
`generated`, `fixed`, and `infisical` paths remain isolated compatibility
surfaces and are mapped in documentation; their removal is CRED-04.
