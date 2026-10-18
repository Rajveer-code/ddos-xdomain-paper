"""
Build the IEEE Transactions (TNSM) two-column submission PDF from paper/manuscript.md.

Same markdown source as build_pdf.py's single-column proof copy; this produces the
actual submission-format document (IEEEtran journal class) so the real page count
against TNSM's 16-page ceiling can be checked, instead of guessing from the 26pp
single-column proof, which uses a ~6.3in column against IEEEtran's ~3.3in one.

Reuses build_pdf.py's markdown primitives (escaping, inline markdown, list handling,
font probing) since those are format-agnostic. Reimplements table and figure placement,
because most of this paper's tables and figures were sized for the single-column proof's
~6.3in width and do not survive a 3.3in column un-adapted — they need `table*`/`figure*`
(spans both columns, ~6.9in) instead. Also special-cases the Abstract/Keywords block and
the References list into IEEEtran's own environments (`abstract`, `IEEEkeywords`,
`thebibliography`) rather than the generic heading+list treatment the proof copy uses,
since those get IEEEtran's built-in formatting only inside its own environments.

    python scripts/build_pdf_ieee.py
    python scripts/build_pdf_ieee.py --tex-only
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
from scripts.build_pdf import (
    esc, inline, split_row, take_list, plain_len, colspec, pick_font, ORDERED, BULLET,
)

SRC = PAPER / "manuscript.md"
TEX = PAPER / "manuscript_ieee.tex"
PDF = PAPER / "manuscript_ieee.pdf"

UNNUMBERED = {"Data and code availability"}  # Abstract and References are special-cased below

#: A single IEEE column is ~3.3in; both figures (native aspect ratios checked directly,
#: 5.4-9.7in wide before shrinking) and all but the narrowest tables lose legibility
#: shrunk that far, so both default to spanning the full ~6.9in with table*/figure*.
SINGLE_COL_CHARS = 40
SINGLE_COL_MAX_COLS = 4
WIDE_TABLE_CHARS = 95  # inside whichever width was chosen, same wrap threshold as the proof


def wide_colspec(base: str, header: list[str], body: list[list[str]],
                  char_limit: int) -> tuple[str, bool]:
    n = len(header)
    widths = [plain_len(header[c]) for c in range(n)]
    for row in body:
        for c in range(min(n, len(row))):
            widths[c] = max(widths[c], plain_len(row[c]))
    if sum(widths) <= char_limit:
        return base, False
    total = max(sum(widths), 1)
    spec = []
    for c in range(n):
        if widths[c] / total > 0.30:
            spec.append("X")
        else:
            spec.append(base[c] if c < len(base) else "l")
    if "X" not in spec:
        spec[widths.index(max(widths))] = "X"
    return "".join(spec), True


def needs_full_width(header: list[str], body: list[list[str]]) -> bool:
    n = len(header)
    widths = [plain_len(header[c]) for c in range(n)]
    for row in body:
        for c in range(min(n, len(row))):
            widths[c] = max(widths[c], plain_len(row[c]))
    return not (sum(widths) <= SINGLE_COL_CHARS and n <= SINGLE_COL_MAX_COLS)


def extract_front_matter(md: str) -> tuple[str, str, str, str, str]:
    """Pull title, author, abstract prose, keywords and the remaining body markdown
    (from Introduction onward) apart, since IEEEtran renders the first three specially."""
    m_title = re.search(r"^# (.+)$", md, re.M)
    title = m_title.group(1).strip()

    m_author = re.search(r"^\*\*(.+?)\*\*\s*$", md[m_title.end():], re.M)
    author = m_author.group(1).strip()

    m_abs = re.search(r"^## Abstract\s*\n\n(.*?)\n\n\*\*Keywords:\*\*\s*(.*?)\n\n---",
                       md, re.M | re.S)
    abstract = re.sub(r"\s+", " ", m_abs.group(1)).strip()
    keywords = re.sub(r"\s+", " ", m_abs.group(2)).strip()

    rest = md[m_abs.end():]
    return title, author, abstract, keywords, rest


def convert_references(refs_md: str) -> str:
    """References list -> thebibliography, so IEEEtran's own bibliography formatting
    (smaller font, hanging indent, numeral style) applies instead of a generic list."""
    entries = re.split(r"\n(?=\d+\.\s)", refs_md.strip("\n"))
    out = [r"\begin{thebibliography}{20}"]
    for e in entries:
        e = e.strip()
        if not e:
            continue
        m = re.match(r"(\d+)\.\s(.*)", e, re.S)
        n, body = m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()
        out.append(rf"\bibitem{{ref{n}}} " + inline(body))
    out.append(r"\end{thebibliography}")
    return "\n".join(out)


def convert(md: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i = 0
    table_n = 0
    fig_n = 0

    while i < len(lines):
        ln = lines[i]
        st = ln.strip()

        if st in ("---", ""):
            if st == "":
                out.append("")
            i += 1
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", st)
        if m:
            lvl, txt = len(m.group(1)), m.group(2)
            txt = re.sub(r"^\d+(\.\d+)*\.?\s*", "", txt)
            if txt == "References":
                # consumed as a whole block below via convert_references(); skip the
                # heading line itself, the body loop's list-handling never sees "## References"
                i += 1
                continue
            cmd = {1: "title", 2: "section", 3: "subsection", 4: "subsubsection"}[lvl]
            star = "*" if txt in UNNUMBERED else ""
            out.append("\\%s%s{%s}" % (cmd, star, inline(txt)))
            i += 1
            continue

        m = re.match(r"^!\[[^\]]*\]\(([^)]+)\)$", st)
        if m:
            rel = m.group(1)
            name = Path(rel).name
            path = (FIGURES / name).as_posix()
            cap = ""
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            cm = re.match(r"^\*\*Figure (\d+)\.\*\*\s*(.*)$", lines[j].strip()) if j < len(lines) else None
            if cm:
                cap = cm.group(2)
                k = j + 1
                while k < len(lines) and lines[k].strip() and not lines[k].strip().startswith(("#", "|", "!", "**")):
                    cap += " " + lines[k].strip()
                    k += 1
                i = k
            else:
                i = i + 1
            fig_n += 1
            # every figure here is native 5.4-9.7in wide (checked directly); all need
            # the full ~6.9in of figure* to stay legible, none fit a 3.3in column
            out.append(r"\begin{figure*}[htbp]\centering")
            out.append(r"\includegraphics[width=0.85\textwidth]{%s}" % path)
            if cap:
                out.append(r"\caption{%s}" % inline(cap))
            out.append(r"\label{fig:%d}" % fig_n)
            out.append(r"\end{figure*}")
            continue

        cap_m = re.match(r"^\*\*Table (\d+)\.\s*(.*?)\*\*(.*)$", st)
        pending_caption = None
        if cap_m:
            parts = [p for p in (cap_m.group(2).strip(), cap_m.group(3).strip()) if p]
            nxt = i + 1
            while (nxt < len(lines) and lines[nxt].strip()
                   and not lines[nxt].strip().startswith("|")):
                parts.append(lines[nxt].strip())
                nxt += 1
            while nxt < len(lines) and lines[nxt].strip() == "":
                nxt += 1
            if nxt < len(lines) and lines[nxt].strip().startswith("|"):
                pending_caption = " ".join(parts)
                i = nxt
                st = lines[i].strip()

        if st.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|?$", lines[i + 1].strip()):
            header = split_row(lines[i])
            spec = colspec(split_row(lines[i + 1]))
            body = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                body.append(split_row(lines[j]))
                j += 1
            i = j
            table_n += 1

            full_width = needs_full_width(header, body)
            char_limit = WIDE_TABLE_CHARS if full_width else SINGLE_COL_CHARS
            spec, wide = wide_colspec(spec, header, body, char_limit)
            env = "tabularx" if wide else "tabular"
            width_expr = r"\textwidth" if full_width else r"\columnwidth"
            arg = r"{%s}{%s}" % (width_expr, spec) if wide else r"{%s}" % spec
            table_env = "table*" if full_width else "table"

            size = r"\scriptsize" if full_width else r"\footnotesize"
            out.append(r"\begin{%s}[htbp]\centering%s" % (table_env, size))
            if pending_caption:
                out.append(r"\caption{%s}" % inline(pending_caption))
            out.append(r"\begin{%s}%s" % (env, arg))
            out.append(r"\toprule")
            out.append(" & ".join(inline(c) for c in header) + r" \\")
            out.append(r"\midrule")
            for row in body:
                row = (row + [""] * len(header))[:len(header)]
                out.append(" & ".join(inline(c) for c in row) + r" \\")
            out.append(r"\bottomrule")
            out.append(r"\end{%s}" % env)
            out.append(r"\end{%s}" % table_env)
            continue

        if st.startswith(">"):
            block = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                block.append(lines[i].strip()[1:].strip())
                i += 1
            out.append(r"\begin{quote}" + inline(" ".join(block)) + r"\end{quote}")
            continue

        if re.match(ORDERED, st):
            i = take_list(lines, i, ORDERED, r"^\d+\.\s*", "enumerate", out)
            continue

        if re.match(BULLET, st):
            i = take_list(lines, i, BULLET, r"^[-*]\s*", "itemize", out)
            continue

        para = []
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,4}\s|\||!\[|>|\d+\.\s|[-*]\s|---$)", lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        if para:
            out.append(inline(" ".join(para)))
        else:
            i += 1

    return "\n".join(out)


PREAMBLE = r"""\documentclass[journal]{IEEEtran}
\usepackage{fontspec}
\setmainfont{@@FONT@@}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{graphicx}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{microtype}
\begin{document}

