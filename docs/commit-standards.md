# Commit Standards

This document defines how changes are classified, staged, committed, and pushed. The goal is high signal history, safe review, and predictable releases.

## Principles
1. Fix root cause, not symptoms.
2. Remove temporary workarounds once the root cause is fixed.
3. One clear primary flow per behavior. No parallel paths.
4. Commit only complete, working slices.
5. Every commit should be reviewable without external context and justified in context.

## Change Classification
Classify every change before you start coding.

**Bugfix**
1. A behavior is wrong, broken, or regressed.
2. Fix restores intended behavior without adding new user-visible features.

**Feature**
1. New capability, new user flow, new UI surface, or new command.
2. Any new API or new data path is a feature.

**Refactor**
1. No change in behavior or output.
2. Improves structure, readability, or testability.
3. Refactor must be structurally complete (no remaining multi-block monolith or large closures).

If a change includes multiple types, split into multiple commits.

## Branch and Commit Discipline
1. Fixes, features, and refactors must not be mixed in a single commit.
2. No “misc cleanup” commits without a clear statement of intent.
3. Each commit must stand alone and be traceable.
4. Branch name and commit message must reflect the actual nature of the change.
5. Cleanup after a root‑cause fix is part of the same logical workstream and must not be skipped.

## Branch Usage
Use branch naming that matches classification.

1. Bugfix: `fix/<short-topic>`
2. Feature: `feat/<short-topic>`
3. Refactor: `refactor/<short-topic>`
4. Docs-only: `docs/<short-topic>`
5. Ops/infra: `ops/<short-topic>`

If you must work on `main`, keep commits minimal and atomic.

## Commit Message Format
Use conventional commits and keep it short and precise.

**Format**
1. `type(scope): summary`
2. `type` must be one of: `fix`, `feat`, `refactor`, `docs`, `chore`, `test`
3. `scope` is required and should match the area: `frontend`, `symfony`, `gateway`, `docs`, `infra`

**Body**
Add a body when the change is non-trivial or touches architecture.

Required lines:
1. `Root cause: ...`
2. `Fix: ...`
3. `Cleanup: ...`

Optional lines:
1. `Risks: ...`
2. `Tests: ...`

## Pre-Commit Checklist
Before committing:

1. Root cause is fixed.
2. Temporary workarounds are removed.
3. No parallel or competing code paths remain.
4. The change is minimal and focused.
5. Tests were run or explicitly noted as not run.
6. Documentation was updated when behavior changed.
7. Refactors are structurally complete (no remaining multi-block monolith or large closures).

## Push Policy
1. No push without explicit approval ("ok") from the task owner.
2. Provide a brief status report before asking for approval:
   - Changes summary
   - Tests/Checks run
   - Risks/Open items
3. Push only after approval, not automatically after commit.

## Submodules and Multi-Repo Workflows
This project includes multiple repos (frontend, symfony, gateway).

Rules:
1. Commit changes inside each repo first.
2. Push each repo.
3. Then update the parent repo submodule pointer and commit it.
4. Keep commit messages consistent across repos.
5. Do not mix unrelated changes between repos.

## Scope and Atomicity
1. One commit should answer: “What changed and why?”
2. Large features can be multiple commits, but each commit must be a complete slice.
3. Do not ship half-complete flows.

## Tests and Validation
1. Always mention what was tested in the commit body.
2. If tests were not run, say why.
3. Prefer small, fast checks over none.
4. **Frontend:** `tsc` ist Pflicht nach **jedem Task** und muss erfolgreich sein, sonst gilt der Task nicht als abgeschlossen.
5. **Frontend:** vor **jedem Push** muss `eslint` gelaufen sein (nach `tsc`), außer klar begründet.

Examples:
1. `Tests: not run (UI-only change)`
2. `Tests: docker compose up -d --build frontend; manual flow: invite/accept`
3. `Tests: npx tsc -p tsconfig.json --noEmit; npm -C frontend run lint`

## Examples
**Bugfix**
```
fix(frontend): restore modal scroll

Root cause: modal body overflow was set to hidden during layout fix.
Fix: set overflow-y back to auto.
Cleanup: none.
Tests: manual scroll check in desktop modal.
```

**Feature**
```
feat(symfony): handle identity key registration

Root cause: identity key register command was unhandled.
Fix: add handler and register action.
Cleanup: none.
Tests: manual identity key register.
```

**Refactor**
```
refactor(gateway): extract relay validation

Root cause: registry logic was duplicated in two modules.
Fix: move shared logic into relay.rs helper.
Cleanup: remove duplicate code paths.
Tests: existing gateway tests.
```

## Definition of Done for a Change
A task is DONE only when:

1. Root cause is fixed.
2. Cleanup is completed.
3. Architecture is consistent.
4. Code is commit-ready.
5. Commit message follows this standard.
6. do not commit .env or keys
