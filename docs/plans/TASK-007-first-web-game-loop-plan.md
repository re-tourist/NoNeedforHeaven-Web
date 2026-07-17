# TASK-007 First Operable Web Game Loop ExecPlan

## 1. Objective

Ship the first browser-operable vertical slice over the existing authoritative Python contracts:
inspect a single save, create and confirm a server-owned character draft, load a saved game, render
the complete player/time read model, and commit bounded waiting through revision-protected HTTP.

## 2. Scope

Included:

- one application runtime owning the repository, active session, current draft, new-game service,
  prototype trait catalog, and injected RNG/draft-ID factories;
- environment-configurable single-save path under ignored local runtime data by default;
- OS-secure nonzero initial seed and opaque draft identifiers outside deterministic game RNG;
- five typed FastAPI game endpoints, strict DTOs, and stable error envelopes;
- an eight-entry pre-alpha prototype trait catalog with no effects;
- vanilla TypeScript transport validation, pure UI controller/state machine, responsive DOM views,
  busy/error feedback, selection constraints, explicit overwrite consent, and conflict refresh;
- backend API/application integration tests, frontend state/transport tests, restart recovery proof;
- ADR-008 plus API, frontend, runtime, status, task, and developer documentation.

Excluded:

- domain state/command/event changes, save schema changes, content-runtime integration, migrations,
  replay, multiple slots, delete/import/export, autosave policy, user accounts, or concurrency locks;
- UI frameworks, route libraries, state-management frameworks, browser automation, images, animation,
  formal art, or audio;
- trait effects and all additional gameplay, narrative, authoring, desktop, or LLM work.

## 3. Existing context

TASK-006 is committed as `ca4f8e6` and pushed to `origin/main`; local and remote main match and the
post-push tree is clean. Its pre-change quality gate passes 103 backend tests, three frontend tests,
all format/lint/type checks, content validation, and the Vite production build.

The API currently constructs FastAPI in `buxianxian.api.app` and exposes only `/api/health`. The
frontend is four small files that validate health and render one connection panel. FastAPI,
Pydantic, Vite, TypeScript, and Vitest are already installed; no dependency addition is necessary.

`NewGameService` already guarantees candidate RNG isolation and save-before-session creation.
`PersistentGameSession` already guarantees revision checking, candidate evaluation, save-before-
memory-commit, and rollback. `JsonFileSaveRepository` already provides strict schema-v3 validation
and atomic replacement, but its application port has no existence probe and there is no owner for
session/draft lifecycle yet.

## 4. Proposed design

### Application runtime

`SingleGameRuntime[RandomT]` is a transport-independent application service. It receives a
single-save repository, transactional RNG factory, opaque ID source, and explicit trait catalog. It
owns at most one active session and one `(draft_id, CharacterCreationDraft)` pair.

The repository port gains a narrow `exists()` capability through a new extended protocol; existing
session/new-game ports remain unchanged. The concrete JSON repository implements it without
exposing its path.

Runtime results are frozen typed values for status, draft creation, stale draft, overwrite required,
load success/failure, no active session, and existing session/new-game outcomes. Routes branch on
types, never exception text.

### Random and draft identities

The production RNG factory uses `secrets.randbits(64)` and maps the vanishing zero case to one before
constructing xorshift64star v1. It is used once per new draft. The deterministic game RNG remains
the only source used by domain creation and is persisted after candidate generation.

Draft IDs use `secrets.token_urlsafe` and are never persisted or returned with candidate RNG state.
Tests inject fixed factories and sequential IDs. A new draft clears the prior draft before
generation; validation/save failure retains the current valid draft; success or successful load
clears it. Process restart intentionally loses it.

### Single-save configuration and overwrite

The default save is `<repository>/runtime-data/buxianxian.save.json`, a Git-ignored path derived
relative to the local package checkout rather than a developer absolute path. `BUXIANXIAN_SAVE_PATH`
may replace it. The browser never submits or receives a path.

Confirmation checks the server-held draft first, then refuses any existing filesystem entry unless
`overwrite_existing_save` is true. The existing atomic repository performs the replacement. The
old active session remains authoritative until a replacement save succeeds.

### API contract

