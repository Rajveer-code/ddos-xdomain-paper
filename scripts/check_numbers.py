"""
Verify that every numeric claim in paper/*.md traces to a value in results/*.json.

The rule this project runs on is that no number reaches the manuscript except from a run.
That rule is worth nothing unless it is checked, because the failure mode is silent:
a value is edited in one table, its twin three sections away is not, and the paper ships
with two different figures for the same quantity.

Every decimal literal in the manuscript is extracted and matched against the flattened
set of values in results/*.json, at the precision it is written to. Numbers that cannot
be matched are printed for manual review -- some are legitimate (counts quoted from a
cited paper, section numbers, years), which is exactly why this reports rather than fails.

    python scripts/check_numbers.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.config import PAPER, PROJECT, RESULTS

# Literals that are never data: section numbers, years, small counts, percentages of 100.
ALLOW = {
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "17", "18",
    "19", "20", "39", "43", "50", "76", "80", "95", "99", "100", "240", "400", "500",
    "1000", "2000", "1.0", "0.5", "0.0",
    "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2024", "2025", "2026",
    "2027",
    "2402.10974", "2605.04407",  # arXiv identifiers, not measurements
}

NUM = re.compile(r"(?<![\w.])(-?\d+(?:,\d{3})*(?:\.\d+)?)(?![\w])")


def flatten(obj, out: set[float]) -> None:
    if isinstance(obj, dict):
        for v in obj.values():
            flatten(v, out)
    elif isinstance(obj, list):
        for v in obj:
            flatten(v, out)
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        try:
            f = float(obj)
        except (TypeError, ValueError):
            return
        if f == f:  # not NaN
            out.add(f)


WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
         8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}


def fmt_claim(value, c: dict) -> str:
    """Render a stored value the way the manuscript writes it."""
    kind, d = c.get("fmt", "plain"), c.get("decimals", 0)
    if kind == "pct_range":
        lo, hi = value
        return f"{lo:.{d}f}% to {hi:.{d}f}%"
    if c.get("one_minus"):
        value = 1 - value
    if kind == "word":
        return WORDS[int(value)]
    if kind == "thousands":
        return f"{int(value):,}"
    if kind == "pct":
        return f"{100 * value:.{d}f}%"
    text = f"{value:.{d}f}"
    if kind == "signed":
        text = ("−" + text[1:]) if value < 0 else ("+" + text)
    return text


def check_claims() -> int:
    """Keyed check: each registered claim must equal its result key at the written precision."""
    reg = json.loads((PAPER / "claims.json").read_text(encoding="utf-8"))["claims"]
    manuscript = (PAPER / "manuscript.md").read_text(encoding="utf-8")
    failures = 0
    for c in reg:
        node = json.loads((RESULTS / c["file"]).read_text(encoding="utf-8"))
        for key in c["path"]:
            node = node[key]
        expected = fmt_claim(node, c)
        problems = []
        if expected != c["text"]:
            problems.append(f"result gives {expected!r}")
        if c["text"] not in manuscript:
            problems.append("text not found in manuscript.md")
        status = "ok  " if not problems else "FAIL"
        failures += bool(problems)
        print(f"  {status} {c['text']!r:>18}  <- {c['file']}:{'/'.join(c['path'])}"
              + (f"  [{'; '.join(problems)}]" if problems else ""))
    print(f"\nKeyed claims: {len(reg) - failures}/{len(reg)} pass\n")
    return failures


def main() -> int:
    failures = check_claims()
    values: set[float] = set()
    files = sorted(RESULTS.glob("*.json"))
    for p in files:
        try:
            flatten(json.loads(p.read_text(encoding="utf-8")), values)
        except json.JSONDecodeError as e:
            print(f"  ! could not parse {p.name}: {e}")
    print(f"Loaded {len(values):,} numeric values from {len(files)} result files\n")

    vals = sorted(values)
    # AUDIT.md, OUTLINE.md and REFERENCES_VERIFIED.md are working documents about the paper, not the paper.
    # Their numbers are word counts, literal counts and venue fees, which correctly
    # have no backing result file.
    META = {"AUDIT.md", "OUTLINE.md", "REFERENCES_VERIFIED.md"}
    docs = [d for d in sorted(PAPER.glob("*.md")) if d.name not in META]
    docs += [PROJECT / "FINDINGS.md"]
    total = matched = 0
    unmatched: list[tuple[str, int, str]] = []

    for doc in docs:
        if not doc.exists():
            continue
        text = doc.read_text(encoding="utf-8")
        # Bibliographic numbers (years, volumes, pages, arXiv ids) are citations, not
        # measurements, and correctly have no backing result file.
        cut = text.find("## References")
        if cut != -1:
            text = text[:cut]
        for ln, line in enumerate(text.splitlines(), 1):
            if line.strip().startswith(("<!--", "`[PENDING", "[PENDING")):
                continue
            for tok in NUM.findall(line):
                clean = tok.replace(",", "")
                if tok in ALLOW or clean in ALLOW:
                    continue
                total += 1
                try:
                    x = abs(float(clean))
                except ValueError:
                    continue
                # Match at the precision the manuscript states, plus a percentage form.
                dec = len(clean.split(".")[1]) if "." in clean else 0
                tol = 0.5 * (10 ** -dec) if dec else 0.5
                if any(abs(abs(v) - x) <= tol or abs(abs(v) * 100 - x) <= tol
                       for v in vals):
                    matched += 1
                else:
                    unmatched.append((doc.name, ln, tok))

    print(f"{matched}/{total} numeric literals matched a value in results/")
    if unmatched:
        print(f"\n{len(unmatched)} for manual review "
              f"(cited literature, structural numbers, or genuine drift):")
        for name, ln, tok in unmatched:
            print(f"  {name}:{ln}  {tok}")
    else:
        print("\nEvery numeric literal matches some value in results/ (a weak check; "
              "the keyed claims above are the strong one).")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
