# Architecture

Puzzle Workout is a small, auditable data pipeline plus a thin application
layer. Everything is standard library; nothing phones home.

## Data pipeline

```
data/batches/*.json          20 author batches — the source of truth
        │
        │  scripts/validate_one.py     schema + content + histogram gate
        │  (the same gate every entry passed at authoring time)
        ▼
scripts/build_db.py           revalidates each batch, drops cross-batch
        │                     duplicates (exact + near-duplicate),
        │                     assigns stable IDs (NS-014, LS-003, ...),
        │                     writes data/questions.db atomically,
        │                     regenerates docs/DATA_SOURCES.md
        ▼
data/questions.db             shipped SQLite bank — schema/001_schema.sql
        │
        ▼
src/fun_problem/              the application
```

## Application layers

| Module | Role |
|---|---|
| `fun_problem.db` | `QuestionBank` (read access, sampling, search, stats) and the `Question` record |
| `fun_problem.quiz` | `QuizSession` (random / leveled / adaptive) + lenient answer matching |
| `fun_problem.cli` | the `puzzle-workout` command: quiz, show, categories, stats, search, export |

`FUN_PROBLEM_DB` points at any alternative database; the default resolves to
the shipped `data/questions.db`.

## Key decisions

| Decision | Why |
|---|---|
| Batches are JSON; the DB is a build artifact | auditable, rebuildable, dedupe-able |
| Validator run twice (authoring + build) | the DB can never quietly drift from the data |
| Stable IDs assigned at build time | deterministic rebuilds, stable references |
| Sources ledger generated from the data | no hand-typed URLs — provenance is mechanical |
| Stdlib only | runs anywhere, offline, no dependency churn |

## Tests

`tests/` — every shipped row is parametrized through the schema checks; a
trademark-ban scan covers all repo text files and every database column;
rebuild-determinism, citation-ledger coverage, CLI smoke tests, and the
author-gate itself are all exercised.
