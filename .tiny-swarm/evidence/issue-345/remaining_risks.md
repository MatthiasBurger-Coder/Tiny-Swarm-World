# Remaining Risks — #345 / ARCH-03.02

- `installer.py` and `simple_installer.py` remain explicit legacy boundary
  exceptions until ARC-03 extracts the installer lifecycle.
- The repository has no physical `interfaces` package; the contract documents
  and reserves that logical layer so a future package cannot be imported by
  domain code.
- The composition module cycle identified by ARCH-03.01 remains ARC-04 work;
  this slice does not claim to remove it.
- Local verification does not establish live, browser, or SonarQube evidence.
