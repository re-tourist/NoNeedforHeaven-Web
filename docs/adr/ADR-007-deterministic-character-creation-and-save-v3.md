# ADR-007: Deterministic character creation and save v3

- Status: Accepted
- Date: 2026-07-16

## Context

TASK-005 introduced authoritative elapsed-day time, but its intentionally minimal `GameState` had no
player. A formal session now needs a complete immutable player profile without representing the
character-creation screen as nullable or half-initialized game state.

Character creation consumes deterministic randomness before a session exists. The player must be
able to inspect generated choices and submit a later confirmation, while validation failure and
initial-save failure must not corrupt RNG position or expose a session that has not been persisted.

The project still has no released saves or formal product trait catalog. Schema v2 therefore cannot
be assigned invented player data, and test traits must not become product lore or balance.

## Decision

### Complete formal player state

`GameState` requires `revision`, `elapsed_days`, and one immutable `PlayerCharacter`. A formal state
without a player is invalid.

`PlayerCharacter` contains:

- an NFC-normalized, trimmed player name of 1 through 32 Unicode code points with Unicode control
  characters (`Cc`) and isolated surrogate code points (`Cs`) rejected;
- one `InnateAptitudes` value;
- exactly two distinct stable trait IDs in canonical sorted tuple order.

`InnateAptitudes` contains `constitution`, `comprehension`, `spiritual_sense`, `temperament`, and
`fortune`. Every value is an exact integer from 1 through 10 and the total is exactly 25. These are
opening growth tendencies, not a complete combat-stat or power-ranking model.

### Deterministic aptitude generation

The domain enumerates every ordered five-value distribution that satisfies the aptitude bounds and
total. The enumeration order is lexicographic and independent of filesystems, mappings, or sets.

Three distinct distributions are selected with a partial Fisher-Yates sample over indices using the
injected `RandomSource`. This performs exactly three bounded draws, has no retry loop, and samples
uniformly over the valid ordered distributions when the random source fulfills its unbiased
inclusive-integer contract.

Generated aptitude options receive candidate-local IDs. Confirmation selects one ID; callers cannot
submit arbitrary aptitude values and ask the domain to trust them.

### Trait catalog and selection

The creation boundary accepts an explicit caller-provided sequence of `TraitDefinition(id, name,
description)`. IDs use stable lowercase ASCII machine form. Names and descriptions are clean,
non-empty display strings. Definitions must have unique IDs.

The catalog is sorted by ID and six distinct definitions are selected through six more bounded
partial-Fisher-Yates draws. Confirmation requires exactly two distinct IDs from that candidate pool.
Stored IDs are sorted so UI selection order has no hidden rule meaning.

No production trait catalog, effect language, rarity, conflict rule, level, budget, or content
compiler schema is introduced.

### Two-stage pre-session application boundary

`NewGameService` owns the application workflow:

1. `begin` forks the caller RNG and generates candidates on the fork.
2. A `CharacterCreationDraft` retains immutable candidates and the private post-generation RNG
   position.
3. `confirm` revalidates name and selections without consuming RNG.
4. A defensive fork at the draft position is saved with the complete initial state.
5. `PersistentGameSession` is created only after persistence succeeds.

Generation failure discards the candidate fork. Confirmation failure does not fork or save. Save
failure returns a structured `InitialSaveFailed`, exposes no session, and leaves the draft available
for deterministic retry. No logic counts or reverses random draws.

Structured error codes distinguish invalid name, aptitude selection, trait count, duplicate trait,
unoffered trait, insufficient/invalid catalog, invalid candidate contract, and RNG contract failure.

### Save schema v3

The product identity remains `buxianxian-save`. Schema 3 stores complete player, time, revision, and
xorshift64star v1 state:

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

The loader is strict. Experimental schemas v1 and v2 are unsupported rather than assigned guessed
player data. ADR-006's compatibility commitment beginning with the first externally playable
release remains in force.

### Atomic time composition

`AdvanceTime` remains a command for a direct time skip. It is not a reusable second transaction for
all future activities.

A future cultivation, travel, work, crafting, or other time-consuming command must apply its
gameplay effects and elapsed-day change in one domain transition and one persisted state commit.
Submitting an effect command and then a separate `AdvanceTime` would permit partial success and is
prohibited.

## Consequences

Positive:

- every formal game state contains one complete immutable player;
- candidate generation is deterministic, bounded, testable, and independent of global random;
- player confirmation cannot forge aptitude values or traits outside its candidate pool;
- initial state and exact post-generation RNG position commit together before a session exists;
- save v3 strictly reconstructs player identity, aptitudes, trait IDs, time, and RNG;
- future time-consuming mechanics have an explicit atomic-composition rule.

Costs and limits:

- experimental schema-v2 saves no longer load;
- candidate drafts are in-memory application objects and are not resumable across process restart;
- there is no formal trait catalog or trait behavior yet;
- no reroll policy, API, frontend, character appearance, age, gender, origin, location, cultivation,
  inventory, combat, narrative, or other gameplay capability exists.
