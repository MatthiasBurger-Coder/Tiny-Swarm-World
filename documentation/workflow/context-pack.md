# Workflow Context Pack

Workflow: `traefik-https-ingress-existing-ca-20260609`
Version: `1.0.0`
Branch: `feature/traefik-https-ingress-existing-ca-20260609`
Profile: `FULL_PATH`

## Purpose

Navigation aid for the active Traefik HTTPS ingress workflow. This file does
not replace `AGENTS.md`, `QUALITY.md`, ADRs, arc42, routing rules, role files,
or skill files.

## Process Strand

- Workflow authoring
- Architecture governance
- Python automation
- Docker Swarm / LXC runtime
- TLS and existing CA validation
- Live browser verification

## Affected Areas

- `documentation/workflow/**`
- `documentation/architecture/**`
- `documentation/arc42/**`
- `src/tiny_swarm_world/**`
- `infra/config/**`
- `infra/compose/**`
- `tests/**`

## Forbidden Areas

- Java, Maven, Spring Boot project structure
- React, TypeScript, Vite, TSX/JSX frontend project setup
- Kubernetes-first deployment
- Windows-native command examples for normal setup
- Committed secrets, CA private keys, live evidence, raw command output, local
  host topology

## Required Roles

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior DevOps Engineer
- Senior Security Engineer
- Senior Tester
- Senior Documentation Engineer

## Conditional Roles

- Greenpath Recovery Lead
- Failure Classification Expert
- Evidence Auditor

## Quality Commands

```bash
git diff --check
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
TSW_RUN_POST_INSTALL_BROWSER_LIVE=1 PYTHONPATH=src python3 -m unittest tests.live.test_post_install_browser_live
```

The live browser command is opt-in only and not part of the default quality
gate.

## Hash Provenance

See `context-pack.json` for recorded file hashes.
