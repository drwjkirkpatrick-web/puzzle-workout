#!/usr/bin/env python3
"""Build data/questions.db from data/batches/*.json.

The batch files are the source of truth; every one must pass
scripts/validate_one.py (the same gate the authors used) before it enters the
database. Also regenerates docs/DATA_SOURCES.md from the built data.

Usage:
    python3 scripts/build_db.py [--allow-missing] [--db PATH]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "data" / "batches" / "BATCH_MAP.json"
SCHEMA_PATH = ROOT / "schema" / "001_schema.sql"
DEFAULT_DB = ROOT / "data" / "questions.db"

INSERT_SQL = (
    "INSERT INTO questions (id, category, difficulty, question, guidance, "
    "answer, alt_answers, explanation, tags, source_kind, source_title, "
    "source_author, source_year, source_url, source_license, source_accessed) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)


def _norm(text) -> str:
    return re.sub(r"\s+", " ", str(text)).strip().casefold()


def _tokens(text):
    return set(_norm(text).split())


def _jaccard(a, b) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load_batches(allow_missing=False):
    mapping = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    prefixes = mapping["categories"]
    entries = []
    missing = []
    for file_index, batch in enumerate(mapping["batches"]):
        path = ROOT / "data" / "batches" / batch["file"]
        if not path.exists():
            if allow_missing:
                missing.append(batch["file"])
                continue
            print(f"FAIL: missing batch file {path}")
            sys.exit(1)
        check = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_one.py"), str(path)],
            capture_output=True, text=True,
        )
        if check.returncode != 0:
            print(f"FAIL: {batch['file']} did not pass the validator:")
            print(check.stdout.strip() or check.stderr.strip())
            sys.exit(1)
        for entry_index, entry in enumerate(json.loads(path.read_text(encoding="utf-8"))):
            entries.append({
                "entry": entry,
                "file_index": file_index,
                "entry_index": entry_index,
                "prefix": prefixes[entry["category"]]["prefix"],
            })
    if missing:
        print(f"WARNING: {len(missing)} batch file(s) not yet present "
              f"(--allow-missing): {', '.join(missing)}")
    return entries


def _bigrams(text):
    toks = _norm(text).split()
    return {f"{a} {b}" for a, b in zip(toks, toks[1:])}


def dedupe(entries):
    """Exact + near-duplicate detection.

    Near-duplicates compare token bigrams (which keep grid arrangements
    distinct) after a document-frequency filter, so shared boilerplate
    ("each cell of a 3x3 grid holds...") cannot flag two different puzzles
    as duplicates.
    """
    kept, dropped = [], []
    seen_exact = {}
    seen_sigs = []
    df = Counter()
    all_sigs = [_bigrams(item["entry"]["question"]) for item in entries]
    for sig in all_sigs:
        for bigram in sig:
            df[bigram] += 1
    n = max(1, len(entries))
    common = {b for b, c in df.items() if c > max(3, 0.10 * n)}

    def signature(sig):
        return sig - common or sig

    for item, sig in zip(entries, all_sigs):
        nq = _norm(item["entry"]["question"])
        if nq in seen_exact:
            dropped.append((item, f"exact duplicate of {seen_exact[nq]}"))
            continue
        key = signature(sig)
        dup_of = None
        for other in seen_sigs:
            if _jaccard(key, other["key"]) >= 0.85:
                dup_of = f"near-duplicate of {other['label']}"
                break
        if dup_of:
            dropped.append((item, dup_of))
            continue
        seen_exact[nq] = f"batch {item['file_index']}[{item['entry_index']}]"
        seen_sigs.append({
            "label": f"batch {item['file_index']}[{item['entry_index']}]",
            "key": key,
        })
        kept.append(item)
    return kept, dropped


def assign_ids(entries):
    per_category = defaultdict(list)
    for item in entries:
        per_category[item["entry"]["category"]].append(item)
    assigned = []
    for category, items in per_category.items():
        items.sort(key=lambda it: (it["entry"]["difficulty"], it["file_index"], it["entry_index"]))
        for n, item in enumerate(items, start=1):
            clone = dict(item)
            clone["id"] = f"{item['prefix']}-{n:03d}"
            assigned.append(clone)
    return assigned


def row_from(item):
    e = item["entry"]
    s = e["source"]
    return (
        item["id"], e["category"], e["difficulty"], e["question"], e["guidance"],
        e["answer"], json.dumps(e["alt_answers"], ensure_ascii=False),
        e["explanation"], json.dumps(e["tags"], ensure_ascii=False),
        s["kind"], s["title"], s["author"], s["year"], s["url"], s["license"],
        s["accessed"],
    )


def write_db(assigned, db_path: Path):
    fd, tmp_name = tempfile.mkstemp(suffix=".db", dir=str(db_path.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    tmp.unlink()  # start from a truly empty file, not mkstemp's placeholder
    try:
        conn = sqlite3.connect(tmp)
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.executemany(INSERT_SQL, [row_from(item) for item in assigned])
        conn.commit()
        conn.close()
        os.replace(tmp, db_path)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


def write_data_sources(assigned):
    kinds = Counter(item["entry"]["source"]["kind"] for item in assigned)
    works = {}
    for item in assigned:
        s = item["entry"]["source"]
        if s["kind"] == "original":
            continue
        work = works.setdefault(s["title"], {
            "count": 0, "kind": s["kind"], "author": s["author"],
            "license": s["license"], "accessed": s["accessed"], "url": s["url"],
        })
        work["count"] += 1
        if s["author"]:
            work["author"] = work["author"] or s["author"]
        if s["url"]:
            work["url"] = work["url"] or s["url"]
    total = len(assigned)
    lines = [
        "# Data Sources",
        "",
        "> Generated by `scripts/build_db.py` from `data/batches/*.json` — do not edit by hand.",
        "> Every adapted entry carries the URL its adapter actually fetched, the license,",
        "> and the access date; original entries are composed for this project (MIT).",
        "",
        "## Summary",
        "",
        f"- **{total} questions** across 10 categories",
        f"- Original: **{kinds.get('original', 0)}**, adapted from public-domain works: "
        f"**{kinds.get('public-domain', 0)}**, adapted from open-license works: **{kinds.get('open-license', 0)}**",
        f"- Distinct cited works: **{len(works)}**",
        "",
        "## Cited works",
        "",
        "| Work | Author | Kind | License | Accessed | Questions | URL |",
        "|---|---|---|---|---|---|---|",
    ]
    for title, w in sorted(works.items(), key=lambda kv: (-kv[1]["count"], kv[0])):
        author = w["author"] or "—"
        url = w["url"] or "—"
        lines.append(
            f"| {title} | {author} | {w['kind']} | {w['license']} | "
            f"{w['accessed']} | {w['count']} | {url} |"
        )
    lines += [
        "",
        "## Provenance model",
        "",
        "- `original` — composed for this project. License: MIT (project original).",
        "- `public-domain` — adapted (rewritten in modern English) from a pre-1931",
        "  publication; the URL is the exact page the adapter fetched.",
        "- `open-license` — adapted from CC-licensed material with attribution.",
        "- Batch files are the source of truth; `data/questions.db` is a build artifact.",
        "",
    ]
    (ROOT / "docs" / "DATA_SOURCES.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--allow-missing", action="store_true",
                    help="Skip map batches whose file does not exist yet (interim builds)")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    args = ap.parse_args(argv)

    entries = load_batches(allow_missing=args.allow_missing)
    if not entries:
        print("FAIL: no entries loaded")
        return 1
    kept, dropped = dedupe(entries)
    assigned = assign_ids(kept)
    write_db(assigned, Path(args.db))
    write_data_sources(assigned)

    per_cat = Counter(item["entry"]["category"] for item in assigned)
    histogram = Counter(item["entry"]["difficulty"] for item in assigned)
    print(f"BUILT {len(assigned)} questions into {args.db}")
    for cat in sorted(per_cat):
        print(f"  {cat}: {per_cat[cat]}")
    print("  histogram:", dict(sorted(histogram.items())))
    if dropped:
        print(f"  dropped {len(dropped)} duplicate(s):")
        for item, reason in dropped:
            print(f"    - batch {item['file_index']}[{item['entry_index']}]: {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
