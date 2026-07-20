# Slice 03 Distribution Decision

Decision: SERIAL FALLBACK REVIEW.

Workflow orchestration, progress events and timeout handling share the same
application contracts. No parallel stream is safe. Frontend and live runtime
streams are not applicable.
