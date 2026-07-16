# ADR-004: Versioned snapshot saves and xorshift64star state

- Status: Superseded in part by ADR-006
- Date: 2026-07-15

ADR-006 supersedes only the experimental schema-v1 state shape and current-version statement.
Snapshot authority, random compatibility, JSON safety, version dispatch, and atomic replacement
remain accepted.

## Context

The P2 domain kernel has an authoritative immutable state snapshot and an injected random-source
boundary. P3 needs to preserve both across a process restart without coupling domain models to
files, JSON libraries, Python runtime internals, or an event-replay design that does not yet exist.

The persisted representation becomes a long-lived compatibility contract. It must identify the
product and format version, reject unknown data clearly, and remain interpretable without executing
arbitrary Python objects.

## Decision

### Snapshot authority

The complete `GameState` snapshot remains the authority for current facts. Domain events continue
to explain accepted transitions but are not the only source from which state can be reconstructed.
TASK-002 does not persist or replay events.

### Save envelope and versions

The first save format is UTF-8 JSON with this explicit shape:

```json
{
  "format": "buxianxian-save",
  "schema_version": 1,
  "state": {
    "revision": 4,
    "counter": 11
  },
  "random": {
    "algorithm": "xorshift64star",
    "version": 1,
    "state": "0123456789abcdef"
  }
}
```

The schema version governs the complete envelope. Loaders dispatch on the recognized integer
version before decoding version-specific data. Unknown versions are rejected; loaders must never
guess. A future old-version loader may validate and transform its representation into then-current
in-memory contracts, but no fictional v0 or migration is implemented now.

The v1 decoder is strict: required fields, types, and object shapes must match. A shape change that
cannot be read under those rules requires an intentional schema-version decision.

### Random compatibility

The concrete source is `xorshift64star` state version 1. It uses the xorshift64* transition with
unsigned 64-bit masking and multiplier `2685821657736338717`. The constructor treats a nonzero
64-bit seed as the initial internal state. Bounded integers use rejection sampling rather than
biased modulo reduction.

The state is stored as exactly 16 lowercase hexadecimal digits. This avoids the precision limit of
JSON numbers in some runtimes and makes the state portable and inspectable. The algorithm name,
state version, transition, output mapping, and seed interpretation together form the compatibility
contract. Any incompatible change requires a new random-state version or algorithm identity.

The source is non-cryptographic. It is selected for a small stable state and an implementation that
can be independently specified and tested, not as a claim that it is the final algorithm for every
future simulation requirement.

### Serialization and file replacement

The persistence adapter lives outside `buxianxian.domain`. It validates JSON with explicit standard
library mappings and reconstructs domain objects through their public constructors.

Saving writes a complete temporary file in the destination directory, flushes and `fsync`s it,
closes it, and uses `os.replace` to replace the target. A write or replacement failure is reported
through a structured persistence error and cleanup is attempted without deleting the previous
valid target.

`pickle` is prohibited because it is opaque, Python-specific, unsafe for untrusted input, and not
a stable schema. Python `random.getstate()` is also prohibited because it would make an internal
runtime representation the project's persisted compatibility contract.

## Consequences

Positive:

- state and random progress survive restart deterministically;
- save data is inspectable and strictly versioned;
- domain purity and Python authority remain intact;
- corruption and compatibility failures have stable machine-readable categories;
- atomic replacement protects the previous complete save during ordinary write failures.

Costs and limits:

- the RNG sequence is now a compatibility obligation covered by a frozen known-vector test;
- v1 stores the current synthetic state shape and must evolve when the real state model evolves;
- only xorshift64star v1 and save schema v1 are supported;
- the portable strategy flushes the temporary file but does not promise directory-metadata durability
  across every possible power-loss/filesystem combination;
- replay logs, event persistence, backup rotation, slot management, and migrations remain future work.
