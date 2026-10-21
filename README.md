# Puzzle Workout 🧩

**An open puzzle gym for everyone who wants to think sharper.**

Puzzle Workout is a bank of **270 reasoning puzzles** — number sequences, letter
series, verbal analogies, odd-one-out, logic, math word problems, matrix
patterns, riddles, word arithmetic, and spatial reasoning — and every single
one comes with a **coaching strategy**, a **verified answer**, a **worked
explanation**, a **difficulty level** from Foundational to Expert, and a
**citation** you can follow to its public-domain source.

It is not a test, and it measures nobody. It is a *workout*: warm up at level 1,
drill the moves that make new puzzles less scary, and level up at your own pace.

## Try it in your browser

No install, no account, no tracking — the whole gym runs in your browser:

**→ [puzzle-workout.vercel.app](https://puzzle-workout.vercel.app)**

The site is the same bank (270 puzzles), the same three training modes —
random, leveled, adaptive — the same coach's hints and cited explanations,
served as a zero-dependency static page. Prefer a terminal? Read on.

## What's inside

- **270 puzzles across 10 categories** — balanced from Foundational to Expert
- **Every entry teaches an approach**, not just an answer: ask for the strategy
  hint (`h`) before you commit, then read the full reasoning after
- **Three training modes** — random, leveled, adaptive
- **Honest provenance** — adapted puzzles cite the exact public-domain page
  fetched (Dudeney 1907/1917, Carroll 1886/1896, Loyd 1914, Stearns, Pearson,
  and friends); original puzzles are MIT. The source ledger is generated
  mechanically from the data — never hand-typed: [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md)
- **Zero dependencies** — pure Python 3.9+ standard library, with the SQLite
  bank shipped in the repo, so it works offline the moment you clone it

## Quick start

```bash
git clone https://github.com/drwjkirkpatrick-web/puzzle-workout.git
cd puzzle-workout
python3 -m pip install -e .

puzzle-workout stats                        # what's in the bank
puzzle-workout quiz                         # 10 random puzzles
puzzle-workout quiz --mode leveled --difficulty 3
puzzle-workout quiz --mode adaptive         # the level moves with you
puzzle-workout quiz --print --limit 5 --category lateral-thinking   # study mode
```

## Three ways to train

- **random** — a shuffled draw across the whole bank. Fresh every session,
  reproducible with `--seed`.
- **leveled** — fix a level (`--difficulty 1-5`) and drill exactly there.
- **adaptive** — starts at level 2; each correct answer moves you up a level,
  each miss moves you down, clamped at 1 and 5. The workout finds your edge.

In any session: type `h` for the coaching hint, `s` to skip, `q` to quit with a
summary. Every question ends with the full explanation and its source line.

## Commands

| Command | What it does |
|---|---|
| `puzzle-workout quiz` | interactive session (`--mode`, `--difficulty`, `--category`, `--limit`, `--seed`) |
| `puzzle-workout quiz --print` | study mode — questions with answers and reasoning, no interaction |
| `puzzle-workout show <ID>` | one full entry, e.g. `puzzle-workout show NS-005` |
| `puzzle-workout search "prime"` | find puzzles by text (`--answers` to include answers) |
| `puzzle-workout categories` | category counts |
| `puzzle-workout stats` | totals, difficulty histogram, source breakdown |
| `puzzle-workout export` | dump entries as JSON for your own tools |

## The question bank

```
data/batches/*.json      source of truth — 20 author batches, plain JSON
schema/001_schema.sql    the SQLite schema
data/questions.db        the shipped database (build artifact)
scripts/build_db.py      revalidates every batch, dedupes, assigns stable
                        IDs (NS-014, LS-003, ...), rebuilds the DB and
                        regenerates docs/DATA_SOURCES.md
scripts/build_web.py     serializes the bank to web/puzzles.json — the site's copy
web/                    the puzzle-workout.vercel.app static site (no build step)
scripts/validate_one.py  the content gate every entry must pass
```

Rebuild from source any time: `python3 scripts/build_db.py`
The build refuses any batch that fails the validator — the same gate the
authors used — so the database can never quietly drift from the data.

## Data sources & licenses

- **Code and original puzzles:** MIT
- **Adapted puzzles:** public-domain works published before 1931, each citing
  the exact page its adapter fetched, with license and access date recorded.
- Full ledger (generated, not typed): **[docs/DATA_SOURCES.md](docs/DATA_SOURCES.md)**

## Contributing

New puzzles are the best contribution — the validator is friendly and tells
you exactly what to fix. See **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)**.
Test suite: `python3 -m pytest -q`.

## A note on what this is

Puzzle Workout names no organizations and claims no affiliations. It is
practice material for critical thinking — for meeting *new* puzzles with a
toolbox instead of a blank stare. Nothing here measures intelligence or
anyone's worth. Puzzles are for everyone.

— drwjkirkpatrick-web
