"""The author gate: every batch must pass the child validator; bad input fails."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MAP = json.loads((ROOT / "data" / "batches" / "BATCH_MAP.json").read_text(encoding="utf-8"))


def run_validator(*args):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_one.py"), *map(str, args)],
        cwd=str(ROOT), capture_output=True, text=True,
    )


def test_exemplar_passes_without_map():
    proc = run_validator(ROOT / "data" / "exemplar" / "exemplar_entries.json", "--no-map")
    assert proc.returncode == 0, proc.stdout
    assert "PASS" in proc.stdout


@pytest.mark.parametrize("name", [b["file"] for b in MAP["batches"]])
def test_batch_passes_validator(name):
    proc = run_validator(ROOT / "data" / "batches" / name)
    assert proc.returncode == 0, proc.stdout
    assert "PASS" in proc.stdout


def test_validator_rejects_bad_input(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('[{"category": "bogus"}]', encoding="utf-8")
    proc = run_validator(bad, "--no-map")
    assert proc.returncode == 1
    assert "FAIL" in proc.stdout
