# TASK-009 Inventory and Warehouse ExecPlan

## 1. Objective

Ship a small browser-operable item-management slice over the existing authoritative state and
transactional single-save runtime:

```text
new/load game -> Items page -> backpack/warehouse transfer -> atomic save -> restart recovery
```

The outcome is a real item page, not a generic item/effect framework.

## 2. Scope

Included:

- immutable item stacks and backpack/warehouse state;
- four explicit pre-alpha item definitions and fixed new-game quantities;
- typed store/retrieve commands, structured rejection, and one aggregate event;
- 12 distinct-stack backpack capacity and bounded integer quantities;
- strict `buxianxian-save` schema v5;
- existing session transaction and revision protection;
- two explicit item-transfer API routes and complete presentation projection;
- vanilla TypeScript Items navigation/page with quantity inputs and busy/error handling;
- focused high-risk tests, one full quality run, and temporary-save smoke verification.

Excluded:

- item use, equip, drop, trade, shops, currency rules, drops, crafting, quality, durability,
  affixes, sorting/filtering, drag/drop, warehouse upgrades, or multiple warehouses;
- item effects, cultivation integration, effect DSL, content-compiler item schemas;
- sighting trials, later cultivation, narrative, desktop packaging, or LLM behavior;
- migration of experimental pre-alpha schema v4.

## 3. Existing context

TASK-008 is committed and pushed as `1c0769c`; the worktree is clean. `GameState` currently owns
revision, elapsed days, player, and cultivation. `DomainEngine` dispatches typed commands and builds
independent complete states. `PersistentGameSession` checks revision, evaluates on a forked RNG,
saves candidate state/RNG, and changes official memory only after persistence succeeds.

`JsonFileSaveRepository` strictly loads schema v4 and atomically replaces UTF-8 JSON. The
`SingleGameRuntime` owns the repository/session and exposes command-specific methods. FastAPI
projects complete state through strict Pydantic DTOs. The TypeScript controller owns only transient
page/busy/error/result state and replaces authority from responses.

No dependency change is needed. Static prototype trait metadata already demonstrates the intended
product-configuration boundary.

## 4. Proposed design

### State and invariants

`ItemStack(item_id, quantity)` is frozen. IDs use stable lowercase ASCII machine form; quantity is
an exact integer from 1 through `MAX_ITEM_STACK_QUANTITY = 1_000_000_000`.

`StorageState(backpack, warehouse)` uses sorted tuples. Each container rejects duplicate IDs,
non-stack values, or non-canonical ordering. Backpack has at most 12 distinct stacks; warehouse has
no slot limit. Zero quantities are never represented.

The domain owns four initial identities because command validation must distinguish unknown items
from known-but-insufficient items. Infrastructure owns names, descriptions, and display categories
through `PROTOTYPE_ITEM_CATALOG`. The engine accepts an optional explicit known-ID tuple for focused
capacity tests without introducing discovery or registration machinery.

New games start with:

```text
spirit_stone.low            20
provision.dry_food           5
material.common_herb         3
document.tattered_scroll     1
```

Warehouse starts empty. Existing state constructors receive the same complete default, while the
new-game path sets it explicitly.

### Commands and transition

`StoreItem` moves backpack to warehouse. `RetrieveItem` moves warehouse to backpack. Validation
order is exact quantity/type, safety bound, known ID, source sufficiency, target overflow, and
backpack new-slot capacity. Rejection returns the original state and consumes no RNG.

Success removes a zero source stack, merges or creates the target stack, keeps tuples sorted,
preserves player/cultivation/time, increments revision once, and emits one `ItemTransferred` fact
with source/target and resulting quantities.

### Persistence and application

Schema v5 retains product and RNG contracts and adds:

```json
"storage": {
  "backpack": [{"item_id": "spirit_stone.low", "quantity": 20}],
  "warehouse": []
}
```

The decoder validates exact object fields and reconstructs domain state. Experimental v1-v4 are
unsupported. Existing save-before-memory semantics require no transaction redesign.

### API and frontend

The runtime owns the explicit item catalog for projection. State includes backpack capacity/used
slots and both containers with display metadata. Routes:

- `POST /api/game/items/store`;
- `POST /api/game/items/retrieve`.

Both accept `item_id`, `quantity`, and `expected_revision`, and map no-session, conflict, domain
rejection, and persistence failure to existing envelopes plus `item_command_rejected`.

The existing in-game state gains page `items`. The page renders backpack and warehouse cards,
quantity inputs, and action buttons. During a request the page is busy and buttons are disabled;
success replaces the complete server state, conflict adopts the server refresh state, and errors
remain recoverable.

## 5. Milestones

### A. Domain and initial state

Files: domain storage contracts, model/engine/exports, character creation, focused domain tests.

Validation: focused Ruff/Pyright and storage/character tests. Recovery is local removal of the new
module and dispatch branches.

### B. Persistence and application

Files: save repository v5, runtime/catalog/composition, session/runtime/persistence tests.

Validation: round-trip/restart, quantity conservation, RNG stability, revision conflict, and
save-failure rollback. Existing atomic writer/RNG format remain unchanged.

### C. API and frontend

Files: DTOs/routes/API tests, TypeScript client/controller/DOM/style and representative tests.

Validation: normal store/retrieve, structured failure, conflict refresh, busy guard, type/lint and
production build.

### D. Documentation, smoke, Git closure

Files: ADR-010, task/status/architecture/API/README and this plan.

Validation: one full backend/frontend suite, content validation, Git scope/artifact scans, temporary
save flow `20 -> store 10 -> retrieve 3 -> backpack 13 / warehouse 7 -> restart load`, cleanup,
commit, push, remote equality, clean tree.

## 6. Progress log

- [x] 2026-07-17: Confirmed clean TASK-008 `1c0769c` baseline and read governance, status,
  architecture, roadmap, ADR-004/007/008/009, TASK-006/007/008 records, and actual code/tests.
- [x] 2026-07-17: Reported the bounded tuple-state, configured catalog, schema-v5, two-route,
  focused-test, and smoke plan before editing.
- [ ] Implement domain state, initial items, commands, events, and focused tests.
- [ ] Implement save v5, runtime catalog, transaction coverage, and API.
- [ ] Implement Items UI and representative frontend tests.
- [ ] Complete documentation, full checks, smoke, scope audit, commit, push, and clean-tree proof.

## 7. Discoveries and deviations

- Only four product items are required, so a fixed engine ID set is sufficient in production. The
  optional explicit ID set exists only to test the 12-slot rule with neutral synthetic stacks; it
  is not a plugin or registry system.
- Existing transaction semantics already cover no-RNG item commands, persistence failure, and
  deterministic retry; no Unit of Work or new application abstraction is needed.

## 8. Verification

Pending implementation.

## 9. Completion summary

Pending implementation.
