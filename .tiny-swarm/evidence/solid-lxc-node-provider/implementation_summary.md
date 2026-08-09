# Issue #184 — Implementation Summary

Issue #184 decomposes the verified LXC node-provider mechanics into explicit
command, node, profile and resource boundaries while retaining the legacy
module as a compatibility facade for `LxcNodeProvider` and command types.

Implemented:

- moved asynchronous command result/runner transport to
  `lxc/command/node_command.py`;
- centralized LXC command argument construction in `lxc/command/args.py`;
- extracted observed-node, lookup and teardown models to `lxc/node/models.py`;
- extracted instance/device safety checks to `lxc/node/safety.py`;
- extracted profile safety/reconciliation policy to `lxc/profile/policy.py`;
- extracted resource validation, parsing, resolution and evidence to
  `lxc/resource/resolution.py`;
- preserved legacy imports and public lifecycle outcome behavior;
- updated process-spawn architecture allowlisting for the new command module;
- added focused module tests and a legacy-module architecture guard.

Typed serialized evidence builders remain the explicit #191 successor scope.
