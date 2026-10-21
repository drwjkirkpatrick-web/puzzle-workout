"""QuestionBank behavior: counts, filters, sampling, search, stats."""
from fun_problem.db import DIFFICULTY_LABELS, QuestionBank


def test_total_count_at_least_250(bank):
    assert bank.count() >= 250


def test_all_ten_categories_present(bank):
    cats = bank.categories()
    assert len(cats) == 10
    assert all(count >= 20 for count in cats.values())


def test_every_difficulty_well_populated(bank):
    hist = bank.difficulty_histogram()
    assert set(hist) == {1, 2, 3, 4, 5}
    assert all(count >= 25 for count in hist.values())


def test_unique_ids(bank):
    ids = [q.id for q in bank.questions()]
    assert len(ids) == len(set(ids)) == bank.count()


def test_id_prefix_matches_category(bank):
    prefixes = {"numeric-sequences": "NS", "letter-series": "LS",
                "verbal-analogies": "VA", "odd-one-out": "OO",
                "logical-deduction": "LD", "math-word-problems": "MW",
                "matrix-patterns": "MP", "lateral-thinking": "LT",
                "cryptarithms-codes": "CC", "spatial-reasoning": "SR"}
    for q in bank.questions():
        assert q.id.startswith(prefixes[q.category] + "-")


def test_seeded_sample_is_reproducible(bank):
    a = [q.id for q in bank.sample(n=20, seed=42)]
    b = [q.id for q in bank.sample(n=20, seed=42)]
    assert a == b


def test_sample_without_replacement(bank):
    ids = [q.id for q in bank.sample(n=250, seed=1)]
    assert len(ids) == len(set(ids))


def test_sample_n_larger_than_pool(bank):
    pool = bank.count(difficulty=1)
    got = bank.sample(n=10_000, difficulty=1)
    assert len(got) == pool


def test_leveled_filter(bank):
    for q in bank.sample(n=15, difficulty=3, seed=5):
        assert q.difficulty == 3
    assert bank.count(difficulty=3) == sum(1 for q in bank.questions(difficulty=3))


def test_category_filter(bank):
    for q in bank.sample(n=15, category="letter-series", seed=6):
        assert q.category == "letter-series"


def test_get_known_and_unknown(bank):
    known = bank.questions()[0]
    assert bank.get(known.id).id == known.id
    assert bank.get("NOPE-999") is None


def test_search_finds_and_misses(bank):
    hits = bank.search("prime", limit=50)
    assert hits and all(
        "prime" in (q.question + q.guidance + q.explanation + " ".join(q.tags)).lower()
        for q in hits
    )
    assert bank.search("zzzqqx-no-such-term") == []


def test_stats_consistent(bank):
    stats = bank.stats()
    assert stats["total"] == bank.count()
    assert sum(stats["categories"].values()) == stats["total"]
    assert sum(stats["histogram"].values()) == stats["total"]
    assert sum(stats["source_kinds"].values()) == stats["total"]


def test_difficulty_labels(bank):
    for q in bank.questions()[:50]:
        assert q.difficulty_label == DIFFICULTY_LABELS[q.difficulty]
