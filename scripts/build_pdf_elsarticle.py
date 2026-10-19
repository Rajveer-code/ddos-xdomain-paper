"""
Build the Computer Networks (Elsevier, elsarticle) submission from paper/manuscript.md.

Writes a self-contained upload folder, paper/elsarticle/, holding main.tex, the figures it
uses under figures/ (relative paths), and main.pdf. It compiles with pdfLaTeX, which both
arXiv and Elsevier's system use, so the same folder serves as the arXiv source package.

Reuses the IEEE builder's markdown conversion; only the front matter, the end-matter
declarations Elsevier requires, figure paths and Unicode handling differ.

    python scripts/build_pdf_elsarticle.py
    python scripts/build_pdf_elsarticle.py --tex-only
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.config import FIGURES, PAPER
from scripts.build_pdf import inline
from scripts.build_pdf_ieee import convert, convert_references, extract_front_matter

SRC = PAPER / "manuscript.md"
OUT = PAPER / "elsarticle"
TEX = OUT / "main.tex"

AUTHOR = "Rajveer Singh Pall"
EMAIL = "rajveerpall04@gmail.com"
AFFIL = ("organization={Department of Computer Science and Business Systems, Gyan Ganga "
         "Institute of Technology and Sciences}, city={Jabalpur}, country={India}")

# Elsevier end matter. Funding confirmed by the author 2026-10-19 (no funding). The AI
# declaration was finalised with the author on 2026-10-19.
DECLARATIONS = r"""
\section*{CRediT authorship contribution statement}
\textbf{Rajveer Singh Pall:} Conceptualization, Methodology, Software, Validation, Formal
analysis, Investigation, Data curation, Writing -- original draft, Writing -- review \&
editing, Visualization.

\section*{Declaration of competing interest}
The author declares that he has no known competing financial interests or personal
relationships that could have appeared to influence the work reported in this paper.

\section*{Funding}
This research did not receive any specific grant from funding agencies in the public,
commercial, or not-for-profit sectors.

\section*{Declaration of generative AI and AI-assisted technologies in the manuscript preparation process}
During the preparation of this work the author used Claude Code (Anthropic) in order to edit
and restructure manuscript text, check every reported number against the stored result files,
verify bibliographic references against Crossref and arXiv, and draft revisions in response to
an AI-assisted pre-submission audit; and ChatGPT (OpenAI) in order to obtain a critical review
of an earlier draft. AI use in code development and analysis is described in Section 3.8. After using these tools, the
author reviewed and edited the content as needed and takes full responsibility for the content
of the published article.
"""

# pdfLaTeX has no glyphs for these by default; map each to a LaTeX equivalent.
UNICODE = {
    "−": r"\ensuremath{-}", "→": r"\ensuremath{\rightarrow}", "↔": r"\ensuremath{\leftrightarrow}",
    "×": r"\ensuremath{\times}", "≠": r"\ensuremath{\neq}", "≤": r"\ensuremath{\leq}",
    "≥": r"\ensuremath{\geq}", "ρ": r"\ensuremath{\rho}", "≈": r"\ensuremath{\approx}",
    "Δ": r"\ensuremath{\Delta}", "±": r"\ensuremath{\pm}", "·": r"\ensuremath{\cdot}",
    "—": "---", "–": "--", "‘": "`", "’": "'", "“": "``", "”": "''", "…": r"\ldots{}",
    "é": r"\'e", "É": r"\'E", "á": r"\'a", "ş": r"\c{s}", "Ş": r"\c{S}", "ü": r'\"u',
    "ö": r'\"o', "ç": r"\c{c}", "ı": r"\i{}", "ğ": r"\u{g}", "’": "'",
    "⁰": r"\textsuperscript{0}", "¹": r"\textsuperscript{1}", "²": r"\textsuperscript{2}",
    "³": r"\textsuperscript{3}", "⁴": r"\textsuperscript{4}", "⁵": r"\textsuperscript{5}",
    "⁶": r"\textsuperscript{6}", "⁷": r"\textsuperscript{7}", "⁸": r"\textsuperscript{8}",
    "⁹": r"\textsuperscript{9}", " ": "~", "�": "?", "§": r"\S{}",
}

PREAMBLE = r"""\documentclass[preprint,12pt]{elsarticle}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{newtxtext,newtxmath}
\usepackage{amsmath}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{graphicx}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{microtype}
\usepackage{adjustbox}
\usepackage{xurl}
\graphicspath{{figures/}}
\journal{Computer Networks}

