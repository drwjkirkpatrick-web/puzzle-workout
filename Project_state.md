# Project State: fun-problem-26 (published as "puzzle-workout")

> **Last updated:** 2026-10-21
> **Current phase:** polish
> **Overall health:** green

---

## 1. Goal (1-2 sentences)

An open, friendly puzzle trainer: a bank of 250+ aptitude-style reasoning
puzzles, each with question, transferable guidance, verified answer,
explanation, difficulty 1-5, and a grounded citation — playable in random,
leveled, or adaptive order from a small CLI.

## 2. Current Status

### Done
- [x] Research: 20+ public-domain puzzle sources verified, registered in citation ledger (data/research/ledger.json)
- [x] Question schema + content rules (docs/QUESTION_SCHEMA.md) + child validator (scripts/validate_one.py)
- [x] 20 author batches written via 4 delegate waves (270 candidates, one file per child)
- [x] All batches PASS the validator; cryptarithms brute-force verified unique (14/14)
- [x] Cross-batch dedupe (bigram + document-frequency aware), final SQLite build
- [x] Quiz package (db, quiz, cli) — random / leveled / adaptive modes
- [x] Full test suite green (schema parametrized over every row, trademark scan, rebuild determinism, citation coverage, CLI)
- [x] README (community voice) + docs + CI + examples
- [x] Published to GitHub as drwjkirkpatrick-web/puzzle-workout
- [x] Web UI: zero-dependency static site (web/), all three training modes,
      coach's hints and cited explanations, deployed via Vercel CLI to
      https://puzzle-workout.vercel.app (2026-10-21)

### In Progress
- [ ] (none)

### Not Started
- [ ] Future: more categories, spaced-repetition scheduling

## 3. Architecture & Key Decisions

| Decision | Rationale | Date |
|---|---|---|
| SQLite `data/questions.db` shipped in-repo | small, instant use, no build step for users | 2026-10-20 |
| JSON batches are the source of truth; DB is built | auditable, rebuildable, dedupe-able | 2026-10-20 |
| One subagent per batch file; parent owns shared files | Walker hard rule | 2026-10-20 |
| No organization/trademark names anywhere (validator + tests enforce; token assembled at runtime) | project stance; welcoming to everyone | 2026-10-20 |
| Public-domain adaptations + original composition only | clean, verifiable licensing | 2026-10-20 |
| Near-dupe detection via token bigrams + document-frequency filter | plain token sets false-positived on grid boilerplate (dropped 8 legit matrix puzzles before the fix) | 2026-10-21 |
| Static site ships answers client-side; JS is a faithful port of quiz.py (modes + lenient matcher) | offline-first, zero-backend; parity-tested 23/23 against Python answers_match | 2026-10-21 |
| web/puzzles.json generated only by scripts/build_web.py from the SQLite bank | never hand-typed; site can't drift from the data | 2026-10-21 |
| Re-dispatch waves in smaller sizes after provider 429 usage-cap failures | full 6-child wave lost to Ollama Cloud 5-hour cap; 3-child waves after window roll succeeded | 2026-10-21 |

## 4. Blockers & Risks

- None open. (Historical: Ollama Cloud 429 usage cap killed one 6-child wave — recovered by re-dispatching in two 3-child waves.)

## 5. Next Step (only ONE)

None — first push complete. Future expansion ideas live in section 2.

## 6. Environment & Tooling Notes

- Runtime python: 3.14 (Hermes-managed venv); tests run with /usr/bin/python3 (3.10.12, pytest 9.1.1)
- SQLite 3.53.1
- Skills used: grounded-citations, subagent-batch-production, github-workflows, project-state-management, remedy_personality_picker (Phosphorus voice for README)

## 7. Recent Session Log

- 2026-10-20: Project created; 17 sources verified; schema/validator/map/exemplar; waves 1-2 dispatched and verified (13 batches).
- 2026-10-21: Waves 3-4 completed (429 outage on first wave-4 attempt — re-dispatched in smaller waves); all 20 batches done; dedupe fixed (bigram+df); final build; tests green; published as puzzle-workout.
- 2026-10-21: Web UI built (web/: index.html, style.css, app.js + generated puzzles.json), deployed to puzzle-workout.vercel.app; fixed mid-question advance bug found by browser test; mobile grid blowout hardened; answer matcher parity-tested vs Python.

## 8. References

- Schema: `docs/QUESTION_SCHEMA.md`
- Batch map: `data/batches/BATCH_MAP.json`
- Source ledger: `data/research/ledger.json`
- Skills: subagent-batch-production (waves), grounded-citations (ledger)
