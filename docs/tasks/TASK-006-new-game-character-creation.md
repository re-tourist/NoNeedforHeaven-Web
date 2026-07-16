# TASK-006: Headless new game and character creation

## Goal

Establish a deterministic, UI-independent new-game flow that generates bounded character choices,
validates the player's selections and name, creates the first complete player-bearing `GameState`,
atomically persists it with the post-generation RNG position, and only then creates a persistent
session.

## Required public behavior

- Five immutable innate aptitudes each range from 1 through 10 and total exactly 25.
- Candidate generation returns three distinct aptitude options and six distinct traits from an
  explicit caller-provided catalog.
- Candidate generation is deterministic, bounded, independent of global `random`, and performed on
  a forked transactional RNG.
- Confirmation revalidates the selected aptitude option, exactly two distinct offered trait IDs,
  and a trimmed, bounded, control-free Unicode name.
- The initial complete state has revision 0, elapsed day 0, and an immutable player profile.
- Persistence success commits state plus the post-generation RNG position before a session exists.
- Validation or persistence failure does not create a session or advance the caller's official RNG.
- `buxianxian-save` schema v3 strictly persists player, time, revision, and xorshift64star v1 state.

## Explicitly excluded

- character creation API or frontend;
- reroll controls, gender, age, lifespan, appearance, portraits, origin, sect, or map position;
- formal trait catalog, trait effects, levels, rarity, budgets, conflicts, conditions, or DSLs;
- cultivation, combat attributes, inventory, money, resources, tasks, travel, scenes, or narrative;
- content-compiler trait schemas, save slots, desktop packaging, or LLM behavior.

## Time composition rule

`AdvanceTime` remains a direct time-skip command. Future cultivation, travel, work, crafting, or
other time-consuming commands must apply their gameplay effects and elapsed-time change atomically
in one domain transition. They must not commit gameplay first and submit `AdvanceTime` afterward.

## Completion record

Completed and locally verified on 2026-07-16.

- Domain contracts: immutable player/aptitude state, deterministic candidate generation, typed
  confirmation, and structured expected failures.
- Application contract: two-stage `NewGameService` with private candidate RNG, save-before-session
  ordering, structured initial-save failure, and deterministic retry.
- Persistence contract: strict `buxianxian-save` schema v3 with complete player/time/revision/RNG;
  experimental v1/v2 are rejected without guessed migration.
- Verification: Ruff format/lint, Pyright, 103 pytest tests, zero-entry published-content validation,
  dependency/scope review, and `git diff --check` all pass.
- Scope: no API, frontend, production traits/effects, cultivation, inventory, narrative, or other
  later gameplay capability was implemented.
