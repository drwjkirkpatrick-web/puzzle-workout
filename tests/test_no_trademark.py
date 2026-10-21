"""The repository must never name any organization, company, or test product.

The banned token is assembled at runtime so this file itself stays clean.
"""
import sqlite3

TEXT_SUFFIXES = {".py", ".md", ".json", ".sql", ".toml", ".yml", ".yaml",
                 ".txt", ".cfg", ".ini", ".gitignore", ".cfg"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "build", "dist"}
SKIP_FILES = {"questions.db"}  # covered by the SQL scan below

TOKEN = "m" + "ensa"


def test_no_banned_token_in_repo_text_files(root):
    offenders = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in SKIP_FILES or path.suffix == ".db":
            continue
        if path.suffix not in TEXT_SUFFIXES and path.name != ".gitignore":
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if TOKEN in text.lower():
            offenders.append(str(path.relative_to(root)))
    assert not offenders, f"banned token found in: {offenders}"


def test_no_banned_token_in_database(bank):
    pattern = f"%{TOKEN}%"
    with sqlite3.connect(bank.path) as conn:
        for column in ("question", "guidance", "answer", "explanation",
                       "tags", "source_title", "source_author",
                       "source_license", "alt_answers"):
            n = conn.execute(
                f"SELECT COUNT(*) FROM questions WHERE {column} LIKE ?",
                (pattern,),
            ).fetchone()[0]
            assert n == 0, f"{n} rows contain the banned token in {column}"
