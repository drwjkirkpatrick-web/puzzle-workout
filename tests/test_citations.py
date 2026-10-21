"""Grounded-citations discipline: cited URLs are registered in the research ledger."""
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "research" / "ledger.json"


def _ledger_urls():
    text = LEDGER.read_text(encoding="utf-8")
    data = json.loads(text)
    urls = set()
    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "url" and isinstance(v, str):
                    urls.add(v)
                else:
                    walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)
    walk(data)
    return urls


def test_every_cited_url_is_in_the_ledger(bank):
    ledger_urls = _ledger_urls()
    assert ledger_urls, "ledger is empty"
    with sqlite3.connect(bank.path) as conn:
        urls = [r[0] for r in conn.execute(
            "SELECT DISTINCT source_url FROM questions WHERE source_kind != 'original'"
        )]
    assert urls, "expected at least one adapted entry"
    for url in urls:
        assert url in ledger_urls, f"cited URL not registered in ledger: {url}"


def test_all_cited_urls_are_https(bank):
    with sqlite3.connect(bank.path) as conn:
        urls = [r[0] for r in conn.execute(
            "SELECT DISTINCT source_url FROM questions WHERE source_url IS NOT NULL"
        )]
    for url in urls:
        assert url.startswith("https://"), f"non-https citation: {url}"
