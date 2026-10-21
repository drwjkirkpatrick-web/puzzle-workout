# Contributing to Puzzle Workout

The best contribution is a new puzzle (or ten). The pipeline is deliberately
strict so the bank stays trustworthy — every entry is schema-checked,
answer-verified, and provenance-tracked.

## How to add puzzles

1. **Read the rules** — [QUESTION_SCHEMA.md](QUESTION_SCHEMA.md) defines the
   entry fields, content rules, source kinds, and the difficulty scale.
2. **Pick a home** — add entries to an existing batch in `data/batches/`, or
   create `data/batches/<category>_<letter>.json` and register it in
   `data/batches/BATCH_MAP.json` with its `count` and `difficulty` histogram.
3. **Source honestly**:
   - `kind: "original"` — your own composition (license `MIT (project original)`).
   - `kind: "public-domain"` — adapted from a pre-1931 book **you actually
     fetched** (https only); record the exact URL and the access date.
   - Never copy from modern copyrighted books, test-prep companies, or any
     organization's current website.
4. **Verify your answer mechanically** where the category allows — compute
   sequences, brute-force cryptarithms, enumerate logic cases with python3.
5. **Pass the gate**:
   ```bash
   python3 scripts/validate_one.py data/batches/<your-file>.json
   ```
   It checks schema, content rules, your declared histogram, in-file
   duplicates, and the organization-name ban.
6. **Rebuild and test**:
   ```bash
   python3 scripts/build_db.py
   python3 -m pytest -q
   ```
7. **Open a PR** against `main` with a short note on what the puzzles test.

## House rules

- No organization, company, or product names anywhere (validator-enforced).
- Questions fully self-contained, world-neutral, friendly for ages 13+.
- Exactly one defensible primary answer; other fully acceptable answers go in
  `alt_answers`.
- `guidance` teaches a transferable strategy — never the answer itself.
