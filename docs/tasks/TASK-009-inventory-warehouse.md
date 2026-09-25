# TASK-009: Inventory and warehouse gameplay

## Status

Implemented in the current pre-alpha worktree; closure verification completed with TASK-010.

## Delivered

- Immutable backpack and warehouse stacks with a 12-distinct-item backpack limit.
- Four display-only prototype item definitions and fixed new-game quantities.
- Atomic `StoreItem` and `RetrieveItem` domain commands with structured rejection.
- Save schema v5 with strict storage validation and existing atomic replacement.
- FastAPI storage projection plus `/api/game/items/store` and `/api/game/items/retrieve`.
- Frontend items page with quantity controls, busy guards, conflict refresh, and restart recovery.

## Deferred

Item use, equip, drop, trade, shops, effects, quality, durability, crafting, and resource
integration are not part of this task.

## Verification

Backend and frontend test suites pass. The temporary-save smoke flow confirms creation, item
transfer, restart, and storage recovery. See the final task report for exact commands.

