# Issue #187 — Implementation Summary

Issue #187 replaces the HostPreflightProbe service-name conditional chain with
an ordered, typed service-probe registry while preserving the public method
and all existing service fingerprints.

Implemented:

- added ServiceProbe, HttpServiceProbe, CallbackServiceProbe and
  ServiceProbeRegistry under infrastructure preflight/service_probes;
- encoded the exact 15 named service patterns in compatibility order;
- delegated HostPreflightProbe.port_matches_expected_service without changing
  its signature;
- kept low-level HTTP/TLS/TCP behavior and unrelated host checks in their
  existing owner;
- added focused registry tests and a no-conditional architecture guard;
- recorded before/after responsibility evidence and local audit state.

No live service check or host-detection redesign was introduced.