\begin{document}
\begin{frontmatter}
\title{%s}
\author{%s}
\ead{%s}
\affiliation{%s}

\begin{abstract}
%s
\end{abstract}

\begin{keyword}
%s
\end{keyword}
\end{frontmatter}

"""


def fit_wide(tex: str) -> str:
    """Shrink any table wider than the text block (adjustbox max width only shrinks), and
    let bare URLs break across lines."""
    tex = tex.replace(r"\begin{tabular}", r"\begin{adjustbox}{max width=\textwidth}\begin{tabular}")
    tex = tex.replace(r"\end{tabular}", r"\end{tabular}\end{adjustbox}")
    return re.sub(r"(?<![{=])(https?://[^\s}]+?)([.,;)]?)(?=\s)", r"\\url{\1}\2", tex)


def to_pdflatex(tex: str) -> str:
    for ch, rep in UNICODE.items():
        tex = tex.replace(ch, rep)
    left = sorted({c for c in tex if ord(c) > 127})
    if left:
        raise SystemExit(f"unmapped non-ASCII characters for pdfLaTeX: {[hex(ord(c)) for c in left]}")
    return tex


def relocate_figures(tex: str) -> str:
    """Point \\includegraphics at figures/<name> and copy each file into the package."""
    (OUT / "figures").mkdir(parents=True, exist_ok=True)

    def repl(m: re.Match) -> str:
        src = Path(m.group(2))
        if not src.is_absolute():
            src = (PAPER / src).resolve()
        if not src.exists():
            src = FIGURES / src.name
        shutil.copy2(src, OUT / "figures" / src.name)
        return m.group(1) + "{" + src.stem + "}"

    tex = re.sub(r"(\\includegraphics\[[^\]]*\])\{([^}]+)\}", repl, tex)
    return tex.replace(r"\begin{figure*}", r"\begin{figure}").replace(r"\end{figure*}", r"\end{figure}") \
              .replace(r"\begin{table*}", r"\begin{table}").replace(r"\end{table*}", r"\end{table}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tex-only", action="store_true")
    args = ap.parse_args()

    md = SRC.read_text(encoding="utf-8")
    title, _author, abstract, keywords, rest = extract_front_matter(md)
    refs_at = re.search(r"\n## References\n\n", rest)
    body_md, refs_md = rest[:refs_at.start()], rest[refs_at.end():]

    OUT.mkdir(parents=True, exist_ok=True)
    body = fit_wide(relocate_figures(convert(body_md)))
    kw = r" \sep ".join(inline(k.strip()) for k in keywords.split(","))
    tex = (PREAMBLE % (inline(title), AUTHOR, EMAIL, AFFIL, inline(abstract), kw)
           + body + "\n" + DECLARATIONS + "\n"
           + convert_references(refs_md).replace(r"\begin{thebibliography}{20}",
                                                 r"\begin{thebibliography}{99}")
           + "\n\\end{document}\n")
    TEX.write_text(to_pdflatex(tex), encoding="utf-8")
    print(f"wrote {TEX}")
    if args.tex_only:
        return 0

    engine = shutil.which("pdflatex")
    if not engine:
        print("pdflatex not found; wrote .tex only")
        return 1
    for run in (1, 2):
        r = subprocess.run([engine, "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                           cwd=OUT, capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        if r.returncode != 0:
            errs = [l for l in (r.stdout or "").split("\n") if l.startswith("!") or "Error" in l]
            print(f"pdflatex failed on pass {run}:\n" + ("\n".join(errs[:30]) or r.stdout[-2000:]))
            return 1
        print(f"  pass {run} ok")
    for ext in (".aux", ".log", ".out", ".spl"):
        (OUT / f"main{ext}").unlink(missing_ok=True)
    pdf = OUT / "main.pdf"
    print(f"wrote {pdf} ({pdf.stat().st_size / 1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
