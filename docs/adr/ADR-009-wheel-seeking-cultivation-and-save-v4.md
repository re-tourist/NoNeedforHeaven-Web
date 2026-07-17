# ADR-009: Wheel-seeking cultivation and save v4

- Status: Accepted
- Date: 2026-07-17

## Context

The authoritative state, deterministic RNG, transactional session, single-save API, and browser
client can already create, persist, load, inspect, and advance a game. The first real cultivation
action must combine gameplay progress, elapsed time, randomness, events, and persistence without
breaking those boundaries.

The product source describes `寻轮` and later `见轮三验`. TASK-008 deliberately ends at the
preliminary `疑见生命之轮` milestone; it does not claim the three trials or completion of seeking.
The project is pre-alpha and has no externally supported schema-v3 saves.

## Decision

### Authoritative cultivation state

Every immutable `GameState` contains `CultivationState`:

- stage is currently only `seeking_wheel`;
- wheel insight is an exact integer from 0 through 100;
- status is `seeking` below 100 and `suspected_sighting` at 100.

The threshold and all balance constants are centralized domain constants. They are pre-alpha tuning
values, not content, API, or frontend rules. New games begin with zero insight and `seeking`.

### One atomic command

`SeekWheel(max_days)` accepts exact integers from 1 through 30. The domain settles one day at a time
and stops immediately after reaching suspected sighting. One accepted command atomically:

- applies all insight gain;
- advances elapsed days by the actual settled days;
- changes suspected-sighting status when applicable;
- increments revision exactly once;
- emits one aggregate `WheelSeekingCompleted` event.

Calling `AdvanceTime` after applying cultivation effects is prohibited. Persistence still evaluates
on a forked RNG and commits state plus RNG only after the atomic save succeeds.

### Deterministic daily rule

Every actual day consumes exactly two inclusive-integer RNG calls, in fixed order:

1. subtle-sense roll from 1 through 10;
2. inspiration roll from 1 through 100.

Daily ordinary insight is:

```text
1 + floor(comprehension / 3) + floor(temperament / 5)
+ 1 when subtle_sense_roll <= spiritual_sense
```

Daily inspiration is:

```text
3 + floor(comprehension / 5)
when inspiration_roll <= fortune * 2, otherwise 0
```

The total is capped at 100. Both draws occur before the daily gain is applied; no unused draws are
introduced after reaching the threshold. Constitution and prototype traits intentionally have no
effect in this first rule. Integer arithmetic, bounded calls, and fixed ordering make one seven-day
command equivalent to seven one-day commands for time, insight, milestone status, and final RNG
position, aside from revision count and event grouping.

### Save schema v4

The product identity remains `buxianxian-save`. Schema 4 preserves player, time, revision, and
`xorshift64star` v1 state and adds an exact cultivation object:

```json
{
  "cultivation": {
    "stage": "seeking_wheel",
    "wheel_insight": 0,
    "wheel_status": "seeking"
  }
}
```

The loader reconstructs and validates the domain invariants. Experimental schemas v1 through v3
are unsupported rather than assigned invented cultivation progress. The first externally playable
release remains the start of the formal save-compatibility commitment.

### Transport projection

FastAPI exposes `POST /api/game/cultivation/seek-wheel` with `max_days` and
`expected_revision`. Success returns the complete authoritative state and the aggregate action
summary. Expected failures remain typed as no session, revision conflict, cultivation rejection, or
persistence failure. Paths and RNG state remain private.

The vanilla TypeScript client projects the server-owned threshold and result. It never recalculates
insight, elapsed time, status, or revision.

## Consequences

Positive:

- cultivation, time, RNG, revision, event, and save share one transaction;
- deterministic daily settlement is transparent, bounded, and split/merge consistent;
- save failure, conflict, and domain rejection cannot advance official state or RNG;
- the browser exposes a real playable action without duplicating domain rules.

Costs and limits:

- the formula and threshold are intentionally provisional;
- schema-v3 pre-alpha saves no longer load;
- constitution and traits have no current seeking effect;
- suspected sighting is not completion of seeking;
- breath, pain, and dream trials, later stages, multiple methods, resources, injuries, and other
  cultivation systems remain unimplemented.
