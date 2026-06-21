# Installer Console Output

`./install.sh` delegates to `python3 -m tiny_swarm_world.installer`. The
installer prints human-readable progress and diagnostics while it writes logs
and evidence to generated local directories.

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

Failure diagnostics include the failed phase, reason, evidence path, and
suggested commands when available. Suggested commands are printed for operator
use; the reporter does not execute them.

Setup phase progress is emitted as left-aligned text lines. It must remain
readable in copied terminal logs and CI output, without cursor-positioned drift
or truncated fragments such as partial phase names.

Console output must not contain raw JSON, raw Python dictionaries, YAML payloads,
or internal event object representations. Machine-readable JSON belongs in
generated report files, not stdout or stderr.
