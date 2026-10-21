"""CLI subcommand smoke tests."""
import json

from fun_problem.cli import main


def test_stats(capsys, bank):
    assert main(["stats"]) == 0
    out = capsys.readouterr().out
    assert f"Total questions: {bank.count()}" in out
    assert "Difficulty histogram" in out


def test_categories_lists_all(capsys, bank):
    assert main(["categories"]) == 0
    out = capsys.readouterr().out
    for cat in bank.categories():
        assert cat in out


def test_show_known_entry(capsys, bank):
    q = bank.questions()[0]
    assert main(["show", q.id]) == 0
    out = capsys.readouterr().out
    assert "Answer:" in out
    assert q.answer in out


def test_show_unknown_entry(capsys):
    assert main(["show", "NOPE-001"]) == 1
    assert "No entry" in capsys.readouterr().out


def test_quiz_print_study_mode(capsys):
    assert main(["quiz", "--print", "--limit", "2", "--seed", "7"]) == 0
    out = capsys.readouterr().out
    assert out.count("How to approach it") == 2
    assert "Why:" in out


def test_quiz_leveled_needs_difficulty(capsys):
    assert main(["quiz", "--mode", "leveled", "--limit", "2"]) == 2


def test_quiz_interactive_answer_then_quit(capsys, monkeypatch, bank):
    first = bank.sample(n=1, seed=3)[0]
    inputs = iter([first.answer, "q"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    assert main(["quiz", "--limit", "3", "--seed", "3"]) == 0
    out = capsys.readouterr().out
    assert "Correct!" in out
    assert "Session summary" in out


def test_search_reports_matches(capsys):
    assert main(["search", "the", "--limit", "5"]) == 0
    assert "match(es)" in capsys.readouterr().out


def test_export_category(tmp_path):
    out_file = tmp_path / "export.json"
    assert main(["export", "--category", "numeric-sequences", "--out", str(out_file)]) == 0
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data
    assert all(d["category"] == "numeric-sequences" for d in data)
    assert all(d["source"]["license"] for d in data)


def test_no_command_shows_help(capsys):
    assert main([]) == 2
    assert "usage" in capsys.readouterr().out.lower()
