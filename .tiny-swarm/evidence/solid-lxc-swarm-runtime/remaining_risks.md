# Issue #183 Remaining Risks

1. `REQ-017` remains open: public behavior uses the extracted modules and
   compatibility facades, but non-public `_Legacy*` historical definitions
   remain in `lxc_swarm_runtime.py` and should be removed in a separately
   verified cleanup pass.
2. The live post-install HTTP probe recorded `URLError` failures for the
   routed HTTPS hosts even though the Selenium browser suite passed all nine
   routes; the direct probe path needs TLS/routing diagnosis.
3. `REQ-025` is blocked because the observable SonarCloud gate is `ERROR` on
   New Code Security Rating (`2` versus threshold `1`).
4. `REQ-026` is blocked because the workflow commit has no SonarCloud branch
   analysis or before/after smell comparison; the exposed `main` analysis
   reports `425` open code smells.
5. The local quality result is not evidence of SonarCloud acceptance.
5. Existing provider/runtime risks remain as documented in
   `documentation/arc42/11_risks_and_debt.adoc`.
