# TASK-008 Wheel-Seeking Cultivation Vertical Slice ExecPlan

## 1. Objective

Ship the first browser-operable cultivation action over the existing authoritative state,
deterministic RNG, atomic session, single-save API, and vanilla TypeScript client:

```text
active game + SeekWheel(max_days) + candidate RNG
    -> daily deterministic settlement until requested days or suspected sighting
    -> atomic state/time/RNG save
    -> complete server projection and browser result
```

The slice ends at `SUSPECTED_SIGHTING`. The three sighting trials and every later cultivation realm
remain absent.

## 2. Scope

Included:

- immutable cultivation state in every formal `GameState`;
- one `SeekWheel(max_days)` command accepting exact integers from 1 through 30;
- one centralized pre-alpha threshold and integer-only daily settlement;
- exactly two deterministic RNG calls for every actual cultivation day;
- one summarized domain event per accepted command;
- atomic insight, status, elapsed-day, revision, RNG, and persistence commit;
- strict `buxianxian-save` schema v4 with complete cultivation state;
- one application-runtime command entry and one FastAPI cultivation route;
- full state plus cultivation-result HTTP projection and stable expected errors;
- lightweight Overview/Cultivation navigation, progress, 1/7/30-day controls, busy/error state, and
  last-result display;
- domain, persistence, application, API, frontend, restart, and browser acceptance coverage;
- ADR-009 plus architecture, API, status, roadmap, task, and developer documentation.

Excluded:

- the breath, pain, and dream sighting trials or formal completion of wheel seeking;
- breakthrough, Wheel-and-Sea, Life Spring, later realms, generic progression trees, or multiple
  methods;
- mana, combat attributes, injury, lifespan, deviation, pills, resources, inventory, storage,
  locations, environments, trait effects, or an effect DSL;
- runtime-content reading, formal authored content, private Obsidian material, art, desktop
  packaging, or LLM behavior;
- save migration from experimental schema v3, event persistence, replay, or new concurrency work.

## 3. Existing context

TASK-007 is committed as `0be9361`, pushed to `origin/main`, and the worktree is clean. Its final
gate passes 125 backend tests, 18 frontend tests, all format/lint/type/content/build checks, and a
fresh-profile Edge create/wait/restart/continue flow.

Current formal state requires revision, elapsed days, and a complete immutable player. The only
domain command is `AdvanceTime`. `PersistentGameSession` already forks the official RNG, evaluates
one pure transition, saves candidate state and RNG, and commits memory only after persistence
succeeds. `SingleGameRuntime` and FastAPI already distinguish no session, conflict, domain
rejection, and persistence failure.

Save schema v3 strictly stores player, time, revision, and xorshift64star v1 state. No released
player save requires migration. ADR-006 and ADR-007 permit an explicit pre-alpha schema retirement
without reusing a version number.

The browser state is a small discriminated union with one `overview` gameplay state. It replaces
authoritative state only from server responses and already adopts a returned state on revision
conflict.

The private author document describes seeking through bodily settling, even breathing, inward
attention, guarded stillness, and a later three-trial verification. It remains outside the
repository and runtime. This task's approved product contract treats the threshold as a preliminary
suspected sighting and defers all three trials.

## 4. Proposed design

### Cultivation state and invariants

`CultivationState` contains:

- `stage = CultivationStage.SEEKING_WHEEL`;
- `wheel_insight`, an exact integer from 0 through 100;
- `wheel_status = SEEKING` while insight is below 100;
- `wheel_status = SUSPECTED_SIGHTING` exactly when insight is 100.

The suspected-sighting threshold is the centralized pre-alpha constant
`WHEEL_SUSPECTED_SIGHTING_THRESHOLD = 100`. The redundant explicit status is intentional because it
is a player-visible domain fact and is validated against insight rather than inferred separately by
API or frontend code.

Every new character starts at revision 0, elapsed day 0, stage Seeking Wheel, zero insight, and
status Seeking. `AdvanceTime` preserves cultivation state unchanged.

### Daily settlement and RNG contract

Every actual cultivation day consumes exactly two inclusive-integer calls in this order:

1. `subtle_sense_roll = integer_inclusive(1, 10)`;
2. `inspiration_roll = integer_inclusive(1, 100)`.

Ordinary daily insight is:

```text
1
+ comprehension // 3
+ temperament // 5
+ (1 if subtle_sense_roll <= spiritual_sense else 0)
```

Occasional inspiration is:

```text
3 + comprehension // 5
```

when `inspiration_roll <= fortune * 2`, otherwise zero.

All values are integers. Comprehension raises the dependable and inspired gain, spiritual sense
raises subtle-capture frequency, temperament raises the dependable floor, and fortune raises a
bounded 2% through 20% inspiration chance. Constitution is deliberately unused in this first
wheel-seeking rule. Trait IDs remain display-only.

The constants and formula live in one domain rules module and are explicitly pre-alpha balance.
There are no retry loops, floating probabilities, global randomness, file order, or set iteration.
The day consumes both calls before gain is applied. Insight caps at 100; reaching it ends the
command immediately and consumes no later day's RNG.

