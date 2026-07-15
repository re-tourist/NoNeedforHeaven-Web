# Product vision

## Product

**不羡仙** is an independent, local-first text game intended for long-term development.

Its eventual experience may combine authored narrative, state-driven choices, simulation, procedural events, and LLM-assisted presentation. These are product possibilities, not current implementation requirements.

## Runtime and authoring

The product has two separate environments:

### Player runtime

A standalone local web application:

- Python owns authoritative state and rules.
- A browser-based frontend displays the game and submits player commands.
- The runtime does not require Obsidian.

### Author workspace

Obsidian is used as a convenient editor and knowledge workspace for future content:

- worldbuilding;
- characters;
- locations;
- factions;
- events;
- narrative drafts;
- reference material.

Author notes are not automatically runtime content. A later content pipeline will explicitly validate and compile publishable material.

## Long-term product principles

1. **System before content**

   Build reliable state transitions, persistence, content contracts, and author tooling before formal narrative production.

2. **Single source of truth**

   Python is authoritative. The frontend does not duplicate game rules.

3. **Local first**

   The core game should work without accounts, cloud infrastructure, or mandatory online services.

4. **Deterministic where necessary**

   State transitions and random outcomes should be reproducible for testing, debugging, and replay.

5. **Content is data, not code**

   Ordinary future content should not require changes to the core engine.

6. **LLM is constrained assistance**

   LLMs may help generate presentation or proposals, but cannot bypass validation or directly alter authoritative state.

7. **Incremental delivery**

   Each milestone must produce a small, testable capability and preserve a working main branch.

## Non-goals for the initial stages

- polished visuals;
- a complete story;
- complex simulation;
- mobile release;
- public online deployment;
- multiplayer;
- modding support;
- desktop packaging;
- autonomous LLM-driven world simulation.

## First meaningful product proof

The first meaningful proof is not a story scene.

It is a headless engine that can:

- accept a command;
- validate it;
- transform immutable input state into deterministic output state;
- record the transition;
- reject invalid commands without corrupting state;
- pass automated tests.

Only after that foundation is reliable should the project prove persistence, content compilation, API transport, UI interaction, and finally authored gameplay.
