# Stale Reference Search: #284 / CRED-06

The user-facing documentation and `.env.example` were searched for removed
credential-mode flags, generated/fixed/bootstrap credential-file paths, and
manual-password preparation instructions.

Remaining recovery wording is limited to explicit negative statements (the
normal path does not create recovery files) or unrelated operational/TLS
recovery. It is not an instruction to create deleted credential state.

The canonical catalog remains the sole location for the disposable internal-
test convention; component exceptions link back to it rather than duplicating
values in the installer output or templates.
