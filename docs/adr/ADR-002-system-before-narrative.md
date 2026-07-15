# ADR-002: System before narrative

- Status: Accepted
- Date: 2026-07-15

## Context

A story scene can make an early demo feel concrete, but it also encourages named-character logic, special-case effects, and premature content schemas before the engine's actual needs are understood.

## Decision

Build and validate generic mechanisms before introducing formal narrative content.

Before the narrative-integration phase:

- all tests and demonstrations use neutral synthetic fixtures;
- no named character, faction, location, cultivation method, or plot branch enters the core implementation;
- a narrative requirement cannot justify a one-off domain rule;
- the core engine must be demonstrably usable for a non-xianxia test game.

## Consequences

Positive:

- cleaner domain abstractions;
- lower rework risk;
- better tests;
- story content can evolve independently;
- Codex tasks remain easier to review.

Costs:

- early demos are visually and emotionally plain;
- some content requirements will be discovered later;
- discipline is needed to resist premature feature requests.
