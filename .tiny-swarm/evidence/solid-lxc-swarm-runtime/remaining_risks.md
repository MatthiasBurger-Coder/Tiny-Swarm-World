# Issue #183 Remaining Risks

1. The live post-install HTTP probe recorded `URLError` failures for the
   routed HTTPS hosts even though the Selenium browser suite passed all nine
   routes; the direct probe path needs TLS/routing diagnosis.
2. SonarCloud PR #238 is green for commit `3a81bf0` with 90.0% New Code
   coverage and zero unresolved new issues.
3. Existing provider/runtime risks remain as documented in
   `documentation/arc42/11_risks_and_debt.adoc`.