Routes:

- `GET /api/game` — save existence/loadability, active-session flag, optional state/error;
- `POST /api/game/drafts` — new opaque draft and server-generated candidates;
- `POST /api/game/new` — draft ID plus name/choice IDs and overwrite consent;
- `POST /api/game/load` — validate/load the configured single save;
- `POST /api/game/wait` — `days` plus `expected_revision`.

Strict Pydantic request/response DTOs are projections rather than domain models. Errors use an exact
`{"error": {"code", "message", "fields"}, "state": ...}` envelope. Request validation is also
normalized to this envelope. Save errors map by stable `SaveErrorCode`; internal paths, exception
types, tracebacks, RNG algorithm/state, and candidate RNG snapshots are omitted.

### Prototype trait projection

An explicit infrastructure/product-config module provides eight clearly labelled pre-alpha trait
definitions with neutral Chinese names/descriptions and no effects. The runtime owns the catalog.
API read models resolve stored IDs against it for display; IDs remain the only authoritative player
state. Missing display metadata degrades to an unknown-prototype label rather than changing state.

### Frontend state machine

`HttpGameApi` validates unknown JSON into typed transport contracts and throws `ApiClientError`
with stable code/message and optional current state. `GameController` owns a discriminated union:
`booting`, `start`, `creating`, or `overview`, with explicit busy and recoverable error fields.

The controller never computes authoritative aptitudes, time, or revision. It only manages form
selection, submits the current server IDs/revision, and replaces displayed state from responses. A
revision conflict adopts the server-provided current state and does not auto-retry.

Vanilla DOM render functions provide accessible controls and clear Chinese copy. Vitest tests the
controller and transport contracts without adding jsdom or browser automation.

### Alternatives considered

- Route-module global session/draft values were rejected because lifecycle and tests would be
  fragmented.
- Putting filesystem checks and concrete RNG construction in routes was rejected because it would
  mix composition and transport mapping.
- Persisting drafts was rejected because drafts are pre-session UI workflow, not authoritative game
  state.
- A UI framework, router, store, and Playwright were rejected because the current state surface is
  small and existing Vitest can prove controller behavior.

## 5. Milestones

### Milestone A: application runtime and infrastructure composition

Affected files: application ports/runtime/exports, JSON repository, runtime sources, prototype
catalog, and application tests.

Expected behavior: one typed owner coordinates save inspection, draft replacement, overwrite,
new-game success/failure, load, wait, and restart recovery without transport dependencies.

Validation: focused Ruff, Pyright, application/infrastructure tests, and existing boundary tests.

Recovery: no route or frontend is connected until the headless composition passes; tests use temp
paths and fixed sources.

### Milestone B: FastAPI transport and integration tests

Affected files: API contracts/routes/composition/app and API tests.

Expected behavior: all five routes project stable DTOs/errors, preserve application/domain
authority, and never leak paths/RNG/internal exceptions.

Validation: focused API tests through `TestClient`, including overwrite, corruption/version errors,
conflict, persistence failure, and restart reload.

Recovery: `/api/health` remains; the router is composed with an injected runtime for isolation.

### Milestone C: browser client and frontend tests

Affected files: TypeScript API client/controller/main/styles and Vitest tests.

Expected behavior: the complete user flow is keyboard-operable, responsive, busy-safe, error-aware,
and refreshed only from server responses.

Validation: Prettier, ESLint, TypeScript, focused/all Vitest, and Vite build.

Recovery: no dependency or persistent browser storage is introduced; views can be reverted without
affecting backend contracts.

### Milestone D: decisions, documentation, and final acceptance

Affected files: ADR-008, architecture/status/roadmap, READMEs, API/frontend docs, TASK-007 record,
and this plan.

Expected behavior: setup, save path override, draft lifetime, overwrite behavior, API boundary, and
known limitations match actual commands and code.

Validation: complete backend/frontend checks, content validation, `git diff --check`, manual local
browser flow, restart proof, artifact/secret/dependency/scope scans.

Recovery: no real save used for tests or manual verification may remain in the repository.

## 6. Progress log

