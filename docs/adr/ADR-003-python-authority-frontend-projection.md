# ADR-003: Python authority and frontend projection

- Status: Accepted
- Date: 2026-07-15

## Context

Using both Python and TypeScript can accidentally create duplicated rules and divergent state.

## Decision

Python is the sole authority for durable game state and game outcomes.

The frontend:

- requests read models;
- submits player commands;
- displays loading, success, and failure;
- may hold transient presentation state;
- does not apply authoritative effects.

## Consequences

- game rules have one implementation;
- API contracts become important;
- offline browser-only operation is not an initial goal;
- frontend tests focus on rendering and transport behavior rather than duplicating domain outcomes.
