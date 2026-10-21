#!/usr/bin/env python3
"""Validate one fun-problem-26 question batch file.

Usage:
    python3 scripts/validate_one.py data/batches/<file>.json
    python3 scripts/validate_one.py data/exemplar/exemplar_entries.json --no-map

Checks schema, content rules, source blocks, difficulty histogram, in-file
duplicates, and the organization-name ban. Exit status 0 == PASS.
Expected count and difficulty histogram are read from data/batches/BATCH_MAP.json
by file name unless --no-map is given.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "data" / "batches" / "BATCH_MAP.json"

CATEGORIES = {
    "numeric-sequences", "letter-series", "verbal-analogies", "odd-one-out",
    "logical-deduction", "math-word-problems", "matrix-patterns",
    "lateral-thinking", "cryptarithms-codes", "spatial-reasoning",
}
ENTRY_KEYS = {
    "category", "difficulty", "question", "guidance", "answer", "alt_answers",
    "explanation", "tags", "source",
}
SOURCE_KEYS = {"kind", "title", "author", "year", "url", "license", "accessed"}
KINDS = {"original", "public-domain", "open-license"}
LICENSES = {
    "Public domain (US)", "Public Domain Mark 1.0",
    "CC BY-SA 4.0", "CC0 1.0", "MIT (project original)",
}
# Banned organization name token(s) are assembled at runtime so the literal
# never appears anywhere in this repository.
FORBIDDEN_TOKENS = ("m" + "ensa",)
ORIGINAL_TITLE = "Original composition for fun-problem-26"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _iso_ok(value):
    if not isinstance(value, str) or not DATE_RE.match(value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _norm(text):
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def validate_source(src, errors, p):
    if not isinstance(src, dict):
        errors.append(f"{p}: source must be an object")
        return
    keys = set(src)
    if keys != SOURCE_KEYS:
        missing, extra = SOURCE_KEYS - keys, keys - SOURCE_KEYS
        if missing:
            errors.append(f"{p}.source: missing keys {sorted(missing)}")
        if extra:
            errors.append(f"{p}.source: unexpected keys {sorted(extra)}")
        return
    kind = src.get("kind")
    if kind not in KINDS:
        errors.append(f"{p}.source: kind must be one of {sorted(KINDS)}")
        return
    license_ = src.get("license")
    if license_ not in LICENSES:
        errors.append(f"{p}.source: license {license_!r} not in whitelist {sorted(LICENSES)}")
    if not _iso_ok(src.get("accessed")):
        errors.append(f"{p}.source: accessed must be a valid YYYY-MM-DD date")
    if not isinstance(src.get("year"), (int, type(None))):
        errors.append(f"{p}.source: year must be an integer or null")
    if kind == "original":
        if src.get("title") != ORIGINAL_TITLE:
            errors.append(f"{p}.source: original entries must use title {ORIGINAL_TITLE!r}")
        if license_ != "MIT (project original)":
            errors.append(f"{p}.source: original entries must use license 'MIT (project original)'")
        if src.get("author") is not None or src.get("year") is not None or src.get("url") is not None:
            errors.append(f"{p}.source: original entries use author/year/url null")
    else:
        if not isinstance(src.get("title"), str) or not src.get("title", "").strip():
            errors.append(f"{p}.source: title required for {kind}")
        url = src.get("url")
        if not isinstance(url, str) or not url.startswith("https://"):
            errors.append(f"{p}.source: url must be an https:// page you actually fetched")
        if kind == "public-domain" and license_ not in {"Public domain (US)", "Public Domain Mark 1.0"}:
            errors.append(f"{p}.source: public-domain entries need a public-domain license value")
        if kind == "open-license" and license_ not in {"CC BY-SA 4.0", "CC0 1.0"}:
            errors.append(f"{p}.source: open-license entries need a CC license value")


def validate_entry(entry, idx):
    errors = []
    p = f"entry[{idx}]"
    if not isinstance(entry, dict):
        errors.append(f"{p}: must be a JSON object")
        return errors
    keys = set(entry)
    if keys != ENTRY_KEYS:
        missing, extra = ENTRY_KEYS - keys, keys - ENTRY_KEYS
        if missing:
            errors.append(f"{p}: missing keys {sorted(missing)}")
        if extra:
            errors.append(f"{p}: unexpected keys {sorted(extra)}")
    if entry.get("category") not in CATEGORIES:
        errors.append(f"{p}: category {entry.get('category')!r} is not one of the 10 canonical categories")
    diff = entry.get("difficulty")
    if isinstance(diff, bool) or not isinstance(diff, int) or not 1 <= diff <= 5:
        errors.append(f"{p}: difficulty must be an integer 1-5, got {diff!r}")
    question = entry.get("question")
    if not isinstance(question, str) or len(question.strip()) < 15:
        errors.append(f"{p}: question must be a self-contained string of >= 15 chars")
    guidance = entry.get("guidance")
    if not isinstance(guidance, str) or len(guidance.strip()) < 60:
        errors.append(f"{p}: guidance must be >= 60 chars and teach a transferable strategy")
    answer = entry.get("answer")
    if not isinstance(answer, str) or not 1 <= len(answer.strip()) <= 60:
        errors.append(f"{p}: answer must be a short non-empty string (<= 60 chars)")
    alts = entry.get("alt_answers")
    if not isinstance(alts, list) or any(
        not isinstance(a, str) or not a.strip() for a in alts
    ):
        errors.append(f"{p}: alt_answers must be a list of non-empty strings")
    explanation = entry.get("explanation")
    if not isinstance(explanation, str) or len(explanation.strip()) < 80:
        errors.append(f"{p}: explanation must be >= 80 chars and prove the answer")
    tags = entry.get("tags")
    if (
        not isinstance(tags, list)
        or not 1 <= len(tags) <= 4
        or any(not isinstance(t, str) or not t.strip() or len(t) > 24 for t in tags)
    ):
        errors.append(f"{p}: tags must be 1-4 short strings")
    validate_source(entry.get("source"), errors, p)
    blob = json.dumps(entry, ensure_ascii=False, default=str).lower()
    for token in FORBIDDEN_TOKENS:
        if token in blob:
            errors.append(f"{p}: contains a banned organization token")
    return errors


def main(argv):
    no_map = "--no-map" in argv
    positional = [a for a in argv[1:] if not a.startswith("--")]
    if len(positional) != 1:
        print(__doc__)
        return 2
    path = Path(positional[0])
    if not path.is_absolute():
        path = (Path.cwd() / path) if (Path.cwd() / path).exists() else (ROOT / path)
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: could not read/parse {path}: {exc}")
        return 1
    if not isinstance(data, list) or not data:
        print(f"FAIL: {path.name} must be a non-empty JSON array")
        return 1

    expected = None
    if not no_map:
        try:
            mapping = json.loads(MAP_PATH.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL: could not read BATCH_MAP.json: {exc}")
            return 1
        expected = next((b for b in mapping["batches"] if b["file"] == path.name), None)
        if expected is None:
            print(f"FAIL: {path.name} not found in data/batches/BATCH_MAP.json")
            return 1

    errors = []
    histogram = {}
    seen = {}
    for i, entry in enumerate(data):
        errors.extend(validate_entry(entry, i))
        if isinstance(entry, dict):
            histogram[entry.get("difficulty")] = histogram.get(entry.get("difficulty"), 0) + 1
            nq = _norm(entry.get("question"))
            if nq in seen:
                errors.append(f"entry[{i}]: duplicate question of entry[{seen[nq]}]")
            else:
                seen[nq] = i

    if expected:
        if len(data) != expected["count"]:
            errors.append(f"count: expected {expected['count']}, got {len(data)}")
        exp_hist = {int(k): v for k, v in expected["difficulty"].items()}
        if histogram != exp_hist:
            errors.append(f"difficulty histogram: expected {exp_hist}, got {histogram}")

    if errors:
        for err in errors:
            print(f"FAIL: {err}")
        print(f"RESULT: {len(errors)} error(s) in {path.name}")
        return 1
    print(
        f"PASS: {len(data)} entries in {path.name} — schema, sources, "
        f"histogram, duplicate-scan, and organization-name scan all clean"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))