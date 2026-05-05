# mempalace.md: Project Memory Palace

## Purpose

This file is a navigation index for Ancient Unfiltered. It helps humans and agents remember where project knowledge lives without turning this file into a competing source of truth.

`mempalace.md` is intentionally index-only. If it conflicts with `spec.md`, `spec.md` wins and this file must be corrected.

## Single Source Of Truth Rule

The app scaffold uses a strict single source of truth model:

1. `spec.md` is the normative source for product intent, architecture, data contracts, UI requirements, accessibility, tests, and release criteria.
2. `agents.md` is the execution protocol derived from `spec.md`.
3. `README.md` is user-facing release documentation for the current shipped state.
4. Code and tests are the implementation record for what currently runs.
5. `mempalace.md` is an index for finding the above quickly.

The ancient texts themselves are not governed by this project SSOT. They are evidence artifacts with their own source provenance. The project must never rewrite an ancient passage to fit the scaffold.

## Quick Index

| Key | Canonical place | Memory job |
| --- | --- | --- |
| `SSOT` | `spec.md` | normative scaffold truth |
| `AGENTS` | `agents.md` | execution protocol derived from the spec |
| `USERDOCS` | `README.md` | shipped user-facing promise |
| `RUNTIME` | `main.py`, `database.py`, `philology.py`, `static/` | current app behavior |
| `CHRONO` | `philology.py`, future `sources/`, `tests/` | cutoff and date-estimate behavior |
| `EVIDENCE` | `examples/`, future fixtures | source inputs and captured source shapes |
| `VERIFY` | `tests/`, `README.md` | repeatable checks and documented outcomes |

## Memory Rooms

### 1. North Door: Product Truth

- Canonical file: `spec.md`
- Use for: v0.2 goals, non-interpretive philosophy, Greek-first expansion, UI requirements, data model, accessibility, release criteria.
- Rule: new product requirements must be added here first.

### 2. East Desk: Agentic Execution

- Canonical file: `agents.md`
- Use for: execution phases, agent guardrails, release workflow, implementation order.
- Rule: keep this file procedural. Do not introduce product requirements here unless they point back to `spec.md`.

### 3. South Shelf: User Promise

- Canonical file: `README.md`
- Use for: what users get today, installation, examples, known limitations, validation outcomes.
- Rule: README describes shipped behavior. It should not promise v0.2 behavior before that behavior exists.

### 4. West Cabinet: Running System

- Canonical files: `main.py`, `database.py`, `philology.py`, `static/`
- Use for: local FastAPI app, cache, source parsing, frontend reading desk.
- Rule: implementation follows `spec.md`; when implementation diverges, either fix code or update `spec.md` deliberately.

### 5. Chronology Gate

- Canonical files: `philology.py`, future `sources/` modules, tests under `tests/`
- Use for: cutoff logic, author/work date estimates, unverified-date handling.
- Rule: date estimates are always labeled as estimates. Future evidence is dropped only when securely later than the cutoff.

### 6. Evidence Archive

- Canonical directories: `examples/`, future fixtures under `tests/fixtures/`
- Use for: smoke passages, captured API shapes, parser fixtures.
- Rule: example ancient texts are evidence inputs, not project requirements.

### 7. Verification Table

- Canonical files: `tests/`, `README.md`
- Use for: unit tests, smoke results, release validation.
- Rule: add tests when parser behavior, chronology, source routing, or accessibility contracts change.

## Change Protocol

When adding or changing project scaffold behavior:

1. Update `spec.md` first if the change alters product truth.
2. Update `agents.md` if the execution process changes.
3. Update code and tests.
4. Update `README.md` only for shipped user-facing behavior.
5. Update `mempalace.md` only if navigation or file ownership changes.

When adding ancient source material:

1. Preserve source wording as retrieved or quoted.
2. Record provenance.
3. Do not treat the example text as a project requirement.
4. Do not normalize, translate, or emend source text without labeling the transformation.

## Conflict Resolution

Use this precedence order for scaffold decisions:

1. `spec.md`
2. `agents.md`
3. tests and code
4. `README.md`
5. `mempalace.md`

Use source provenance for ancient text evidence. Internal project files must not override the ancient source record.