This fixed daily order makes one seven-day command and seven one-day commands core-equivalent for
elapsed time, insight, status, and final RNG position until suspected sighting. Revision and event
grouping intentionally differ.

### Command, event, and rejection

`SeekWheel(max_days)` requests at most 1 through 30 days. Accepted settlement produces one
`WheelSeekingCompleted` event containing requested and actual days, insight before/after, ordinary
and inspiration totals, whether this command reached suspected sighting, and game time before/after.
Revision increments once regardless of actual days.

Invalid type/non-positive days, days above 30 or total-time overflow, and an already suspected
sighting return distinct structured reasons. Rejection preserves state and candidate RNG.
Violations of the injected RNG protocol remain programmer-contract failures rather than expected
player errors.

### Save schema v4

Schema v4 retains format `buxianxian-save`, player/time/revision, and xorshift64star v1, and adds an
exact `cultivation` object below state:

```json
{
  "stage": "seeking_wheel",
  "wheel_insight": 0,
  "wheel_status": "seeking"
}
```

The v4 decoder validates exact fields and reconstructs the domain value. Experimental v1-v3 saves
are unsupported; no guessed cultivation state or fictional migration is added. Atomic replacement
and RNG serialization remain unchanged.

### Application and API

`SingleGameRuntime.seek_wheel(max_days, expected_revision)` delegates one typed command to the
unchanged transactional session. The route is `POST /api/game/cultivation/seek-wheel`.

Success returns:

- the complete game projection, including cultivation stage, status, insight, and server-projected
  threshold;
- one cultivation summary projected from the committed domain event.

Expected results remain no session, revision conflict with refresh state, command rejection with
refresh state, and persistence failure with unchanged refresh state. New API code
`cultivation_command_rejected` is stable. No path, RNG state, or domain implementation object is
exposed.

### Frontend state and view

The existing gameplay controller keeps one authoritative `GameStateView`, a presentation page
(`overview` or `cultivation`), optional last cultivation result, busy flag, and recoverable error.
Navigation is local presentation state only.

`seekWheel` submits the current revision and a 1/7/30-day intent. Success replaces state and recent
result from the response. Conflict adopts the returned authoritative state without blind retry.
Other failures clear busy state and keep the current usable page.

The Cultivation view shows the approved method/stage labels, insight and server threshold,
accessible progress, status, preset buttons, last summary, the deferred-three-trials notice, and
the explicit note that prototype traits have no current effect. No router, UI framework, store, or
dependency is added.

### Alternatives considered

- Deriving status only from insight was rejected because the approved contract asks for an explicit
  stage/status fact and persistence validation benefits from detecting inconsistent saves.
- A random number of calls or retry-until-success rule was rejected because it would make sequence
  progress and batch equivalence opaque.
- Calling `AdvanceTime` after a cultivation transition was rejected because ADR-007 requires
  gameplay and time to commit atomically.
- Per-day events were rejected because one summarized accepted action is sufficient and the project
  does not persist events.
- Trait interpretation, a method plugin, or generic progression framework was rejected as
  premature.

## 5. Milestones

### Milestone A: domain state and deterministic settlement

Affected files: domain model/rules/engine/exports, character creation, and domain tests.

Expected behavior: valid initialization, bounded daily formula, fixed RNG consumption, immutable
atomic success, all rejections, early stop, attribute effects, and batch equivalence.

Validation: focused Ruff/Pyright and domain tests, including deterministic controlled sequences and
bounded gain cases.

Recovery: no persistence or transport file changes until pure rules pass.

### Milestone B: save v4 and application transaction

Affected files: JSON save repository, runtime entry, exports, persistence/application tests.

Expected behavior: strict cultivation round-trip, v3 rejection, complete restart recovery, conflict
and rejection with no RNG/write, save failure rollback, deterministic retry.

Validation: focused persistence/session/runtime suites and existing RNG atomic-write tests.

Recovery: RNG algorithm/state format and session commit algorithm remain unchanged.

### Milestone C: API and frontend vertical slice

Affected files: HTTP contracts/routes/docs/tests and frontend transport/controller/DOM/style/tests.

Expected behavior: one stable cultivation endpoint, full authoritative projection, Overview and
Cultivation views, preset actions, progress/result/error/busy behavior, and suspected-sighting stop.

Validation: focused API tests plus frontend Prettier, ESLint, TypeScript, Vitest, and Vite build.

Recovery: the existing new/load/wait routes and start/creation/overview flow remain operational.

### Milestone D: decisions, docs, final acceptance, and Git

Affected files: ADR-009, architecture/status/roadmap/READMEs, TASK-008 record, and this plan.

Expected behavior: active documentation matches formula, RNG, schema, API, UI, and explicitly
deferred trials.

Validation: complete backend/frontend/content checks, `git diff --check`, dependency/secret/
artifact/private-content/scope scans, isolated browser create-seek-restart-continue-seek flow,
commit, push, remote equality, and clean tree.