\title{%s}
\author{%s\thanks{Department of Computer Science and Business Systems, Gyan Ganga Institute of Technology and Sciences, Jabalpur, India (e-mail: rajveerpall04@gmail.com).}}

\maketitle

\begin{abstract}
%s
\end{abstract}

\begin{IEEEkeywords}
%s
\end{IEEEkeywords}

"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tex-only", action="store_true")
    args = ap.parse_args()

    md = SRC.read_text(encoding="utf-8")
    title, author, abstract_raw, keywords_raw, rest_md = extract_front_matter(md)

    # split References out of the tail so it renders via thebibliography, not a
    # generic numbered list -- everything up to "## References" goes through the
    # normal converter, the references block is handled by convert_references()
    ref_split = re.search(r"\n## References\n\n", rest_md)
    body_md = rest_md[:ref_split.start()]
    after_refs = rest_md[ref_split.end():]
    refs_split2 = re.search(r"\n## Data and code availability\n\n", body_md)
    # "Data and code availability" precedes References in the manuscript source; keep
    # body_md as everything up to References (already true), refs block is the rest
    refs_md = after_refs
    # anything after the reference list itself in the file (there is none currently,
    # but don't silently drop content if a future edit adds a trailing section)
    trailing_after_refs = ""
    m_trailing = re.search(r"\n## ", refs_md)
    if m_trailing:
        trailing_after_refs = "\n## " + refs_md[m_trailing.end():]
        refs_md = refs_md[:m_trailing.start()]

    body = convert(body_md)
    refs_tex = convert_references(refs_md)
    trailing_tex = convert(trailing_after_refs) if trailing_after_refs.strip() else ""

    font = pick_font()
    print(f"main font: {font}")
    preamble = PREAMBLE.replace("@@FONT@@", font) % (
        inline(title), inline(author), inline(abstract_raw), inline(keywords_raw),
    )
    full = preamble + body + "\n\n" + refs_tex + "\n" + trailing_tex + "\n\\end{document}\n"
    TEX.write_text(full, encoding="utf-8")
    print(f"wrote {TEX}")
    if args.tex_only:
        return 0

    engine = shutil.which("xelatex")
    if not engine:
        print("xelatex not found; wrote .tex only")
        return 1
    for run in (1, 2):
        r = subprocess.run(
            [engine, "-interaction=nonstopmode", "-halt-on-error",
             "-output-directory", str(PAPER), str(TEX)],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            tail = [l for l in (r.stdout or "").split("\n") if l.startswith("!") or "Error" in l]
            print(f"xelatex failed on pass {run}:")
            print("\n".join(tail[:30]) or (r.stdout or "")[-2000:])
            return 1
        print(f"  pass {run} ok")

    for ext in (".aux", ".log", ".out"):
        (PAPER / f"manuscript_ieee{ext}").unlink(missing_ok=True)
    size = PDF.stat().st_size / 1e6 if PDF.exists() else 0
    print(f"wrote {PDF} ({size:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
