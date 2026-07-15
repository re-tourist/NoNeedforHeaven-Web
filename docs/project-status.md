# Project status

## Current phase

**P3 — Persistence, replay, and versioning in progress**

Status: `TASK-002-versioned-save` completed and locally verified on 2026-07-15. This completes only
the snapshot/RNG persistence slice; P3 as a whole is not complete.

## Completed tasks

- `docs/tasks/TASK-000-bootstrap.md`
- `docs/tasks/TASK-001-domain-kernel.md`
- `docs/tasks/TASK-002-versioned-save.md`

## Implemented capabilities

- The complete P1 engineering, locked-dependency, quality-check, CI, health, and connectivity
  baseline.
- The P2 pure deterministic domain kernel with immutable synthetic state, typed commands,
  accepted/rejected results, events, and injected randomness.
- A `buxianxian-save` UTF-8 JSON schema v1 envelope containing complete domain and random state.
- Strict product, version, object-shape, field-type, domain-invariant, random-algorithm, and
  random-state validation.
- An explicit schema-version loader dispatch point; unknown versions are rejected without guessing.
- A versioned `xorshift64star` deterministic source with fixed-width portable state and rejection
  sampling for bounded integers.
- Atomic same-directory temporary writes using flush, file `fsync`, close, and `os.replace`, with
  failure cleanup and preservation of the previous valid save.
- Structured persistence failures through `SaveErrorCode` and `SaveError`.

The current `revision`, `counter`, commands, and event remain neutral contract fixtures. They are not
formal resources, actions, progression, or gameplay systems.

## Verification status

- All backend formatting, linting, Pyright strict type checks, and tests pass.
- Twenty focused infrastructure tests cover the frozen random vector, seed determinism, random
  restoration, save round-trip, restart-equivalent continuation, required format markers, malformed
  and non-UTF-8 JSON, all required compatibility/data errors, and atomic replacement failure.
- The complete backend suite passes with thirty tests: twenty infrastructure, nine domain, and the
  unchanged API health contract.
- Existing domain boundary tests still enforce standard-library-only imports and no filesystem
  modules; `buxianxian.domain` was not modified by TASK-002.
- The API still exposes only `GET /api/health`; no frontend file imports or exposes persistence.
- No production or development dependency was added.
- All save tests use pytest temporary directories; no player save is stored in the repository.

## Explicitly deferred

- Event persistence, transition logs, replay, and replay verification.
- Real legacy save fixtures, migration implementations, and save compatibility across a future
  domain-state redesign.
- Application services, new/load orchestration, multiple slots, backups, autosave, and save menus.
- HTTP save/load or command endpoints and all frontend persistence behavior.
- Databases, cloud saves, synchronization, authentication, and multiplayer.
- Final game-state models and all formal gameplay systems.
- Content schemas, compilation, authoring tools, narrative content, Obsidian runtime integration,
  and LLM integration.

## Next phase entry

The next P3 task requires a separate approved specification. It may address the smallest remaining
P3 requirement, but must not infer event replay, application APIs, UI, or migration behavior from
TASK-002. P3 remains in progress until its separately scoped exit requirements are satisfied.
