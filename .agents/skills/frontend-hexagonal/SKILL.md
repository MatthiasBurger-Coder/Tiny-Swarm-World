---
name: frontend-hexagonal
description: Use for frontend boundary design that separates UI components, frontend state, API adapters, and domain evidence models.
---

# Frontend Hexagonal Boundaries

## Purpose

Keep frontend UI, application state and transport adapters separated.

## Practices

- Keep components presentational where practical.
- Place business rules and data transformation behind explicit frontend services or ports.
- Keep API client details out of visual components.
- Use typed models for confirmed evidence, derived analysis, gaps and hypotheses.
- Keep error states explicit and reviewable.

## Verification

- Inspect the existing frontend structure before creating directories.
- Add component, state or adapter tests according to the verified stack.
