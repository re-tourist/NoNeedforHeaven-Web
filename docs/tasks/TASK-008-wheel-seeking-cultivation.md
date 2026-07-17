# TASK-008: Wheel-seeking cultivation vertical slice

Status: Completed on 2026-07-17.

## Goal

Deliver the first browser-operable gameplay action: spend up to 1, 7, or 30 authoritative days
seeking the wheel, gain deterministic insight, persist the exact RNG position, and stop at
`疑见生命之轮`.

## Delivered contract

- Immutable cultivation state is part of every formal `GameState`.
- `SeekWheel(max_days)` accepts 1 through 30 and settles actual days sequentially.
- Every actual day consumes exactly two controlled RNG calls.
- One accepted command advances time, insight, status, revision, and one aggregate domain event
  atomically.
- `buxianxian-save` schema v4 strictly persists cultivation state and RNG.
- The existing session preserves conflict, rejection, save-failure rollback, and deterministic retry.
- FastAPI exposes one typed cultivation route and complete state/result projections.
- The browser provides total/cultivation navigation, accessible progress, 1/7/30-day controls,
  busy/error states, and the latest result.

## Rule summary

The pre-alpha threshold is 100 insight. Ordinary daily insight uses comprehension, spiritual sense,
and temperament. Fortune controls a bounded inspiration chance. Constitution and prototype traits
do not affect this first rule. The complete integer formula and RNG order are recorded in ADR-009.

## Scope

This task does not implement the three sighting trials, a completed seeking breakthrough, later
realms, multiple methods, trait effects, resources, injuries, items, locations, NPCs, narrative,
content-runtime integration, or LLM behavior.

## Verification

Domain tests cover invariants, determinism, fixed RNG consumption, attribute effects, bounded
outputs, early stopping, rejections, and batch/day equivalence. Persistence/application/API tests
cover schema-v4 round trips, restart continuation, conflicts, rejection, save rollback, and secrecy.
Frontend tests cover strict transport parsing, navigation, authoritative refresh, duplicate-submit
guards, conflict refresh, error recovery, and suspected-sighting disablement. Full command and real
browser evidence is retained in the ExecPlan.
