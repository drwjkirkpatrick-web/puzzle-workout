"""QuizSession: modes, answer matching, adaptive difficulty."""
import pytest

from fun_problem.db import QuestionBank
from fun_problem.quiz import QuizSession, answers_match


def test_exact_and_normalized_match():
    assert answers_match("  J ", "j")
    assert answers_match("FORTY-EIGHT", "forty-eight")


def test_numeric_equivalence():
    assert answers_match("48.0", "48")
    assert answers_match(" 0.5 ", "0.50")
    assert not answers_match("47", "48")


def test_alt_answers_accepted():
    assert answers_match("boot", "shoe", ["boot", "loafer"])
    assert not answers_match("sandal", "shoe", ["boot"])


def test_empty_attempt_never_matches():
    assert not answers_match("", "48")
    assert not answers_match("   ", "48")


def test_units_are_not_numeric():
    assert not answers_match("48", "48 feet")  # units matter; alt_answers cover it
    assert answers_match("48", "48 feet", ["48"])


def test_random_mode_serves_limit_without_repeats(bank):
    s = QuizSession(bank, mode="random", limit=8, seed=11)
    served = [s.next().id for _ in range(8)]
    assert len(set(served)) == 8
    assert s.next() is None


def test_leveled_requires_difficulty(bank):
    with pytest.raises(ValueError):
        QuizSession(bank, mode="leveled", limit=5)
    with pytest.raises(ValueError):
        QuizSession(bank, mode="leveled", difficulty=9, limit=5)


def test_leveled_serves_only_that_level(bank):
    s = QuizSession(bank, mode="leveled", difficulty=5, limit=5, seed=2)
    for _ in range(5):
        assert s.next().difficulty == 5


def test_adaptive_moves_with_correct_and_wrong(bank):
    s = QuizSession(bank, mode="adaptive", limit=6, seed=3)
    assert s.current_difficulty == 2
    q = s.next()
    assert s.submit(q.answer) is True
    assert s.current_difficulty == 3
    q = s.next()
    assert s.submit("definitely not the answer 999") is False
    assert s.current_difficulty == 2


def test_adaptive_clamps_at_bounds(bank):
    s = QuizSession(bank, mode="adaptive", limit=10, seed=4)
    s.current_difficulty = 5
    q = s.next()
    s.submit(q.answer)
    assert s.current_difficulty == 5  # clamped at 5
    s.current_difficulty = 1
    q = s.next()
    s.submit("nope nope 123")
    assert s.current_difficulty == 1  # clamped at 1


def test_skip_does_not_change_difficulty(bank):
    s = QuizSession(bank, mode="adaptive", limit=4, seed=5)
    s.next()
    s.skip()
    assert s.current_difficulty == 2
    assert s.skipped == 1


def test_hint_and_reveal(bank):
    s = QuizSession(bank, mode="random", limit=3, seed=6)
    q = s.next()
    assert s.hint() == q.guidance
    answer, explanation = s.reveal()
    assert answer == q.answer
    assert explanation == q.explanation


def test_no_active_question_raises(bank):
    s = QuizSession(bank, mode="random", limit=3, seed=7)
    with pytest.raises(RuntimeError):
        s.hint()
    with pytest.raises(RuntimeError):
        s.submit("x")
    s.next()
    s.submit("x")  # fine now


def test_results_accounting(bank):
    s = QuizSession(bank, mode="random", limit=4, seed=8)
    q1 = s.next()
    s.submit(q1.answer)          # correct
    q2 = s.next()
    s.submit("wrong 000")        # wrong
    q3 = s.next()
    s.skip()                     # skipped
    r = s.results()
    assert r["served"] == 3
    assert r["attempted"] == 2
    assert r["correct"] == 1
    assert r["skipped"] == 1
    assert r["accuracy"] == 0.5
    s.next()  # 4th
    assert s.results()["served"] == 4


def test_invalid_mode_rejected(bank):
    with pytest.raises(ValueError):
        QuizSession(bank, mode="surprise-me", limit=5)


def test_session_iteration(bank):
    s = QuizSession(bank, mode="random", limit=3, seed=9)
    assert len([q for q in s]) == 3
