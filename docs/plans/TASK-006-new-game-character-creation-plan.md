# TASK-006 New Game and Character Creation ExecPlan

## 1. Objective

Build a deterministic headless character-creation and new-game boundary that produces a complete
immutable player-bearing state and persists it with the exact post-generation RNG position before
exposing a `PersistentGameSession`.

## 2. Scope

Included:

- five bounded innate aptitude values with a fixed total;
- three deterministic distinct aptitude candidates;
- a caller-provided trait-definition catalog and six deterministic distinct trait candidates;
- normalized Unicode player-name validation;
- structured candidate-generation, confirmation, and initial-save failures;
- complete `PlayerCharacter` in formal `GameState`;
- a two-stage application service using forked RNG and save-before-session semantics;
- strict `buxianxian-save` schema v3 for player, time, revision, and RNG;
- updated domain/save/time/session tests plus dedicated creation/new-game tests;
- ADR-007 and active architecture/status/developer documentation.

Excluded:

- API/frontend integration, rerolls, save slots, autosave, or desktop packaging;
- formal product traits or content-compiler trait types;
- trait effects, conditions, conflicts, rarity, levels, budgets, or scripting;
- age, lifespan, gender, appearance, origin, sect, location, calendar, or daily simulation;
- cultivation, combat, inventory, resources, money, travel, tasks, scenes, narrative, or LLMs.

## 3. Existing context

Step 0 reviewed and jointly committed the verified TASK-004/TASK-005 work as commit `dd61243`, then
pushed it to `origin/main`. Local and remote main match and the working tree is clean. The baseline
passes seventy-six backend tests, three frontend tests, all formatting/lint/type checks, content
validation, and the frontend production build.

The current formal `GameState` contains revision and elapsed days. The save adapter strictly handles
schema v2 plus xorshift64star v1 state. `PersistentGameSession` already performs revision checking,
candidate RNG forking, domain transition, persistence, and memory commit in the correct order.

Character creation precedes a formal session, so it must not use a nullable player field or a
half-created `GameState`. The existing `TransactionalRandomSource.fork()` and generic
`SessionRepository` ports are sufficient for a separate pre-session application service.

## 4. Proposed design

### Formal player model

`InnateAptitudes` is a frozen value object with `constitution`, `comprehension`, `spiritual_sense`,
`temperament`, and `fortune`. Every value is an exact integer from 1 through 10 and the total is 25.

`PlayerCharacter` is frozen and contains a normalized name, one aptitude value object, and a
canonical sorted tuple of exactly two distinct stable trait IDs. `GameState` requires a player;
there is no optional or partially initialized variant.

### Aptitude candidate algorithm

The domain enumerates every lexicographically ordered five-integer distribution satisfying the
range and total constraints. Generation selects three distinct indices with a bounded partial
Fisher-Yates sample using only the injected `RandomSource`.

This gives a uniform sample over valid ordered distributions when the RNG's inclusive integer
contract is unbiased. It performs exactly three bounded draws for aptitudes, never retries on
duplicates, and has deterministic ordering independent of sets or filesystems.

Each option receives a candidate-local ID (`aptitude_option_1` through `aptitude_option_3`).
Confirmation accepts the ID rather than trusting caller-submitted aptitude values.

### Trait catalog and selection

`TraitDefinition` contains stable lowercase machine ID, Chinese display name, and Chinese short
description. The domain accepts an explicit sequence, validates fields and unique IDs, sorts by ID,
then performs six bounded partial-Fisher-Yates draws without replacement. No production catalog is
included; tests use neutral definitions only.

Confirmation requires exactly two distinct offered IDs. Stored IDs are sorted into a canonical
immutable tuple; selection order has no hidden gameplay meaning.

### Name rules

The confirmation boundary requires an exact string, strips leading/trailing whitespace, normalizes
to Unicode NFC, rejects empty results, caps the normalized name at 32 code points, and rejects
Unicode control characters (`Cc`) and isolated surrogate code points (`Cs`). Chinese and ordinary
Unicode characters remain allowed. No generation or moderation exists.

### Structured domain results

Candidate generation and confirmation return frozen discriminated result types. Stable error codes
distinguish invalid name, invalid aptitude selection, trait count, duplicate trait, unoffered trait,
insufficient catalog, invalid catalog/candidate contract, and RNG contract violation. Expected
failures are not inferred from strings or raw exceptions.

### Application new-game transaction

`NewGameService[RandomT]` has two operations:

1. `begin(random_source)` forks the caller RNG, generates candidates on the fork, and returns a
   draft holding the candidates plus the consumed candidate RNG position. Failure discards the fork.
2. `confirm(draft, ...)` runs pure confirmation, forks the draft RNG, atomically saves the complete
   state/RNG, and creates `PersistentGameSession` only after save succeeds.

Invalid confirmation performs no RNG operation. Save failure returns `InitialSaveFailed`, exposes no
session, preserves the draft for deterministic retry, and relies on the existing atomic repository
to preserve any old file.

### Save schema v3

The identity remains `buxianxian-save`; schema 3 adds strict player data:

```json
{
  "format": "buxianxian-save",
  "schema_version": 3,
  "state": {
    "revision": 0,
    "elapsed_days": 0,
    "player": {
      "name": "测试角色",
      "aptitudes": {
        "constitution": 5,
        "comprehension": 5,
        "spiritual_sense": 5,
        "temperament": 5,
        "fortune": 5
      },
      "trait_ids": ["trait.alpha", "trait.beta"]
    }
  },
  "random": {
    "algorithm": "xorshift64star",
    "version": 1,
    "state": "0123456789abcdef"
  }
}
```