Recovery: all browser and save profiles use verified paths under `C:\tmp` and are removed.

## 6. Progress log

- [x] 2026-07-17: Completed TASK-007 real Edge acceptance, full checks, scope review, commit
  `0be9361`, push, local/remote equality, and clean-tree verification.
- [x] 2026-07-17: Read governance, status, roadmap, architecture, ADR-001 through ADR-008, prior task
  records/plans, the relevant private source excerpt, and current domain/application/save/API/
  frontend code and tests.
- [x] 2026-07-17: Reported the bounded state, formula, schema-v4, API, frontend, and verification plan
  before implementation.
- [x] 2026-07-17: Implemented and verified domain state, deterministic daily settlement, early
  stopping, aggregate event, and split/merge consistency.
- [x] 2026-07-17: Implemented and verified save v4 plus application conflict/rejection/failure
  transaction behavior and restart continuation.
- [x] 2026-07-17: Implemented and verified the strict cultivation API projection and vanilla
  TypeScript overview/cultivation slice.
- [x] 2026-07-17: Recorded ADR-009, task/status/API/architecture/developer documentation, and ran
  the complete backend/frontend automated checks.
- [x] 2026-07-17: Completed isolated Edge acceptance from an empty save through restart recovery,
  continued seeking, and suspected-sighting UI lockout; temporary processes and files were removed.
- [x] 2026-07-17: Completed final scope audit and Git closure with the required commit message;
  verified remote equality and a clean worktree.

## 7. Discoveries and deviations

- The user-approved TASK-008 contract intentionally places a preliminary suspected sighting before
  the three trials, while the private source wording describes the trials before its strongest
  confirmation language. The implementation follows the explicit task boundary and does not encode
  the trials or copy source text.
- The existing session transaction and RNG `fork()` contract already support cultivation without a
  transaction framework or RNG redesign.
- The current frontend has no DOM test dependency. Controller and transport behavior will remain
  unit-tested; the final real Edge smoke will verify the DOM slice.
- The first isolated Edge launch did not run because Windows PowerShell interpreted the UTF-8 script
  without a BOM. The script was converted to ASCII-only source. The next launch was blocked when
  the required GUI permission reviewer disconnected; no browser process or acceptance save was
  created by either attempt.
- The first permitted launch exposed a harness cleanup race: an Edge child still held its cache
  journal. Cleanup was changed to wait for process trees, identify only processes using the exact
  temporary profile root, and retry deletion. The leftover temporary directory was removed before
  rerunning.
- A later harness run reached the final console gate and showed only a missing favicon 404 plus the
  intentionally generated conflict 409, not an unhandled script exception. The page now declares
  an empty data favicon and the secrecy audit uses a successful status response, eliminating both
  artificial console errors. The full run was then repeated from no save.

## 8. Verification

```text
backend ruff format --check      -> pass, 44 files
backend ruff check               -> pass
backend pyright                  -> pass, 0 errors
backend pytest                   -> pass, 150 tests
published content validate       -> pass, 0 entries
frontend prettier check          -> pass
frontend eslint                  -> pass
frontend TypeScript              -> pass
frontend Vitest                  -> pass, 25 tests
frontend production build        -> pass
```

Isolated Edge acceptance with two fresh profiles:

```text
empty save -> create Smoke Player               -> pass
overview -> cultivation navigation              -> pass
request pending                                 -> all 1/7/30 buttons disabled;
                                                   day/revision/insight remained 0/0/0
seek 1 day                                      -> day 1, revision 1, insight 3, seeking
seek 7 days                                     -> day 8, revision 2, insight 33, seeking
restart backend and load same save              -> exact day/revision/insight/status restored
seek 1 day after restart                        -> day 9, revision 3, insight 36, saved
seek at most 30 days                            -> stopped after 16 actual days at insight 100;
                                                   suspected sighting; all buttons disabled
latest action summaries                         -> correct requested/actual/gain values rendered
browser runtime/console exceptions              -> 0
browser-facing API path/RNG/traceback scan       -> no leak
temporary root and acceptance ports             -> absent/closed after finally cleanup
```

Final audit:

```text
git diff --check                              -> pass
dependency manifests/locks changed           -> no
tracked save/temp/cache/build artifacts       -> no
domain infrastructure dependency scan        -> clean
frontend authoritative-calculation scan      -> clean
secret/private-key scan                       -> clean
authoring/private source changes              -> none
```

## 9. Completion summary

TASK-008 is complete. The project now has one immutable wheel-seeking state, a transparent integer
daily rule with exactly two RNG calls, atomic insight/time/revision/RNG persistence, strict save v4,
one stable cultivation API, and a browser-operated overview/cultivation flow. Real Edge acceptance
proved busy-state protection, one- and seven-day settlement, restart recovery, continued saving,
early stop at suspected sighting, button lockout, clean console behavior, and API secrecy. No new
dependency or later cultivation/gameplay system was introduced.
