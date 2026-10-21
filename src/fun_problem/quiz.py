"""Quiz sessions: random, leveled, and adaptive presentation."""
from __future__ import annotations

import random
import re

from .db import Question, QuestionBank


def normalize(text) -> str:
    """Casefold and collapse whitespace for answer comparison."""
    return re.sub(r"\s+", " ", str(text)).strip().casefold()


def _as_number(text) -> "float | None":
    try:
        return float(str(text).strip())
    except ValueError:
        return None


def answers_match(attempt, answer, alt_answers=()) -> bool:
    """Lenient equality: exact (normalized) or numeric equivalence."""
    na = normalize(attempt)
    if not na:
        return False
    for candidate in (answer, *alt_answers):
        nc = normalize(candidate)
        if na == nc:
            return True
        va, vc = _as_number(na), _as_number(nc)
        if va is not None and vc is not None and va == vc:
            return True
    return False


class QuizSession:
    """Serves questions one at a time and scores attempts.

    modes:
      random   — shuffled draw across all difficulties
      leveled  — fixed difficulty level (requires difficulty=1..5)
      adaptive — difficulty rises after a correct answer, falls after a miss
    """

    MODES = ("random", "leveled", "adaptive")

    def __init__(self, bank: QuestionBank, mode="random", difficulty=None,
                 category=None, limit=10, seed=None):
        if mode not in self.MODES:
            raise ValueError(f"mode must be one of {self.MODES}, got {mode!r}")
        if mode == "leveled" and difficulty not in range(1, 6):
            raise ValueError("leveled mode requires --difficulty 1-5")
        self.bank = bank
        self.mode = mode
        self.limit = int(limit)
        self.category = category
        self._rng = random.Random(seed)
        if mode == "adaptive":
            self.current_difficulty = difficulty if difficulty in range(1, 6) else 2
        else:
            self.current_difficulty = difficulty
        if mode in ("random", "leveled"):
            self._deck = bank.sample(
                n=self.limit,
                category=category,
                difficulty=difficulty if mode == "leveled" else None,
                seed=seed,
            )
            self._drawn = len(self._deck)
        else:
            self._deck = []
            self._drawn = 0
        self._served = 0
        self._current = None
        self._used_ids = set()
        for q in self._deck:
            self._used_ids.add(q.id)
        self.attempted = 0
        self.correct = 0
        self.skipped = 0

    @property
    def position(self) -> int:
        """Number of questions served so far."""
        return self._served

    @property
    def current(self) -> "Question | None":
        return self._current

    def _draw_adaptive(self) -> "Question | None":
        pool = [
            q for q in self.bank.questions(category=self.category,
                                            difficulty=self.current_difficulty)
            if q.id not in self._used_ids
        ]
        if not pool:  # level exhausted -> widen to any unused difficulty
            pool = [q for q in self.bank.questions(category=self.category)
                    if q.id not in self._used_ids]
        if not pool:
            return None
        q = self._rng.choice(pool)
        self._used_ids.add(q.id)
        return q

    def next(self) -> "Question | None":
        """Next question, or None when the session is exhausted."""
        if self._served >= self.limit:
            return None
        if self.mode == "adaptive":
            q = self._draw_adaptive()
            if q is None:
                return None
        else:
            if self._served >= len(self._deck):
                return None
            q = self._deck[self._served]
        self._current = q
        self._served += 1
        return q

    def submit(self, attempt) -> bool:
        """Score an answer attempt for the current question."""
        if self._current is None:
            raise RuntimeError("No active question — call next() first.")
        self.attempted += 1
        ok = answers_match(attempt, self._current.answer, self._current.alt_answers)
        if ok:
            self.correct += 1
        if self.mode == "adaptive":
            delta = 1 if ok else -1
            self.current_difficulty = max(1, min(5, self.current_difficulty + delta))
        return ok

    def hint(self) -> str:
        """The transferable-strategy guidance for the current question."""
        if self._current is None:
            raise RuntimeError("No active question — call next() first.")
        return self._current.guidance

    def reveal(self):
        """(answer, explanation) for the current question."""
        if self._current is None:
            raise RuntimeError("No active question — call next() first.")
        return self._current.answer, self._current.explanation

    def skip(self):
        """Move on; counts as seen but not attempted (no difficulty change)."""
        if self._current is None:
            raise RuntimeError("No active question — call next() first.")
        self.skipped += 1

    def results(self) -> dict:
        return {
            "served": self._served,
            "attempted": self.attempted,
            "correct": self.correct,
            "skipped": self.skipped,
            "accuracy": round(self.correct / self.attempted, 3) if self.attempted else None,
            "mode": self.mode,
            "final_difficulty": self.current_difficulty if self.mode == "adaptive" else None,
            "limit": self.limit,
        }

    def __iter__(self):
        return iter(self.next, None)
