# Issue #183 Remaining Risks

1. `REQ-017` remains open: public behavior uses the extracted modules and
   compatibility facades, but non-public `_Legacy*` historical definitions
   remain in `lxc_swarm_runtime.py` and should be removed in a separately
   verified cleanup pass.
2. `REQ-021` and `REQ-022` are blocked by `LIVE_CONSENT_MISSING`; the static
   Selenium contract does not prove a live LXC-backed routed page.
3. `REQ-025` and `REQ-026` are blocked because no observable SonarQube result
   or before/after smell comparison is available.
4. The local quality result is not evidence of live, Selenium, or SonarQube
   success.
5. Existing provider/runtime risks remain as documented in
   `documentation/arc42/11_risks_and_debt.adoc`.