- [x] 2026-07-16: Audited TASK-006 scope, ran full backend/frontend/content checks, scanned artifacts
  and secrets, committed `ca4f8e6`, pushed it, and confirmed clean local/remote equality.
- [x] 2026-07-16: Read governance, project status, architecture, roadmap, ADR-001 through ADR-007,
  TASK-001 through TASK-006 records/plans, current source/tests, dependencies, and developer docs.
- [x] 2026-07-16: Reported the bounded application/API/frontend design before implementation.
- [x] 2026-07-16: Implemented and verified the single-game application runtime and concrete inputs.
- [x] 2026-07-16: Implemented and verified FastAPI routes and stable error projection.
- [x] 2026-07-16: Implemented and verified the browser state machine and responsive views.
- [x] 2026-07-16: Recorded ADR-008 and synchronized API/frontend/runtime/status documentation.
- [x] 2026-07-17: Completed isolated Edge acceptance with fresh browser profiles before and after
  backend restart; created a character, advanced three days, and restored the same complete state.
- [x] 2026-07-17: Re-ran all backend/frontend/content checks and completed the final Git
  scope/artifact/secret review with no generated runtime data or dependency changes.

## 7. Discoveries and deviations

- No new dependency is required. Existing FastAPI/Pydantic and Vite/TypeScript/Vitest cover the
  complete slice.
- Save inspection needs both physical existence and loadability so the UI can distinguish a valid
  Continue action from a corrupt file that still requires explicit overwrite consent.
- The frontend test environment has no DOM implementation. A pure controller plus thin DOM renderer
  provides stronger state-transition tests without adding jsdom.
- Strict Pydantic tuple input rejects JSON arrays under `strict=True`; the request DTO therefore
  accepts a JSON-native `list[str]` and immediately passes it into the existing validating
  application/domain boundary. Response collections remain immutable tuples.
- FastAPI decorated nested closures appear unused to strict Pyright. Explicit `add_api_route`
  registration preserves injected runtime closure ownership and makes usage statically visible.
- Real Edge acceptance exposed that storing bare native `fetch` and invoking it through a class
  field binds the API client as its receiver. A default arrow wrapper now calls browser `fetch`
  without that invalid receiver; a frontend regression test preserves the boundary.

## 8. Verification

Step 0 baseline:

```text
backend Ruff format/lint, Pyright            -> passed
backend pytest                               -> 103 passed
published content validate                   -> 0 entries
frontend Prettier/ESLint/TypeScript           -> passed
frontend Vitest                              -> 3 passed
frontend Vite build                          -> passed
TASK-006 commit/push                          -> ca4f8e6 on local and origin/main
post-push tree                                -> clean
```

TASK-007 automated verification:

```text
backend Ruff format --check --no-cache .       -> passed; 42 files formatted
backend Ruff check --no-cache .                -> passed
backend Pyright                                -> passed; 0 errors, 0 warnings
backend pytest -p no:cacheprovider             -> passed; 125 tests
published content validate                     -> passed; 0 entries
frontend Prettier/ESLint/TypeScript             -> passed
frontend Vitest                                -> passed; 18 tests
frontend Vite production build                 -> passed
```

Manual browser verification on 2026-07-17:

```text
fresh Edge profile, no save                    -> 不羡仙 rendered; only New Game shown
server draft                                   -> 3 aptitude choices; 6 trait choices
incomplete form                                -> confirmation disabled
confirmed new game                             -> 验收角色; day 0; revision 0
wait 3 days                                    -> day 3; revision 1
backend stopped and restarted                  -> successful
second fresh Edge profile                      -> Continue shown; same player/aptitudes/traits/day/revision
browser network evidence                       -> API responses not from disk cache, service worker,
                                                  or prefetch cache
temporary save/browser profiles                -> removed by the acceptance harness
```

The final automated rerun passes after the browser-found `fetch` regression fix. Git scope,
artifact, and secret verification also pass.

## 9. Completion summary

The implementation now provides one complete authoritative web loop from server-owned character
draft through atomic new-game save, overview projection, revision-protected wait, and restart load.
No new dependency, domain command, save schema, content integration, or additional gameplay was
introduced. Manual browser/restart acceptance, final automated rerun, and repository-scope evidence
are complete.
