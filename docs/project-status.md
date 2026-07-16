# Project status

## Current phase

**P7 — Generic gameplay capabilities, bounded foundations in progress**

Status: `TASK-006-new-game-character-creation` completed and locally verified on 2026-07-16.
Authoritative elapsed-day time and headless new-game character creation are the only formal gameplay
foundations. P7 as a whole is not complete. Earlier P3 replay, P4 reference validation, P5 API, and
P6 client work remain explicitly deferred.

## Completed tasks

- `docs/tasks/TASK-000-bootstrap.md`
- `docs/tasks/TASK-001-domain-kernel.md`
- `docs/tasks/TASK-002-versioned-save.md`
- `docs/tasks/TASK-003-persistent-session.md`
- `docs/tasks/TASK-004-read-only-content-compiler.md`
- `docs/tasks/TASK-005-authoritative-time.md`
- `docs/tasks/TASK-006-new-game-character-creation.md`

## Implemented capabilities

- The complete engineering, locked-dependency, quality-check, CI, health, and connectivity baseline.
- A pure deterministic domain kernel with immutable state, typed commands, accepted/rejected
  results, domain events, and an injected random-source boundary.
- Complete immutable `GameState(revision, elapsed_days, player)` with one normalized player name,
  five bounded innate aptitudes totaling 25, and two canonical stable trait IDs.
- Typed, bounded `AdvanceTime(days)` transitions that increment revision once and emit one complete
  `TimeAdvanced` fact without mutating input state or consuming RNG.
- Deterministic character-creation candidates: three distinct aptitude options and six distinct
  traits from an explicit caller catalog, selected through bounded injected-RNG sampling.
- A two-stage headless `NewGameService` that retains the post-generation candidate RNG, revalidates
  confirmation, persists complete initial state plus RNG, and exposes a session only after save.
- Strict `buxianxian-save` JSON schema v3 snapshots containing complete player, time, revision, and
  xorshift64star v1 state, with structured errors and atomic same-directory replacement.
- Explicit unsupported-version rejection for experimental counter schema v1 and player-less time
  schema v2; no fictional migration or guessed player data.
- A headless `PersistentGameSession` with expected-revision protection, candidate RNG execution,
  save-before-memory-commit ordering, and complete rollback on rejection or persistence failure.
- The independent TASK-004 published read-only-document compiler and deterministic
  `buxianxian-content` JSON v1 package boundary.

No production trait catalog or trait effects are present. Test trait definitions are neutral
fixtures only. The synthetic TASK-001 counter appears only in historical records and tests proving
old experimental saves are rejected.

## Verification status

- All backend formatting, linting, Pyright strict type checks, and 103 tests pass.
- Fourteen character-creation domain tests cover determinism, distinct candidates, aptitude
  invariants, catalog/RNG contracts, name validation, forged choices, and trait selection errors.
- Six new-game application tests cover fork isolation, failed preparation/confirmation, exact
  post-generation RNG persistence, real JSON round-trip, save failure, and deterministic retry.
- Twenty-four persistence tests cover strict schema-v3 player/time/RNG round-trip, continuous versus
  resumed state/RNG, invalid player/state/random data, v1/v2/unknown rejection, and atomic old-save
  preservation.
- Existing time, session, RNG, content compiler, dependency-boundary, and API health tests continue
  to pass unchanged in behavior.
- Published-content validation passes with zero production entries. No real save, generated runtime
  content, formal trait, narrative, or private author material is stored in the repository.

## Explicitly deferred

- Character-creation API/frontend, rerolls, save slots, autosave, and restart-resumable drafts.
- Formal trait catalog, effects, levels, rarity, budgets, conflicts, prerequisites, or DSLs.
- Gender, appearance, age, lifespan, origin, sect, location, portrait, title, or name generation.
- Years, months, hours, seasons, solar terms, named eras, and all calendar projections.
- Cultivation, combat attributes, inventory, resources, money, travel, work, crafting, trade, tasks,
  relationships, scenes, narrative, world/NPC simulation, and all other gameplay systems.
- Event persistence, transition logs, replay, event sourcing, and released-save migration tooling.
- Runtime content loading, cross-content references, content/state binding, and additional content
  schemas.
- HTTP gameplay/content endpoints, frontend gameplay behavior, desktop packaging, Obsidian
  runtime/plugins, and LLM integration.

## Next phase entry

The next task requires a separate approved specification. Future time-consuming gameplay commands
must apply their gameplay effects and elapsed-day change in one atomic domain transition; they must
not commit an effect and then issue a separate `AdvanceTime`. No API, frontend, cultivation, item,
location, narrative, or other system follows implicitly from TASK-006.
