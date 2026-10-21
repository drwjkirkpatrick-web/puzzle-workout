"""A three-minute tour of the Puzzle Workout bank.

Run from the repository root:
    PYTHONPATH=src python3 examples/quiz_demo.py
"""
import random

from fun_problem.db import DIFFICULTY_LABELS, QuestionBank

bank = QuestionBank()
stats = bank.stats()
print(f"Puzzle Workout — {stats['total']} puzzles, "
      f"{len(stats['categories'])} categories")
print("Difficulty spread:", "  ".join(
    f"L{lvl}:{stats['histogram'].get(lvl, 0)}" for lvl in range(1, 6)))

rng = random.Random()
for q in bank.sample(n=3, seed=rng.randrange(1 << 30)):
    print("\n" + "=" * 60)
    print(f"[{q.id}] {q.difficulty_label} - {q.category}")
    print(q.question)
    print(f"\nHow to approach it: {q.guidance}")
    print(f"\nAnswer: {q.answer}")
    print(f"Why: {q.explanation}")
    print(f"\n{q.source_line()}")
