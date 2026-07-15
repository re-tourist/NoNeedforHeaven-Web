# ExecPlan contract

Use an ExecPlan for long, risky, cross-module, or contract-changing work.

An ExecPlan is a living implementation document. It must be updated as work proceeds rather than written once and ignored.

## Required sections

### 1. Objective

State the user-visible or engineering outcome.

### 2. Scope

List included and excluded work.

### 3. Existing context

Describe relevant entrypoints, modules, tests, constraints, and prior decisions discovered from the repository.

### 4. Proposed design

Explain boundaries, data flow, public contracts, and alternatives considered.

### 5. Milestones

Break work into independently verifiable steps.

Each milestone should include:

- files or modules affected;
- expected behavior;
- validation commands;
- rollback or recovery considerations where relevant.

### 6. Progress log

Maintain a checklist with dates or clear status markers.

### 7. Discoveries and deviations

Record unexpected repository facts, failed approaches, and reasons for changing the plan.

### 8. Verification

List automated and manual checks and their final results.

### 9. Completion summary

State what shipped, what did not, and remaining risks.

## Planning rules

- Inspect the repository before finalizing the plan.
- Do not invent files or behavior without checking.
- Prefer small milestones with observable results.
- Update the plan when reality differs from the initial assumption.
- Do not expand scope silently.
- If a major architectural decision is required, create or update an ADR.
