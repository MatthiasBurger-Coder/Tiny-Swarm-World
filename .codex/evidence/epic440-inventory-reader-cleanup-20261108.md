# Bounded reader handle cleanup

Actual NativeR5 read-only full recovery capture failed with Errno24: each
Runner invocation omitted explicit selector/stdout/stderr closure. The exact
source change closes only its own three reader handles in finally, retaining
all command/time/byte/admission and owned kill/reap behavior.

Independent reviewer preflight_review approved source84db3608/test8f8df679.
Root authored this narrow correction and records role passes as one integrator.
Actual subprocess regression uses96 harmless readlink children with GCdisabled
and RLIMIT_NOFILE64 in the child only; descriptor growth stays<=1. Success,
external alarm and interrupt also assert both streams/selector closure.

Combined PC SSH/WSL native-r5-correction-r1:348 focused PASS,type978 PASS,all7
quality PASS,3626 tests/36 skipped/288.815s; full quality log SHA256
`d32db48eadfd55fd30840e96f5affce94523f7dd6040a1bf0f4ee32dc0b8fb92`.
No host qualification PASS follows. Immutable historical source remains intact;
new recovery readers require their own exact source/approval binding.
