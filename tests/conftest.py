"""Shared fixtures for fun-problem-26 tests."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fun_problem.db import QuestionBank  # noqa: E402


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def bank() -> QuestionBank:
    return QuestionBank()


@pytest.fixture(scope="session")
def questions(bank):
    return bank.questions()
