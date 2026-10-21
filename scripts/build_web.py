#!/usr/bin/env python3
"""Regenerate web/puzzles.json from the shipped SQLite bank.

Never hand-typed: the same QuestionBank the CLI uses serializes every entry
(id, category, difficulty, question, guidance, answer, alt_answers,
explanation, tags, source block) to a single JSON array the static site
fetches at runtime. Run after 'python3 scripts/build_db.py' whenever the
data changes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fun_problem.db import QuestionBank, default_db_path  # noqa: E402

WEB_DIR = Path(__file__).resolve().parents[1] / "web"
OUT = WEB_DIR / "puzzles.json"


def main() -> int:
    bank = QuestionBank(default_db_path())
    entries = [q.to_dict() for q in bank.questions()]
    if not entries:
        raise SystemExit("bank is empty — run scripts/build_db.py first")
    WEB_DIR.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    cats = bank.categories()
    print(f"Wrote {len(entries)} entries to {OUT}")
    print(f"  categories: {len(cats)} · "
          f"difficulties: {sorted(bank.difficulty_histogram())} · "
          f"source kinds: {bank.source_kinds()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())