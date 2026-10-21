"""fun-problem-26 — an open, friendly puzzle trainer for critical thinking."""

__version__ = "0.1.0"

from .db import DIFFICULTY_LABELS, Question, QuestionBank  # noqa: F401
from .quiz import QuizSession, answers_match  # noqa: F401
