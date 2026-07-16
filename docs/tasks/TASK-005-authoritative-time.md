# TASK-005: Authoritative game time

## Goal

Replace the synthetic counter fixture with the first formal authoritative game-state fact: elapsed
game days. A typed command advances time through the existing deterministic domain engine and the
existing save-before-memory-commit application session.

```text
GameState(revision, elapsed_days)
    + AdvanceTime(days)
    -> Accepted(new state, TimeAdvanced)
    or Rejected(original state, structured reason)
```

## Required public behavior

- A minimal initial state represents revision 0 and elapsed day 0.
- Elapsed time is a non-negative integer count of days since game start.
- A positive, bounded `AdvanceTime` command increments elapsed days and revision exactly once.
- A `TimeAdvanced` event records the prior value, resulting value, and elapsed amount.
- Invalid type, non-positive amount, per-command overflow, and total-time overflow are structured
  domain rejections that preserve the original state.
- The persistent session saves candidate time and RNG before changing official memory.
- Save schema v2 persists `revision` and `elapsed_days` while preserving the `buxianxian-save`
  identity and xorshift64star v1 random-state contract.

## Explicitly excluded

- calendar years, months, hours, seasons, solar terms, or named eras;
- age, lifespan, action points, schedules, automatic world updates, or NPC progression;
- cultivation, attributes, inventory, travel, tasks, events, or other gameplay systems;
- API endpoints, frontend behavior, save slots, desktop packaging, or narrative content;
- content-package/state integration or any TASK-004 content change.

## Pre-alpha compatibility

The synthetic v1 counter save is deliberately not migrated because no external playable release or
real player save exists. It is rejected as an unsupported version. Formal save-compatibility
commitments begin with the first externally playable release; ADR-006 records this policy.

## Implemented contract

- `GameState` contains only `revision` and authoritative `elapsed_days`.
- `AdvanceTime(days)` accepts exact positive integers within the documented command and total-time
  ceilings.
- `TimeAdvanced` contains `previous_elapsed_days`, `current_elapsed_days`, and `days_elapsed`.
- Rejections use `INVALID_DAY_COUNT` or `DAY_COUNT_OUT_OF_RANGE` and return the original state.
- `buxianxian-save` schema v2 strictly persists elapsed time and xorshift64star v1 state.
- The unchanged persistent session commits time only after candidate persistence succeeds.

## Completion

Completed on 2026-07-16. ADR-006 records the authoritative time coordinate, numeric invariants,
schema-v2 shape, pre-alpha v1 rejection, and released-save compatibility threshold. No calendar,
automatic simulation, character system, content integration, API, frontend, or other gameplay
capability was added.