Experimental schema v2 is explicitly unsupported; no player data is guessed. ADR-007 supersedes
ADR-006 only for the current state shape and current save version.

### Time-consuming command composition

`AdvanceTime` remains valid for direct time skipping. Future gameplay commands that consume time
must update their gameplay facts and elapsed days within one atomic domain transition. A two-command
sequence would expose partial commits and is prohibited by ADR-007.

## 5. Milestones

### Milestone A: domain player and creation contracts

Affected files: domain model, new character-creation module, exports, and domain tests.

Expected behavior: bounded deterministic candidates, structured validation, complete initial state,
and unchanged immutable `AdvanceTime` semantics with a required player.

Validation: focused Ruff, Pyright, and domain tests.

Recovery: all changes are pure standard-library domain code; no save is written yet.

### Milestone B: pre-session application transaction

Affected files: new application module/exports and application tests.

Expected behavior: forked candidate RNG, no advancement on failed confirmation, save-before-session,
structured persistence failure, correct resumed RNG, and deterministic retry.

Validation: focused application tests and existing dependency-boundary tests.

Recovery: existing session implementation and ports remain unchanged unless strict typing reveals a
minimal contract gap.

### Milestone C: save v3 and regression updates

Affected files: save repository plus domain, persistence, and session fixtures/tests.

Expected behavior: strict complete player round-trip, old-version rejection, time/session/RNG
regressions, and atomic old-save preservation.

Validation: focused infrastructure/application/domain suites.

Recovery: product identity, RNG format, and atomic-write implementation remain unchanged.

### Milestone D: decisions, docs, and final verification

Affected files: ADR-006 status note, ADR-007, architecture/status/README/backend README, TASK-006
record, and this plan.

Expected behavior: active docs describe new-game/session/save boundaries and prohibit two-step
gameplay/time commits.

Validation: complete backend checks, content isolation, API/frontend/dependency diff audit, artifact
scan, and `git diff --check`.

Recovery: no API, frontend, formal content, or additional gameplay files are introduced.

## 6. Progress log

- [x] 2026-07-16: Audited TASK-004/TASK-005 differences, untracked files, secrets, artifacts,
  naming, branch, remote, and repository scope.
- [x] 2026-07-16: Ran complete backend and frontend quality checks successfully.
- [x] 2026-07-16: Created and pushed joint baseline commit `dd61243`; confirmed local/remote main
  equality and a clean working tree.
- [x] 2026-07-16: Audited current domain state, RNG, save v2, application ports/session, tests,
  architecture, roadmap, ADRs, and TASK-001 through TASK-005 records.
- [x] 2026-07-16: Reported the bounded generation, validation, transaction, schema-v3, and atomic-time
  composition plan before implementation.
- [x] 2026-07-16: Implemented formal player and character-creation domain contracts.
- [x] 2026-07-16: Implemented the pre-session new-game application service.
- [x] 2026-07-16: Upgraded persistence to schema v3 and updated regression fixtures.
- [x] 2026-07-16: Recorded ADR-007 and synchronized active architecture/developer/status docs.
- [x] 2026-07-16: Completed full verification and scope review with 103 passing backend tests.

## 7. Discoveries and deviations

- TASK-004 and TASK-005 shared active README, architecture, and status files. A joint commit avoided
  fragile hunk surgery and preserved already verified behavior.
- The first sandboxed push could not reach GitHub; the approved network retry succeeded without
  changing repository data.
- The existing application persistence/RNG protocols already express the required pre-session
  types, so no generic dependency-injection or unit-of-work framework was needed.
- A complete player can be added without changing `PersistentGameSession`, its repository port, or
  the RNG algorithm. Only the domain state constructor and persistence encoding changed.
- Strict result typing caught malformed application exports during focused checks; the export list
  was corrected before the full suite and no public runtime behavior was affected.

## 8. Verification

Step 0 completed:

```text
backend Ruff format/lint, Pyright, pytest -> passed; 76 tests
published content validate               -> passed; 0 entries
frontend Prettier/ESLint/TypeScript       -> passed
frontend Vitest                           -> passed; 3 tests
frontend production build                 -> passed
git push origin main                      -> dd61243 pushed
local main == origin/main                 -> confirmed
working tree                              -> clean
```

TASK-006 completed:

```text
backend Ruff format --check --no-cache .       -> passed; 33 files formatted
backend Ruff check --no-cache .                -> passed
backend Pyright                                -> passed; 0 errors, 0 warnings
backend pytest -p no:cacheprovider             -> passed; 103 tests
published content validate                     -> passed; 0 entries
git diff --check                               -> passed
domain/application/infrastructure boundaries   -> reviewed; no forbidden dependency
API/frontend/dependency manifests              -> unchanged by TASK-006
runtime saves/generated content/private files  -> absent
```

## 9. Completion summary

TASK-006 adds a deterministic, bounded, two-stage character-creation flow; a complete immutable
player-bearing state; atomic initial save plus post-generation RNG persistence; strict save schema
v3; and an application service that exposes a persistent session only after save success. It adds
no API, frontend, production trait content, trait behavior, narrative, or subsequent gameplay.
