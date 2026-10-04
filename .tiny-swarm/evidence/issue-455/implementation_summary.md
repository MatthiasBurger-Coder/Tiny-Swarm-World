# Issue #455 implementation summary

BOOT-W03 / BOOT-05 is implemented on feature/incus-preparation-20261004.
Dependencies #453/#454 are CLOSED and present at baseline 1a8f237c.

The existing prepare_linux boundary prepares package/Python prerequisites, then
uses the prepared ordinary-user interpreter for an async Incus capability service.
The native composition facade injects prerequisites and path validation into its
internal Incus builder; there is no reverse composition import or new orchestrator.
Application depends on its port/domain observations; infrastructure owns canonical
provider YAML, profile policy, systemd/group/API commands and preserved inventory.

Plan/apply has exact separate consent for startup, access and create-only resources.
Stopped daemon inventory never socket-activates Incus. Persisted group membership
requires logout/login and reinventory; current-user version/info and all resolved
resources are required for Incus READY. Global default profile, credentials, daemon
settings, unrelated instances and existing compatible resources remain untouched.
Missing directory storage, a collision-free private IPv4 NAT/DHCP bridge and declared
profiles are created using local default-project API POSTs. No admin init, profile
edit, delete/reset, implicit existing-resource replacement or privileged default.
Settings-only compatible profiles are reused because existing launch supplies
--network and --storage. Existing resource config/identity, server config and real
host topology changes invalidate consent; DHCP/SLAAC timer countdown is normalized.

Bounded commands have finite 5-second probes / 60-second actions and zero retries;
prepared-interpreter stage deadline is 1800 seconds. Mutations persist private
intent/effect records and distinguish confirmed/uncertain actions. Failure stops
later stages; timeout/interruption exits 124/130 survive. Fresh plans allow safe
resume without automatic rollback. Read-only, refusal and verified no-op never write
evidence. sudo -v is the concrete narrow-elevation recovery prerequisite.

Incus commands use INCUS_CONF=/dev/null plus --force-local/default project. Source
inspection found Incus 6.0 PostRun can save OIDC client state when config.yml exists
even under force-local; the non-directory config root suppresses those writes and
user config/aliases without creating temporary client state. Reference:
https://github.com/lxc/incus/blob/v6.0.0/cmd/incus/main.go and
https://github.com/lxc/incus/blob/v6.0.0/shared/cliconfig/config.go.
API query flags were checked against the official Incus query manpage:
https://linuxcontainers.org/incus/docs/main/reference/manpages/incus/query/.
This source inspection is not live Incus verification.

Architecture ADR was independently accepted before product edits. Actual architecture
and Requirement Lead re-reviews PASS; Tester re-review PASS with 72 focused/architecture
tests. Does implementation still match EPIC #452? Yes: BOOT-05 remains local,
ordinary-user, consent-controlled and preserving; Windows lifecycle/capacity,
kernel/browser integration, aggregate handoff and live qualification remain W04–W09.
The completed #355 workflow was preserved; no workflow execute or checkpoint work.

Final independent completion audit: PASS. Final seven-phase local quality gate
exit 0 (2450 tests, 18 skips) and final focused84 tests PASS. Status: DONE locally.

Publication remediation: PR #466 initial SonarCloud gate identified blocking input in async orchestration. Consent now delegates through the native facade and existing Incus composition owner to a daemon-thread console adapter with cancellable Future delivery. Cancellation never waits for unanswered input or authorizes a late response. Exact yes/EOF semantics and re-inventory after approval remain preserved. Small reporting/configuration/resource validation helpers reduce cognitive complexity; exception-test setup now occurs outside assertRaises. No safety/quality bypass was introduced.
