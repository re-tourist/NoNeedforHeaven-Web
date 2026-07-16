# Project status

## Current phase

**P7 — Generic gameplay capabilities, first bounded mechanism in progress**

Status: `TASK-005-authoritative-time` completed and locally verified on 2026-07-16. Authoritative
elapsed-day time is the only formal gameplay mechanism. P7 as a whole is not complete. Earlier P3
replay, P4 reference validation, P5 API, and P6 client work remain explicitly deferred.

## Completed tasks

- `docs/tasks/TASK-000-bootstrap.md`
- `docs/tasks/TASK-001-domain-kernel.md`
- `docs/tasks/TASK-002-versioned-save.md`
- `docs/tasks/TASK-003-persistent-session.md`
- `docs/tasks/TASK-004-read-only-content-compiler.md`
- `docs/tasks/TASK-005-authoritative-time.md`

## Implemented capabilities

- The complete engineering, locked-dependency, quality-check, CI, health, and connectivity baseline.
- A pure deterministic domain kernel with immutable state, typed commands, accepted/rejected
  results, domain events, and an injected random-source boundary.
- Formal `GameState(revision, elapsed_days)` with exact non-negative integer invariants and explicit
  numeric ceilings.
- Typed, bounded `AdvanceTime(days)` transitions that increment revision once and emit one complete
  `TimeAdvanced` fact without mutating input state or consuming RNG.
- Structured invalid-day and out-of-range rejection that preserves revision and elapsed time.
- Strict `buxianxian-save` JSON schema v2 snapshots containing formal time and xorshift64star v1
  state, with structured errors and atomic same-directory replacement.
- Explicit unsupported-version rejection for experimental counter-based schema v1; no fictional
  counter-to-time migration.
- A headless `PersistentGameSession` with expected-revision protection, candidate RNG execution,
  save-before-memory-commit ordering, and complete rollback on rejection or persistence failure.
- The independent TASK-004 published read-only-document compiler and deterministic
  `buxianxian-content` JSON v1 package boundary.

The source tree contains no current counter state or counter command. The word appears only in
historical records and persistence tests that prove pre-alpha schema v1 is rejected.

## Verification status

- All backend formatting, linting, Pyright strict type checks, and tests pass.
- Fourteen formal time tests cover day zero, legal advancement, one-step revision, complete events,
  immutability, invalid values, numeric bounds, and determinism without RNG use.
- Seventeen persistence tests cover schema v2 time/RNG round-trip, continuous versus resumed state
  and RNG, strict invalid data, v1/unknown-version rejection, and atomic old-save preservation.
- Seven application tests cover explicit/loaded session initialization, successful time commit,
  RNG stability, revision conflict, domain rejection, persistence rollback, and deterministic retry.
- The complete backend suite passes with seventy-six tests, including all unchanged RNG, content,
  boundary, and API health tests.
- Domain purity remains enforced. The session coordinator, application ports, RNG implementation,
  content compiler, API, frontend, and dependency manifests are unchanged by TASK-005.
- No real save, generated runtime content, formal narrative, or private author material is stored in
  the repository.

## Explicitly deferred

- Years, months, hours, seasons, solar terms, named eras, and all calendar projections.
- Player age, lifespan, action points, schedules, daily queues, and automatic world/NPC updates.
- Cultivation, attributes, inventory, locations, travel, work, crafting, trade, tasks, relationships,
  combat, event pools, resources, and all other gameplay systems.
- Event persistence, transition logs, replay, and event sourcing.
- Released-save migration tooling; compatibility commitment starts with the first externally
  playable version under ADR-006.
- Runtime content loading, cross-content references, content/state binding, and additional content
  schemas.
- HTTP gameplay/content endpoints, frontend gameplay behavior, save slots, autosave, desktop
  packaging, formal narrative content, Obsidian runtime/plugins, and LLM integration.

## Next phase entry

The next task requires a separate approved specification. It must not infer a calendar, daily world
simulation, character creation, cultivation, API, frontend, or another gameplay capability from
TASK-005. P7 remains incomplete and each additional mechanism requires its own bounded contract and
tests.
