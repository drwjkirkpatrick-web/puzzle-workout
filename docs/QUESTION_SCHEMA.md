# Question Schema — fun-problem-26

Every batch file in `data/batches/` is a JSON array of entry objects.
Each entry has EXACTLY these top-level keys — no extras, none missing:

| Key | Type | Rules |
|---|---|---|
| `category` | string | One of the 10 canonical categories (below) |
| `difficulty` | integer | 1–5 (1 = Foundational … 5 = Expert) |
| `question` | string | Self-contained puzzle text; the solver needs nothing else |
| `guidance` | string | ≥ 60 chars. A TRANSFERABLE strategy for this puzzle type — never reveals the answer |
| `answer` | string | Primary answer, short (≤ 60 chars) |
| `alt_answers` | array of strings | Other fully acceptable answers; may be `[]` |
| `explanation` | string | ≥ 80 chars. Complete worked reasoning that proves the answer |
| `tags` | array of strings | 1–4 short lowercase tags |
| `source` | object | Citation block (below) |

## `source` object

```json
{
  "kind": "original | public-domain | open-license",
  "title": "…",
  "author": "… or null",
  "year": 1917,
  "url": "https://… or null",
  "license": "…",
  "accessed": "YYYY-MM-DD"
}
```

- `original`: compose the puzzle yourself. Use exactly
  `title: "Original composition for fun-problem-26"`, `author: null`, `year: null`,
  `url: null`, `license: "MIT (project original)"`.
- `public-domain`: you ADAPTED a puzzle from a source you actually fetched this
  session (rewritten in modern, clean English — never long verbatim passages).
  `url` is the exact page you fetched (https only), `license` is
  `"Public domain (US)"` or `"Public Domain Mark 1.0"`.
- `open-license`: adapted from CC-licensed material (e.g. Wikipedia);
  `license` is `"CC BY-SA 4.0"` or `"CC0 1.0"`.
- `accessed` is the date YOU fetched the source (today's date — run `date +%F`).
- Never invent a source you did not fetch. No Hugging Face. No modern
  test-prep companies or organization websites.

## Content rules (validator-enforced)

1. **No entry may name any organization, company, or test product.** The ban is
   enforced by a token assembled at runtime in the validator, so the literal
   string appears nowhere in this repository. The project names no
   organizations, companies, or test products anywhere. Describe the style as
   "aptitude-style reasoning puzzles" if prose needs a label.
2. Questions must be solvable from the question text alone — no images, no
   outside trivia, no culturally specific assumptions.
3. Exactly one defensible primary answer; other fully acceptable answers go in
   `alt_answers`.
4. Verify every answer mechanically where the category allows:
   - numeric sequences: confirm the stated rule reproduces EVERY given term,
     then compute the answer;
   - cryptarithms: brute-force with python3 and confirm the solution is unique;
   - logic puzzles: check every premise is used and consistent;
   - matrix/spatial: enumerate carefully.
5. `guidance` teaches HOW to think (a strategy toolbox the solver can reuse on
   other puzzles); `explanation` shows WHY this answer follows.
6. Accessible to solvers 13+; clean language; world-neutral.
7. Text-renderable: ASCII plus simple symbols (`● ■ ▲ ◆ ★`) allowed; no
   emoji-only puzzles; multi-line grids use `\n` and `|` or spaces.

## Categories (10)

`numeric-sequences`, `letter-series`, `verbal-analogies`, `odd-one-out`,
`logical-deduction`, `math-word-problems`, `matrix-patterns`,
`lateral-thinking`, `cryptarithms-codes`, `spatial-reasoning`

## Difficulty scale

- **1 Foundational** — single obvious rule, gentle numbers/words
- **2 Developing** — one rule with a twist, or two simple rules
- **3 Proficient** — multi-step rule; needs systematic differencing or search
- **4 Advanced** — layered rules or genuinely tricky framing
- **5 Expert** — hard even for practiced solvers; several hypotheses needed