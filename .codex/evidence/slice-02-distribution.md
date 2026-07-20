# Slice 02 Distribution Decision

Decision: SERIAL FALLBACK REVIEW.

The existing network ports and WSL repair adapter share network contracts and
mutation guards. No safe parallel stream is selected. Native Linux routing and
WSL routing are reviewed together because their separation is the acceptance
boundary.
