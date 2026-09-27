# Implementation summary

Issue #357 relocates native Linux versus WSL2 host preparation adapter binding from the application service into `infrastructure/composition_platform.py`. The application now accepts an environment-to-adapter mapping, checks consent before host detection, blocks unsupported hosts, and invokes the selected adapter. Factories remain lazy.

The architecture note inventories remaining conditionals and explains their policy or diagnostic ownership. No live infrastructure action was run.
