# Installer Console Output

`./install.sh` delegates to `python3 -m tiny_swarm_world.simple_installer`. The
installer prints human-readable progress and diagnostics while it writes logs
and evidence to local evidence directories.

Example:

```text
Tiny Swarm World Installer
  RUNNING Mode: fresh-reset; Profile: service-access; Provider: lxc_native
[1/2] fresh-install reset
  RUNNING fresh-install reset started
  OK      fresh-install reset completed
[2/2] live setup
  RUNNING live setup started
[setup] preflight                 START
[setup] preflight                 PASSED
[setup] platform init             START
[setup] platform init             COMPLETED
[setup] platform reconcile        START
[setup] platform reconcile        COMPLETED
[setup] platform expose           START
[setup] platform expose           COMPLETED
[setup] deployment bootstrap      START
[setup] deployment bootstrap      COMPLETED
[setup] artifacts prepare         START
[setup] artifacts prepare         COMPLETED
[setup] artifacts verify          START
[setup] artifacts verify          COMPLETED
[setup] deployment apply          START
```

The completed setup summary remains line-based and includes the workflow,
phase count, status counts, phase-group status/limit/duration, each phase
status, final status, and available evidence paths. Reset, deployment, and
verification commands use the same readable workflow/status pattern.

After a successful run the installer prints the Portainer and Infisical URLs,
the applicable login identifiers, and the `INTERNAL/TEST ONLY` catalog
convention. It deliberately does not print password values or derived secret
material. Read the canonical catalog for disposable defaults, or read a
protected operator override privately when one was supplied.

The default channel is human-readable on native Linux, WSL2, and the
LXC-native setup path. On failure, a structured block in a captured log is
represented by an omission marker; the full log path is printed so the details
remain available in evidence. Recovery hints and suggested checks remain in
the console.

Failure diagnostics include the failed phase, reason, evidence path, and
suggested commands when available. Suggested commands are printed for operator
use; the reporter does not execute them.

Setup phase progress is emitted as left-aligned text lines. It must remain
readable in copied terminal logs and CI output, without cursor-positioned drift
or truncated fragments such as partial phase names.

Console output must not contain raw JSON, raw Python dictionaries, YAML payloads,
or internal event object representations. Machine-readable JSON belongs in
generated report files, not the default stdout or stderr. An operator may opt
into the structured CLI channel explicitly with `--json` or
`TSW_DEBUG_JSON=true`; `TSW_DEBUG_JSON=false` preserves the default summary.
