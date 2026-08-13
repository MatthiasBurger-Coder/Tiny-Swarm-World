# Issue #123 Remaining Risks

The following are intentionally open or evidence-pending after the local
documentation work:

| Risk | State | Next owner/action |
| --- | --- | --- |
| Docker socket authority and Portainer/agent exposure | Open | #126 defines ASVS/admin-surface treatment; #150 implements only the approved design. |
| Local HTTP/TLS and admin route assumptions | Evidence pending | #126 defines authentication, authorization, transport and exposure requirements. |
| Infisical bootstrap and local secret-file permissions | Evidence pending | Validate only in an authorized live workflow with redacted evidence. |
| Admin credentials and Pulsar token handling | Open/evidence pending | Apply secret policy, route/auth design and later live evidence contract. |
| Dependency and image vulnerability baseline | Evidence pending | Retain #127 supply-chain policy and collect approved scan evidence in its scope. |
| Unintended live setup mutation | Blocked by consent | #125 defines evidence; Public-Beta Green Path requires explicit live approval. |

These risks are not accepted merely by completion of #123. The risk register,
SoA and QMS CAPA/change-control documents define ownership and review rules.
