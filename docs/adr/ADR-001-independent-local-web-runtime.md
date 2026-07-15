# ADR-001: Independent local web runtime

- Status: Accepted
- Date: 2026-07-15

## Context

The project began as an Obsidian-based text-game idea. Obsidian remains useful for writing and knowledge organization, but its plugin environment would constrain game presentation, runtime state, testing, and distribution.

## Decision

Build “不羡仙” as an independent local web application.

- Python provides the authoritative runtime.
- A browser frontend provides presentation and input.
- Obsidian is an optional author workspace, not a runtime dependency.
- Author source will later be explicitly validated and compiled before runtime use.

## Consequences

Positive:

- free UI design;
- testable game kernel;
- independent distribution path;
- simpler Python integration for simulation and future LLM work;
- continued use of Obsidian for authoring.

Costs:

- separate backend and frontend toolchains;
- explicit API contracts are required;
- a future content pipeline is required;
- desktop packaging is deferred.
