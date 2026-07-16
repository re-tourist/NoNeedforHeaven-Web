# ADR-005: Versioned published read-only content

- Status: Accepted
- Date: 2026-07-15

## Context

“不羡仙” needs authored material without turning an author's Obsidian workspace into a runtime
dependency or allowing private drafts to enter a build accidentally. The first low-risk content
slice is text that can eventually be read but cannot execute rules or change state.

Author source and runtime content serve different needs. Markdown is convenient to edit and review;
the runtime needs a validated, deterministic, explicitly versioned contract. Player saves are a
third independent category because they contain mutable session facts and random progress.

## Decision

### Explicit publication boundary

Only Markdown below `authoring/published/documents/` is a default compiler input. Private and draft
siblings are ignored by Git and are never discovered by walking `authoring/`, a home directory, or
an Obsidian Vault. Compiler callers must provide the exact publication root.

Compiled packages are generated under `runtime-content/` by default and ignored by Git. Neutral
test fixtures live under `backend/tests/content/fixtures/`, outside the publication root.

This makes publication an intentional repository action, keeps Obsidian optional, and prevents
plugins, personal metadata, backlinks, and unrelated notes from becoming runtime contracts.

### Source contract

Each v1 source begins with four unique frontmatter fields:

```yaml
schema_version: 1
id: document.example
type: read_only_document
title: "Example Document"
```

The remainder is retained as Markdown. Version 1 accepts only simple scalar `key: value` lines,
plain values, and JSON-style double-quoted strings. Unknown or duplicate fields and YAML collections,
comments, anchors, multiline forms, or executable expressions are rejected.

The implementation uses the Python standard library rather than PyYAML. General YAML would add a
dependency, implicit typing rules, and a larger compatibility surface without benefit for four
scalars. If future source metadata requires real YAML, adopting it requires an explicit source
compatibility decision rather than silently widening this parser.

### Stable identity

`id` is explicit metadata and is never derived from a title, filename, directory, or absolute path.
It is a lowercase ASCII machine identifier of at most 128 characters, starts with a letter, and uses
alphanumeric segments separated by `.`, `_`, or `-`. IDs are unique across a package.

Titles are player-visible and may change or use Chinese without changing references. Source files
may be renamed without changing identity.

### Runtime package and versions

The first package is UTF-8 JSON:

```json
{
  "entries": [
    {
      "id": "document.example",
      "markdown": "# Example\n",
      "schema_version": 1,
      "title": "Example Document",
      "type": "read_only_document"
    }
  ],
  "format": "buxianxian-content",
  "schema_version": 1
}
```

The root schema version governs the package envelope. Each entry also carries its content schema
version. Unknown versions and content types are rejected rather than guessed. An incompatible
envelope or entry change requires an explicit new version and future version-dispatch path.

Entries sort by ID, JSON keys sort lexicographically, formatting and newline behavior are fixed,
and no source path or author metadata is emitted. Writing uses a same-directory temporary file,
flush and `fsync`, then `os.replace`; invalid source never produces a success package and ordinary
replacement failure preserves the previous complete target.

### First type is read-only only

Package v1 supports only `read_only_document`. It stores an ID, type, title, entry schema version,
and Markdown body. It has no conditions, effects, transitions, scripts, references, unlock state,
or executable behavior. Starting here verifies the author-to-runtime boundary without prematurely
designing narrative navigation or gameplay schemas.

## Consequences

Positive:

- author publication is explicit and private material remains outside compiler discovery;
- the runtime package is inspectable, deterministic, and separately versioned from saves;
- stable references do not depend on display text or filesystem layout;
- source failures have structured codes plus file and optional line context;
- no production dependency is added and Obsidian remains optional.

Costs and limits:

- the accepted frontmatter syntax is intentionally narrower than YAML;
- package and entry v1 become compatibility contracts;
- no runtime loader consumes this package yet;
- cross-entry references, additional content types, HTML rendering, localization, search, assets,
  Wikilinks, watches, state binding, API/frontend integration, and formal content remain deferred.
