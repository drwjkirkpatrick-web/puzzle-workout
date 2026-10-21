"""SQLite-backed question bank for fun-problem-26."""
from __future__ import annotations

import json
import os
import random
import sqlite3
from dataclasses import dataclass
from pathlib import Path

DIFFICULTY_LABELS = {
    1: "Foundational",
    2: "Developing",
    3: "Proficient",
    4: "Advanced",
    5: "Expert",
}

CATEGORIES = (
    "numeric-sequences",
    "letter-series",
    "verbal-analogies",
    "odd-one-out",
    "logical-deduction",
    "math-word-problems",
    "matrix-patterns",
    "lateral-thinking",
    "cryptarithms-codes",
    "spatial-reasoning",
)

_COLUMNS = (
    "id", "category", "difficulty", "question", "guidance", "answer",
    "alt_answers", "explanation", "tags", "source_kind", "source_title",
    "source_author", "source_year", "source_url", "source_license",
    "source_accessed",
)


def default_db_path() -> Path:
    """Repository database, overridable with the FUN_PROBLEM_DB env var."""
    override = os.environ.get("FUN_PROBLEM_DB")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "data" / "questions.db"


@dataclass(frozen=True)
class Question:
    """One puzzle entry with its citation block."""

    id: str
    category: str
    difficulty: int
    question: str
    guidance: str
    answer: str
    alt_answers: tuple
    explanation: str
    tags: tuple
    source_kind: str
    source_title: str
    source_author: object = None
    source_year: object = None
    source_url: object = None
    source_license: str = ""
    source_accessed: str = ""

    @property
    def difficulty_label(self) -> str:
        return DIFFICULTY_LABELS.get(self.difficulty, "?")

    @property
    def all_answers(self) -> tuple:
        return (self.answer,) + tuple(self.alt_answers)

    def source_line(self) -> str:
        """One-line, human-readable provenance for display."""
        if self.source_kind == "original":
            return "Original puzzle composed for this project (MIT)."
        parts = [self.source_title]
        if self.source_author:
            parts.append(f"by {self.source_author}")
        if self.source_year:
            parts.append(f"({self.source_year})")
        line = "Adapted from " + " ".join(parts)
        line += f" — {self.source_license}, accessed {self.source_accessed}."
        if self.source_url:
            line += f" Source: {self.source_url}"
        return line

    @classmethod
    def from_row(cls, row) -> "Question":
        data = dict(row)
        data["alt_answers"] = tuple(json.loads(data["alt_answers"]))
        data["tags"] = tuple(json.loads(data["tags"]))
        return cls(**{k: data[k] for k in _COLUMNS})

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "difficulty": self.difficulty,
            "difficulty_label": self.difficulty_label,
            "question": self.question,
            "guidance": self.guidance,
            "answer": self.answer,
            "alt_answers": list(self.alt_answers),
            "explanation": self.explanation,
            "tags": list(self.tags),
            "source": {
                "kind": self.source_kind,
                "title": self.source_title,
                "author": self.source_author,
                "year": self.source_year,
                "url": self.source_url,
                "license": self.source_license,
                "accessed": self.source_accessed,
            },
        }


class QuestionBank:
    """Read access to the shipped question database."""

    def __init__(self, db_path=None):
        self.path = Path(db_path) if db_path is not None else default_db_path()
        if not self.path.exists():
            raise FileNotFoundError(
                f"Question database not found at {self.path}. "
                "Build it with 'python3 scripts/build_db.py' or point "
                "FUN_PROBLEM_DB at an existing database."
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _select(self, where="1=1", params=(), order="difficulty, id") -> list:
        sql = (
            f"SELECT {', '.join(_COLUMNS)} FROM questions "
            f"WHERE {where} ORDER BY {order}"
        )
        with self._connect() as conn:
            return [Question.from_row(r) for r in conn.execute(sql, params)]

    def count(self, category=None, difficulty=None) -> int:
        where, params = self._filters(category, difficulty)
        sql = f"SELECT COUNT(*) FROM questions WHERE {where}"
        with self._connect() as conn:
            return conn.execute(sql, params).fetchone()[0]

    @staticmethod
    def _filters(category, difficulty):
        where, params = [], []
        if category is not None:
            where.append("category = ?")
            params.append(category)
        if difficulty is not None:
            where.append("difficulty = ?")
            params.append(difficulty)
        return (" AND ".join(where) or "1=1", tuple(params))

    def get(self, question_id) -> "Question | None":
        matches = self._select(where="id = ?", params=(question_id,))
        return matches[0] if matches else None

    def questions(self, category=None, difficulty=None) -> list:
        """All questions (difficulty, id order), optionally filtered."""
        where, params = self._filters(category, difficulty)
        return self._select(where=where, params=params)

    def sample(self, n=None, category=None, difficulty=None, seed=None) -> list:
        """Shuffled draw without replacement. n=None returns the full deck."""
        pool = self.questions(category=category, difficulty=difficulty)
        rng = random.Random(seed)
        rng.shuffle(pool)
        if n is None:
            return pool
        return pool[: max(0, n)]

    def categories(self) -> dict:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT category, COUNT(*) FROM questions GROUP BY category ORDER BY category"
            ).fetchall()
        return {r[0]: r[1] for r in rows}

    def difficulty_histogram(self, category=None) -> dict:
        where, params = self._filters(category, None)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT difficulty, COUNT(*) FROM questions WHERE {where} GROUP BY difficulty",
                params,
            ).fetchall()
        return {r[0]: r[1] for r in rows}

    def source_kinds(self) -> dict:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT source_kind, COUNT(*) FROM questions GROUP BY source_kind"
            ).fetchall()
        return {r[0]: r[1] for r in rows}

    def distinct_sources(self) -> int:
        with self._connect() as conn:
            return conn.execute(
                "SELECT COUNT(DISTINCT source_title) FROM questions WHERE source_kind != 'original'"
            ).fetchone()[0]

    def stats(self) -> dict:
        return {
            "total": self.count(),
            "categories": self.categories(),
            "histogram": self.difficulty_histogram(),
            "source_kinds": self.source_kinds(),
            "distinct_cited_works": self.distinct_sources(),
        }

    def search(self, text, limit=20, category=None) -> list:
        """Case-insensitive LIKE search across question, guidance, explanation, tags."""
        where, params = self._filters(category, None)
        like = f"%{text}%"
        sql = (
            f"SELECT {', '.join(_COLUMNS)} FROM questions "
            f"WHERE {where} AND (question LIKE ? OR guidance LIKE ? "
            f"OR explanation LIKE ? OR tags LIKE ?) "
            f"ORDER BY difficulty, id LIMIT ?"
        )
        params = params + (like, like, like, like, int(limit))
        with self._connect() as conn:
            return [Question.from_row(r) for r in conn.execute(sql, params)]
