"""Build determinism and generated-artifact checks."""
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_build(db_out):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_db.py"), "--db", str(db_out)],
        cwd=str(ROOT), capture_output=True, text=True,
    )


def test_rebuild_equals_shipped(tmp_path, bank):
    out = tmp_path / "rebuilt.db"
    proc = _run_build(out)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    query = "SELECT id, category, difficulty, question, answer FROM questions ORDER BY id"
    with sqlite3.connect(out) as rebuilt:
        rows_a = rebuilt.execute(query).fetchall()
    with sqlite3.connect(bank.path) as shipped:
        rows_b = shipped.execute(query).fetchall()
    assert rows_a == rows_b
    assert len(rows_b) >= 250


def test_data_sources_doc_lists_every_cited_work(bank):
    doc = (ROOT / "docs" / "DATA_SOURCES.md").read_text(encoding="utf-8")
    with sqlite3.connect(bank.path) as conn:
        titles = [r[0] for r in conn.execute(
            "SELECT DISTINCT source_title FROM questions WHERE source_kind != 'original'"
        )]
    assert titles, "expected at least one cited work"
    for title in titles:
        assert title in doc, f"missing from DATA_SOURCES.md: {title}"


def test_generated_doc_is_declared_generated():
    doc = (ROOT / "docs" / "DATA_SOURCES.md").read_text(encoding="utf-8")
    assert "do not edit by hand" in doc
