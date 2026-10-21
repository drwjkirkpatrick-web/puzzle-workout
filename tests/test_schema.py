"""Every shipped row must satisfy the content schema."""
import re
from datetime import date

import pytest

LICENSES = {"Public domain (US)", "Public Domain Mark 1.0", "CC BY-SA 4.0",
            "CC0 1.0", "MIT (project original)"}
KINDS = {"original", "public-domain", "open-license"}
ORIGINAL_TITLE = "Original composition for fun-problem-26"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _iso_ok(value):
    return bool(DATE_RE.match(value or "")) and _valid_date(value)


def _valid_date(value):
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


@pytest.mark.parametrize("q", [pytest.param(q, id=q.id) for q in
                               __import__("fun_problem").db.QuestionBank().questions()])
def test_entry_schema(q):
    assert q.category in {"numeric-sequences", "letter-series", "verbal-analogies",
                          "odd-one-out", "logical-deduction", "math-word-problems",
                          "matrix-patterns", "lateral-thinking",
                          "cryptarithms-codes", "spatial-reasoning"}
    assert isinstance(q.difficulty, int) and 1 <= q.difficulty <= 5
    assert len(q.question.strip()) >= 15
    assert len(q.guidance.strip()) >= 60
    assert 1 <= len(q.answer.strip()) <= 60
    assert len(q.explanation.strip()) >= 80
    assert 1 <= len(q.tags) <= 4
    assert all(isinstance(t, str) and t.strip() for t in q.tags)
    assert all(isinstance(a, str) and a.strip() for a in q.alt_answers)
    assert q.source_kind in KINDS
    assert q.source_license in LICENSES
    assert _iso_ok(q.source_accessed)
    if q.source_kind == "original":
        assert q.source_title == ORIGINAL_TITLE
        assert q.source_url is None
    else:
        assert q.source_title
        assert q.source_url and q.source_url.startswith("https://")
