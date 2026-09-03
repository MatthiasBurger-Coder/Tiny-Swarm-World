# Stale Reference Search: #284 / CRED-06

The user-facing documentation and `.env.example` were searched for removed
credential-mode flags, generated/fixed/bootstrap credential-file paths, and
manual-password preparation instructions.

Remaining recovery wording is limited to explicit negative statements (the
normal path does not create recovery files) or unrelated operational/TLS
recovery. It is not an instruction to create deleted credential state.

The canonical catalog remains the authoritative location for the disposable
internal-test convention. User-facing guidance links to it for password
values and component derivations; the installer output and `.env.example` do
not duplicate raw credential values. Architecture text may name the contract
without becoming a second source of truth.
