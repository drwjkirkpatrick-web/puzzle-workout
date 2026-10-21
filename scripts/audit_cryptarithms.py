#!/usr/bin/env python3
"""Brute-force audit of cryptarithm entries.

Parses each 'WORD + WORD = WORD' equation from the question text, brute-forces
all digit assignments, and checks: (1) a unique solution exists, (2) the entry's
stated answer matches it. Usage:
    python3 scripts/audit_cryptarithms.py data/batches/cryptarithms_codes_a.json
"""
import itertools
import json
import re
import sys

EQ_RE = re.compile(r"\b([A-Z]{1,10}) \+ ([A-Z]{1,10}) = ([A-Z]{1,10})\b")
ASSIGN_RE = re.compile(r"([A-Z])\s*=\s*(\d)")


def solutions(a, b, c):
    letters = sorted(set(a + b + c))
    if len(letters) > 10:
        return []
    found = []
    for perm in itertools.permutations(range(10), len(letters)):
        m = dict(zip(letters, perm))
        if m[a[0]] == 0 or m[b[0]] == 0 or m[c[0]] == 0:
            continue
        if int("".join(str(m[ch]) for ch in a)) + int("".join(str(m[ch]) for ch in b)) \
                == int("".join(str(m[ch]) for ch in c)):
            found.append(m)
    return found


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    data = json.loads(open(argv[1], encoding="utf-8").read())
    failures = 0
    checked = 0
    for i, entry in enumerate(data):
        text = entry["question"] + " " + entry["explanation"]
        eq = EQ_RE.search(entry["question"])
        if not eq:
            if "cryptarithm" in entry["tags"] or "+" in entry["question"]:
                print(f"entry[{i}]: NO canonical 'A + B = C' equation found")
                failures += 1
            continue
        a, b, c = eq.groups()
        sols = solutions(a, b, c)
        checked += 1
        if len(sols) != 1:
            print(f"entry[{i}]: {a} + {b} = {c} -> {len(sols)} solution(s) (need exactly 1)")
            failures += 1
            continue
        sol = sols[0]
        stated = {m[0]: int(m[1]) for m in ASSIGN_RE.findall(entry["explanation"])}
        if stated and {k: v for k, v in stated.items()} != sol:
            overlap = {k for k in stated if k in sol}
            mismatched = any(stated[k] != sol[k] for k in overlap)
            if mismatched:
                print(f"entry[{i}]: stated assignment {stated} contradicts unique solution {sol}")
                failures += 1
                continue
        print(f"entry[{i}]: OK {a} + {b} = {c} unique solution verified")
    print(f"checked {checked} equation(s), {failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
