# ADR-008: Single-save web runtime and server-owned drafts

- Status: Accepted
- Date: 2026-07-16

## Context

TASK-001 through TASK-006 provide authoritative domain state, deterministic commands, atomic
persistence, transactional sessions, elapsed time, and character creation, but none is reachable
from the browser. The first HTTP slice needs one owner for mutable process state and explicit
transport projections without moving rules into FastAPI or TypeScript.

Character candidates cannot be accepted back from an untrusted browser as authority. A local save
may already exist or be corrupt, and starting a new game must not silently replace it. New games
also need nondeterministic initial entropy while all later domain randomness must remain the
persisted xorshift64star sequence.

The project remains a local, single-user, pre-alpha application. Multiple slots, accounts,
multi-process coordination, and released-save compatibility are not current requirements.

## Decision

### Transport-independent single-game runtime

`SingleGameRuntime` is an application service below FastAPI. One instance owns:

- the configured single-save repository;
- the current `PersistentGameSession`, if any;
- the current opaque draft ID and `CharacterCreationDraft`, if any;
- `NewGameService`;
- the explicit prototype trait catalog;
- injected fresh-RNG and draft-ID sources.

It returns typed application results for save inspection, draft creation, stale drafts, overwrite
requirements, load failures, no-session commands, and existing new-game/session results. It does
not import FastAPI, Pydantic, filesystem implementations, or frontend types.

FastAPI is the concrete composition root: it creates the JSON repository, production sources,
runtime, and route adapter. Tests inject a complete runtime with temporary paths and fixed sources.
Mutable session and draft objects are not distributed among route-module globals.

### Single local save and explicit overwrite

The default path is `runtime-data/buxianxian.save.json` at the repository root. `runtime-data/` is
ignored by Git. `BUXIANXIAN_SAVE_PATH` may override the location for development, tests, or a later
launcher. The path is server configuration and is never accepted from or returned to the browser.

Status distinguishes physical existence from loadability. This allows the browser to hide Continue
for a corrupt/unsupported save while still requiring overwrite consent before new-game creation.

If any entry occupies the configured save path, confirmation without
`overwrite_existing_save=true` returns a stable conflict. With consent, the existing atomic JSON
repository replaces the file. A prior active session is replaced only after the new state and RNG
save succeeds.

### Server-owned ephemeral draft

The server retains at most one draft. Creating another draft invalidates the previous one and
returns a new opaque ID. Confirmation sends only that ID, player name, aptitude option ID, two trait
IDs, and overwrite consent; the application uses the retained draft to revalidate selections.

Validation or save failure retains the valid draft for correction/retry. Successful new-game
creation or successful save loading invalidates it. Drafts are not player state, are never saved,
and intentionally disappear on process restart.

Opaque IDs use `secrets.token_urlsafe` and are outside game determinism. The browser never sees the
candidate RNG snapshot.

### Initial entropy and persisted randomness

Production draft creation obtains a 64-bit seed from `secrets.randbits`; the zero outcome is mapped
to one to satisfy the xorshift64star invariant. This OS entropy is used only to construct a fresh
game RNG. Candidate generation and all future domain randomness continue through the existing
deterministic source, whose exact post-generation state is saved with the new game.

Tests inject fixed factories. Python global `random` is not used in domain rules.

### Prototype traits

The first web slice includes eight explicitly labelled pre-alpha trait definitions in a product
configuration module. They provide only stable IDs, Chinese display names, and short statements
that they have no current rule effects. They do not introduce rarity, balance, conflicts,
conditions, or an effect DSL.

Selected stable IDs remain authoritative state. The API projects display metadata from the current
catalog and tolerates missing prototype metadata without mutating the save.

### HTTP projection and errors

FastAPI request/response models are strict transport DTOs, not domain models. Routes invoke the
application runtime and project complete server state. The browser never computes an authoritative
aptitude, elapsed day, revision, or command result.

Expected failures use an exact envelope with machine code, Chinese message, optional field context,
and optional current state. Request validation is normalized to the same envelope. Paths, RNG
identity/state, exception class names, tracebacks, and raw system messages are never returned.

The first routes are:

- `GET /api/game`;
- `POST /api/game/drafts`;
- `POST /api/game/new`;
- `POST /api/game/load`;
- `POST /api/game/wait`.

## Consequences

Positive:

- the browser can exercise existing authoritative contracts end to end;
- one application object owns mutable lifecycle and is independently testable;
- untrusted clients cannot forge candidate contents or directly modify saves;
- overwrite, conflict, domain rejection, and persistence failure remain distinct;
- restart recovery preserves complete state and exact persisted RNG position;
- no dependency, framework, domain rule, or save-format change is required.

Costs and limits:

- only one process-local session, one draft, and one save location are supported;
- no lock protects simultaneous requests, and multiple worker processes are unsupported;
- drafts disappear on restart and cannot be shared across processes;
- prototype trait IDs and save schema v3 remain pre-alpha contracts that may change before the first
  external playable release;
- there is no authentication, remote exposure policy, multiple slot UI, delete/import/export,
  content reader, desktop wrapper, or additional gameplay.

