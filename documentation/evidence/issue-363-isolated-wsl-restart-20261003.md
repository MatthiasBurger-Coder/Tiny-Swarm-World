# Issue 363: current isolated WSL distribution restart

> Historical evidence from the 2026-10-03 campaign. Intermediate or pending
> decisions below retain their original scope and are superseded for whole-issue
> completion by the [final validation report](issue-363-final-validation-20261003.md).
> Publication does not rerun or qualify the current repository revision.

The owned `TSW-RC1-Isolated` distribution passed the planned graceful restart
scenario on candidate `89357c4a1fd463bbe5ee2ae9dac074180513eace`. This is a
retained disposable installation qualified by the current canonical setup;
it is not a fresh installation or a shared-kernel reboot.

| Verification | Observed result |
| --- | --- |
| Current setup | PASS; 18 phases; 259.281 seconds |
| Baseline platform verification | PASS; 4.570 seconds |
| Baseline authenticated acceptance | PASS; 25 live tests plus 7 API checks; zero failures, errors or skips |
| Planned shutdown | Owned node Docker, socket and containerd stopped before Incus shutdown; only the selected distribution terminated |
| Automatic startup readiness | Platform verification plus all eight application-readiness tests passed within the original 600-second window; UTC elapsed 127.202 seconds, conservative elapsed 128.564 seconds |
| Post-restart authenticated acceptance | PASS; 25 live tests plus 7 API checks; zero failures, errors or skips; 99.956 seconds |
| Distribution identity | PID1 start ticks changed from 3849962 to 3929108; PID namespace changed from 4026532315 to 4026532319; shared kernel boot ID unchanged |
| Persistent identity | Three provider UUIDs and creation times, Swarm/node/service IDs and service configurations preserved |
| Actual persistent content | New Jenkins fixture job, successful build 1 and archived known-content `fixture.txt` preserved after startup and again after complete authenticated acceptance |
| Final isolation cleanup | Three owned nodes stopped with data retained; prior disabled startup/socket state restored; isolated distribution stopped; owned bridge and managed ports released |
| Unrelated host continuity | Primary Ubuntu PID1, namespace, kernel boot ID and interoperability preserved; unrelated Docker/socket/containerd and four legacy 5000/8081 listeners preserved |

The actual fixture is `tsw-issue363-isolated-restart-20261003`. Its archived
content SHA-256 is `ab8559f89c39c3bce463d214dd92efbf79d8bd129ed1f1fddd33a50bef5aecab`.
Comparisons cover job configuration, build status, artifact content, private
Jenkins configuration/secrets, job inventory, persistent home and storage node.
Private fingerprints remain outside the portable evidence; the portable
package contains comparison booleans. The Jenkins task and container were
replaced while the desired image and running image identity were preserved.

The historical interoperability unit and helper matched their retained source.
Its enabled guard kept a read-only binfmt bind in the isolated mount namespace;
primary Ubuntu interoperability survived both selected terminations. Enabled
Incus startup/socket units started the owned nodes normally after relaunch.
No service, network or data repair was performed after the tested boundary.

Three non-success observations remain explicit history. Short preparatory WSL
commands initially allowed idle distribution shutdown, resolved with an
isolated transient foreground lease. The first fixture attempt refused to
reuse an existing historical private baseline before any data mutation; the
external harness was corrected to use a new protected directory. The first
early application-readiness attempt failed after 54.020 seconds; a later attempt
passed all eight tests without repair or extending the original startup deadline.
These observations are not reclassified as successful attempts.

Recorded operation durations use the canonical producer’s monotonic clock around
execution and summarization. Start/finish timestamps are separate UTC wall-clock
readings. Their observed differences remain unchanged; the clock discrepancy
cause is not established. Both startup duration bases remain below 600 seconds.

The aggregate successful verification state is `LIVE_VERIFIED`. Failed attempts
retain their individual non-success classifications.

The portable package is `observed/summary.json`, `phase-ledger.json`,
`provenance.json`, `handover.json` and `manifest.json` under the isolated stream's
issue-363 evidence directory. It contains allowlisted exits, timings, counts and
comparisons, without environment values, protected paths or private fingerprints.
The isolated stream ended `READY_FOR_UBUNTU_RESTORE`; primary restoration and
whole-issue completion are independently owned by the integration root.
