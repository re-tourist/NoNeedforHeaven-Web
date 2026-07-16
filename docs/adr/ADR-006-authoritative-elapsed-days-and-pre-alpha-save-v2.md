# ADR-006: Authoritative elapsed days and pre-alpha save v2

- Status: Superseded in part by ADR-007
- Date: 2026-07-16

ADR-007 supersedes only the minimal player-less state shape and current schema-v2 statement.
Elapsed days, numeric bounds, pre-alpha compatibility policy, and direct `AdvanceTime` semantics
remain accepted.

## Context

TASK-001 used `revision` and a synthetic `counter` only to prove the deterministic transition
contract. TASK-002 persisted that shape in `buxianxian-save` schema v1. The project has not shipped
an externally playable version and has no real player saves that depend on the experimental field.

TASK-005 introduces the first formal gameplay fact. Future activities and world behavior need one
authoritative time coordinate, but the calendar, years, months, seasons, hours, and named eras are
not yet defined.

Changing the meaning of schema v1 in place would make the version marker dishonest. Inventing a
counter-to-time migration would assert semantics that the counter never had.

## Decision

### Authoritative time coordinate

`GameState` contains exactly `revision` and `elapsed_days` for this milestone. `elapsed_days` is an
exact non-negative integer count of full game days since game start. Day zero represents the initial
state.

The stored value is not a date or calendar object. Future calendar concepts must be projections of
elapsed days unless a later accepted decision changes the authority model.

The state ceiling is `2**63 - 1` elapsed days. A single `AdvanceTime` command is capped at
`1_000_000` days. These are defensive numeric limits, not claims about month length, year length,
lifespan, or progression balance.

### Transition contract

`AdvanceTime(days)` is the only current formal command. A legal command produces a distinct state,
increments revision exactly once, increases elapsed days by the requested amount, and emits one
`TimeAdvanced` fact containing the prior time, resulting time, and elapsed amount.

Non-integer, Boolean, non-positive, per-command overflow, and total-time overflow inputs are
expected structured rejections. Time advancement does not consume randomness, but it continues
through the existing transactional session and persists the candidate RNG state unchanged.

The synthetic counter field, commands, event, and rejection reasons are removed from current
contracts. They remain visible only in historical records and the explicit schema-v1 rejection
fixture.

### Save schema v2

The product identity remains `buxianxian-save`. The current envelope schema becomes version 2:

```json
{
  "format": "buxianxian-save",
  "schema_version": 2,
  "state": {
    "elapsed_days": 11,
    "revision": 4
  },
  "random": {
    "algorithm": "xorshift64star",
    "version": 1,
    "state": "0123456789abcdef"
  }
}
```

The strict loader supports v2 only. Experimental v1 saves are returned as unsupported versions;
they are not guessed, silently reinterpreted, or migrated. The xorshift64star v1 state contract and
ADR-004 atomic-write strategy are unchanged.

### Compatibility commitment

Before the first externally playable release, experimental saves may be retired by an explicit
schema change recorded in an ADR and tests. This is not permission to reuse a schema number with a
different meaning.

Starting with the first externally playable release, save compatibility becomes a product
commitment. An incompatible change must define and test a migration or establish an explicit,
user-visible compatibility policy; it must not silently discard or reinterpret released saves.

## Consequences

Positive:

- authoritative state now contains a real foundational gameplay fact rather than a synthetic
  counter;
- future calendar displays can project from one stable monotonic coordinate;
- revision, event, persistence, and application transaction semantics remain explicit;
- save v2 honestly identifies the incompatible state-shape change;
- no fictional migration or calendar system is introduced.

Costs and limits:

- experimental schema-v1 saves no longer load;
- the numeric ceilings become tested domain policy until deliberately revised;
- the current state has time only and is not a complete future player/world model;
- no daily reactions, calendar projection, age, lifespan, schedule, automatic simulation, API, or
  frontend behavior exists.
