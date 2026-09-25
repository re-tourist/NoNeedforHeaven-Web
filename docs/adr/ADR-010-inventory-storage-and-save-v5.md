# ADR-010: Pre-alpha inventory storage and save v5

## Status

Accepted for the pre-alpha prototype.

## Context

The first playable loop needs a small, persistent item-management capability without coupling
items to cultivation, time, or an effect language. The existing snapshot save and single-process
session already provide the required atomic commit boundary.

## Decision

The formal `GameState` contains immutable `StorageState` with sorted `ItemStack` tuples for a
backpack and warehouse. The backpack allows at most 12 distinct item IDs; the warehouse has no
prototype capacity limit. A stack always has one stable item ID and a positive bounded integer
quantity. Zero quantities remove the stack.

The initial pre-alpha catalog contains four display-only IDs: `spirit_stone.low`,
`provision.dry_food`, `material.common_herb`, and `document.tattered_scroll`. Display names and
descriptions live in infrastructure; saves contain only IDs and quantities.

`StoreItem` and `RetrieveItem` are typed domain commands. They atomically change both containers,
increment revision once, emit one aggregate transfer event, do not advance time, and do not consume
RNG. The existing session forks and persists the candidate state before replacing official memory.

The save envelope remains `buxianxian-save` and moves to schema v5. Experimental schemas v1-v4 are
explicitly rejected; no migration is invented before external player saves exist.

## Consequences

The browser can inspect and transfer prototype item stacks, and restart recovery includes storage.
Item behavior, use/equip/drop/trade, effects, and content-compiler integration remain deferred.

