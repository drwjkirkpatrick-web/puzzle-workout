"""Command-line interface for fun-problem-26."""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .db import CATEGORIES, DIFFICULTY_LABELS, Question, QuestionBank
from .quiz import QuizSession


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="puzzle-workout",
        description=(
            "A friendly, open puzzle trainer: reasoning puzzles with guided "
            "strategies, verified answers, and grounded citations."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--db", help="Path to questions.db (default: shipped database or FUN_PROBLEM_DB)")
    sub = parser.add_subparsers(dest="command")

    quiz = sub.add_parser("quiz", help="Run a quiz session")
    quiz.add_argument("--mode", choices=("random", "leveled", "adaptive"), default="random",
                      help="random: mixed deck | leveled: fixed difficulty | adaptive: level moves with you")
    quiz.add_argument("--difficulty", type=int, choices=range(1, 6), metavar="1-5",
                      help="1=Foundational ... 5=Expert (required for leveled; start level for adaptive)")
    quiz.add_argument("--category", choices=CATEGORIES)
    quiz.add_argument("--limit", type=int, default=10, help="Questions per session")
    quiz.add_argument("--seed", type=int, help="Reproducible shuffle")
    quiz.add_argument("--print", action="store_true",
                      help="Study mode: print questions with answers, no interaction")

    show = sub.add_parser("show", help="Show one full entry by id")
    show.add_argument("id")

    sub.add_parser("categories", help="List categories with counts")
    sub.add_parser("stats", help="Bank statistics")

    search = sub.add_parser("search", help="Search question text")
    search.add_argument("text")
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--answers", action="store_true", help="Include answers in output")

    export = sub.add_parser("export", help="Export entries as JSON")
    export.add_argument("--category", choices=CATEGORIES)
    export.add_argument("--difficulty", type=int, choices=range(1, 6), metavar="1-5")
    export.add_argument("--out", help="Output file (default: stdout)")
    return parser


def _print_question(q: Question, with_answer: bool = True) -> None:
    print(f"[{q.id}] {q.difficulty_label} · {q.category}")
    print(q.question)
    if with_answer:
        print(f"\nHow to approach it: {q.guidance}")
        print(f"\nAnswer: {q.answer}")
        if q.alt_answers:
            print(f"Also accepted: {', '.join(q.alt_answers)}")
        print(f"\nWhy: {q.explanation}")
        print(f"\n{q.source_line()}")


def _summary(session: QuizSession) -> None:
    r = session.results()
    line = f"--- Session summary: {r['correct']}/{r['attempted']} correct on {r['served']} served"
    if r["skipped"]:
        line += f", {r['skipped']} skipped"
    print(line)
    if r["accuracy"] is not None:
        print(f"    accuracy {r['accuracy'] * 100:.0f}%")
    if r["final_difficulty"] is not None:
        print(f"    final adaptive level: {DIFFICULTY_LABELS[r['final_difficulty']]} ({r['final_difficulty']})")


def cmd_quiz(args, bank: QuestionBank) -> int:
    if args.mode == "leveled" and args.difficulty is None:
        print("leveled mode requires --difficulty 1-5")
        return 2
    session = QuizSession(
        bank, mode=args.mode, difficulty=args.difficulty,
        category=args.category, limit=args.limit, seed=args.seed,
    )
    if args.print:
        for q in session:
            _print_question(q)
            print()
        print(f"Printed {session.results()['served']} question(s) (study mode).")
        return 0
    print(f"Starting {args.mode} quiz — up to {args.limit} question(s). "
          "Type 'h' for a hint, 's' to skip, 'q' to quit.")
    while True:
        q = session.next()
        if q is None:
            break
        print(f"\n=== Question {session.position}/{args.limit} — "
              f"{q.difficulty_label} · {q.category} [{q.id}] ===")
        print(q.question)
        while True:
            try:
                raw = input("\n(answer | h=hint | s=skip | q=quit) > ").strip()
            except (EOFError, KeyboardInterrupt):
                raw = "q"
            low = raw.lower()
            if low in ("q", "quit"):
                _summary(session)
                return 0
            if low == "h":
                print(f"Hint: {session.hint()}")
                continue
            if low == "s":
                session.skip()
                answer, explanation = session.reveal()
                print(f"Skipped. The answer: {answer}\nWhy: {explanation}")
                print(q.source_line())
                break
            ok = session.submit(raw)
            answer, explanation = session.reveal()
            if ok:
                print("Correct!")
            else:
                print(f"Not quite. The answer: {answer}")
            print(f"Why: {explanation}")
            print(q.source_line())
            break
    _summary(session)
    return 0


def cmd_show(args, bank: QuestionBank) -> int:
    q = bank.get(args.id.upper())
    if q is None:
        print(f"No entry with id {args.id!r}")
        return 1
    _print_question(q)
    return 0


def cmd_categories(bank: QuestionBank) -> int:
    cats = bank.categories()
    width = max(len(c) for c in cats) if cats else 0
    for cat, count in cats.items():
        print(f"{cat.ljust(width)}  {count}")
    return 0


def cmd_stats(bank: QuestionBank) -> int:
    stats = bank.stats()
    print(f"Total questions: {stats['total']}")
    print(f"Categories ({len(stats['categories'])}):")
    for cat, count in stats["categories"].items():
        print(f"  {cat}: {count}")
    print("Difficulty histogram:")
    for level in range(1, 6):
        count = stats["histogram"].get(level, 0)
        label = DIFFICULTY_LABELS[level]
        bar = "#" * count
        print(f"  {level} {label:<12} {count:4}  {bar}")
    kinds = stats["source_kinds"]
    print(f"Source kinds: {json.dumps(kinds, sort_keys=True)}")
    print(f"Distinct cited works: {stats['distinct_cited_works']}")
    return 0


def cmd_search(args, bank: QuestionBank) -> int:
    hits = bank.search(args.text, limit=args.limit)
    if not hits:
        print("No matches.")
        return 0
    for q in hits:
        first_line = q.question.splitlines()[0]
        print(f"[{q.id}] {q.difficulty_label} · {q.category}: {first_line}")
        if args.answers:
            print(f"    -> {q.answer}")
    print(f"{len(hits)} match(es). Use 'fun-problem show <id>' for the full entry.")
    return 0


def cmd_export(args, bank: QuestionBank) -> int:
    entries = bank.questions(category=args.category, difficulty=args.difficulty)
    data = [q.to_dict() for q in entries]
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(payload + "\n")
        print(f"Wrote {len(data)} entries to {args.out}")
    else:
        print(payload)
    return 0


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 2
    try:
        bank = QuestionBank(args.db)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1
    handlers = {
        "quiz": lambda: cmd_quiz(args, bank),
        "show": lambda: cmd_show(args, bank),
        "categories": lambda: cmd_categories(bank),
        "stats": lambda: cmd_stats(bank),
        "search": lambda: cmd_search(args, bank),
        "export": lambda: cmd_export(args, bank),
    }
    return handlers[args.command]()


if __name__ == "__main__":
    sys.exit(main())
