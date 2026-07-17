# TASK-007: First operable web game loop

## Goal

Connect the existing headless new-game, save/load, session, and authoritative-time capabilities to
FastAPI and the vanilla TypeScript browser client as the first complete user-operable vertical
slice.

## Required behavior

- Inspect the configured single local save without exposing its path or RNG state.
- Create one server-authoritative in-memory character draft with an opaque ID; a replacement draft
  invalidates the previous one.
- Confirm a valid draft into an atomically persisted new game, requiring explicit overwrite consent
  whenever a save file already exists.
- Load the single valid save into one active in-process session.
- Submit `AdvanceTime` with the caller's expected revision and expose structured success, conflict,
  domain rejection, persistence failure, and no-session results.
- Project player name, aptitudes, prototype trait labels, elapsed days, and revision to the browser.
- Provide boot, start, character-creation, overview, busy, and recoverable-error UI states without
  duplicating domain rules in TypeScript.

## Explicit exclusions

- cultivation, inventory, storage, locations, travel, tasks, events, combat, NPCs, or narrative;
- calendars, age, lifespan, months, seasons, or automatic simulation;
- multiple save slots, delete/import/export, accounts, networking, or desktop packaging;
- production trait effects, rarity, conflicts, conditions, or DSLs;
- TASK-004 runtime content reading, artwork, audio, animation, or LLM behavior.

## Completion record

Completed and verified on 2026-07-17.

- Application: one typed single-save runtime owns session/draft/new-game/catalog/source lifecycle.
- API: five game routes, strict projections, normalized validation, and stable expected errors.
- Frontend: boot/start/creation/overview controller and responsive accessible vanilla DOM views.
- Persistence: explicit overwrite and exact state/RNG recovery after runtime restart.
- Verification: 125 backend tests, 18 frontend transport/controller regression tests, all
  format/lint/type/build checks, zero-entry content validation, isolated Edge creation/wait/restart
  flow, and Git scope/artifact review.
- Scope: no additional gameplay, content reader, save slot, desktop, narrative, or LLM work.
