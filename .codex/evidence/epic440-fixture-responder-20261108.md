# S449 bounded fixture responder correction

Base `08541b3f` (full source base recorded in the accompanying pin manifest).
Root authorized a source-only fixture correction before another native pause.
Only the listener fixture, its existing test module and this record are changed.
The separately reviewed init compatibility delta is included verbatim from
source SHA3f49505f89e65805461a69dbf2b164fec9163cdd980a56e426b1e74e8589eb5e
and test SHA85725a25cd67a6c2825d4aee6f9663ed6ac9cd96ef103e89539fd52d2bab6118
before adding this responder change: both prepared/effect init argv omit the
unsupported `--no-start`; the fake rejects that flag before changing state.

## Actual prerequisite and preserved boundary

Root's static inspection of the exact pinned official Alpine3.21 rootfs found
only BusyBox installed, without its HTTPD applet. The prior `busybox httpd`
command could not provide the required success. No fixture success is inferred
from source checks. The preceding native attempt is reported fully restored;
this author did not query any host or active maintenance window.

The pinned Alpine3.21 BusyBox configuration enables NC, its server/extra/1.10
compatibility features, NETSTAT and AWK, while HTTPD is disabled:
https://raw.githubusercontent.com/alpinelinux/aports/3.21-stable/main/busybox/busyboxconfig
This is the source prerequisite, not an actual applet runtime acceptance claim.
Root must verify the actual pinned applet transport independently.

## Implemented behavior

A pure renderer accepts only the existing canonical 32-lowerhex run ID and
constructs a fixed HTTP/1.1 200 response. Content-Length is exactly32, Connection
is close, and the complete body is that run-specific nonce with no newline.
POSIX printf pipes the response into exactly one built-in BusyBox nc listener,
bound only to guest127.0.0.1:8080 with `-l -s 127.0.0.1 -p 8080 -w 15`.
All background input/output/error descriptors are detached through /dev/null.
No image, package, binary, network, host firewall or guest disk artifact is added.

Before returning from the existing <=20s exec command, the foreground shell
checks that the responder remains alive and polls only `busybox netstat -ltn`.
A fixed AWK predicate requires the exact IPv4 loopback8080 LISTEN row. At most
25 attempts with0.2s sleeps are made. Readiness never connects, so it cannot
consume the single response intended for the host. Failure remains fail-closed;
the existing owned guest cleanup stops/deletes the fixture. The nc lifetime is
bounded independently by its15s timeout.

Host curl disables configuration files/proxies, permits HTTP only, does not
follow redirects, and retains the bounded5s maximum with2s connection timeout.
Its output must equal the exact expected nonce, not merely be nonempty. Only the
body digest is retained. There is no external URL or alternative HTTP fallback.
The mandatory stopped-after-init, complete profile/effective-device checks,
no-listener-before-start, proxy scope, owned cleanup and unchanged route/Windows
comparisons remain in place. Fixture900s/cleanup120s bounds are unchanged.

## Authored tests and verification status

The existing full stateful lifecycle test returns the actual run nonce, checks
the selected exec renderer and exact body digest, and adds a wrong-body failure
that must still clean the owned instance and profiles. A new real POSIX shell
regression executes the renderer with only a temporary fake BusyBox transport:
no real socket, daemon, HTTP client, Incus or host resource is used. It records
printf's actual bytes, checks exact CRLF headers/body and fixed nc argv, proves
only nc/netstat/awk/sleep applets are requested once or finitely, accepts the
loopback listener and refuses an all-interface listener. Temporary owned process
groups are always terminated. Invalid run IDs are refused by the pure renderer.
These tests are authored and have not been run by this author.

Author checks: AST parsing of the two modified Python files and
`git diff --check` only. No imports, product execution, tests, hosts or commits.
Root must independently review exact pins, run focused/typecheck/all required
PC gates and actual pinned applet checks, then commit/stage fresh source before
any new intent/proposal/maintenance approval. Existing failed evidence and
restoration results remain historical. No fixture pass, supported version or
EPIC completion is claimed here.

## Root integration and actual designated-PC verification

Root independently reviewed renderer, nonce validation, exact argv/HTTP body, nonconnecting readiness and stateful failure cleanup. Pinned public Alpine binaries were extracted statically and run only on designated PC WSL using their own isolated musl loader: actual nc/netstat/awk/sleep present, httpd absent, exact nc flags documented by actual help. Applet/help logs SHA7a85e4b781db3f0f64fedd6f9f2734db856312220d1a5a33f77d560aad7d7073 /429e144d28100bf99f48654289bd90f496b9cf57b20bc7ab935d5f3e689d4141; this was no listener/Incus test.

Exact three-file08541-based PCcandidate typecheck918 PASS c044c2a10fc1d2568018d7e234e1f19a2e38a60460df1a76d7d3293011392caa; focused296/11.400s PASS69dfef0b854eb20ec9eee16f7552d88b3c32d6088a748175cdf0c76e3b2ea880; full seven quality PASS3416/216.489s/36skips, logaf877c3968eb4f63f1d8e9d46ffdb8d61e40f13491e0cc8499b491b2ab6a681d. Logs retained on PC private ext4. Root5a6e8c32 includes the identical separately tested no-start correction plus its evidence; this integration adds only the exact responder delta and record. No native/WSL real listener fixture or capability PASS attributed before execution.
