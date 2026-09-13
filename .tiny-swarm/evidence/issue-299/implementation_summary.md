# RC1-R03 Implementation Summary

Status: DONE for the selected planned-restart and recovery contract. Product code
is unchanged at c921e695. The canonical hosted fresh chain and cross-host update
proofs are integrated in R05/R01; this package adds actual node recovery, WSL
distribution restart and native VM reboot with full authenticated use afterward.

The first WSL restart produced an endpointless Pulsar Manager container. A full
acceptance attempt failed; it remains LIVE_PARTIAL. A container restart caused
Swarm replacement, with intermediate port-allocation errors. After repair all
preservation and 25+7 authentication checks passed. The verifier's former generic
manual_repair_performed field referred only to that read-only helper; the separate
repair-context.json explicitly records the overall manual repair. It is not an
automatic restart success or proof of the underlying Docker root cause.

A second, explicitly selected planned boundary stops node Docker/socket/containerd
before Incus shutdown and restarts only the isolated WSL distribution. Normal
startup then restores all services within the 600-second bound without a post-start
repair. Identity, configuration, persistent fixture and authenticated use pass.
The [observed runbook](../../../documentation/evidence/rc1-wsl-planned-restart-20260913.md)
is maintained separately from a general hard-power-loss guarantee.

Native shared failure and worker recovery execute the product-equivalent bedb
revision; the actual full VM reboot and authentication execute c921. The native
kernel boot ID changes. WSL changes its PID1 identity while retaining the shared
kernel boot ID. These host proofs are distinct.
