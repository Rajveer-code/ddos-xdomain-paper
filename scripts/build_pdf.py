"""
Build the submission PDF from paper/manuscript.md.

The markdown is the single source of truth for the paper, exactly as results/*.json is for
the numbers, so the PDF is generated rather than maintained. Edit the markdown and rerun.

Produces paper/manuscript.tex and paper/manuscript.pdf via XeLaTeX (chosen for the Unicode
in the text: minus signs, Greek, arrows, superscripts).

    python scripts/build_pdf.py
    python scripts/build_pdf.py --tex-only
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

SRC = PAPER / "manuscript.md"
TEX = PAPER / "manuscript.tex"
PDF = PAPER / "manuscript.pdf"

# Characters XeLaTeX will not find in a text font, mapped to math or ASCII.
UNI = {
    "−": r"$-$", "×": r"$\times$", "→": r"$\rightarrow$",
    "≈": r"$\approx$", "≥": r"$\geq$", "≤": r"$\leq$",
    "Δ": r"$\Delta$", "ρ": r"$\rho$", "α": r"$\alpha$",
    "–": "--", "—": "---",
    "‘": "`", "’": "'", "“": "``", "”": "''",
    "³⁰⁴": r"$^{304}$", "²⁵²": r"$^{252}$",
    "³": r"$^{3}$", "²": r"$^{2}$",
}
SPECIALS = {"&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
            "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}"}


def esc(t: str) -> str:
    """Escape LaTeX specials, then map Unicode. Order matters: specials first."""
    out = []
    for ch in t:
        out.append(SPECIALS.get(ch, ch))
    t = "".join(out)
    for k, v in UNI.items():
        t = t.replace(k, v)
    return t


def inline(t: str) -> str:
    """Markdown inline formatting to LaTeX, applied after escaping."""
    t = esc(t)
    t = re.sub(r"`([^`]+)`", lambda m: r"\texttt{" + m.group(1) + "}", t)
    t = re.sub(r"\*\*([^*]+)\*\*", lambda m: r"\textbf{" + m.group(1) + "}", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", lambda m: r"\emph{" + m.group(1) + "}", t)
    return t


UNNUMBERED = {"Abstract", "References", "Data and code availability"}

#: Above this total width in characters a plain tabular runs off the page, so the table is
#: set with tabularx and the prose-bearing columns are allowed to wrap.
WIDE_TABLE_CHARS = 95


def colspec(sep_cells: list[str]) -> str:
    spec = []
    for c in sep_cells:
        c = c.strip()
        if c.startswith(":") and c.endswith(":"):
            spec.append("c")
        elif c.endswith(":"):
            spec.append("r")
        else:
            spec.append("l")
    return "".join(spec)


def plain_len(cell: str) -> int:
    """Rendered width of a cell, ignoring markdown markup."""
    return len(re.sub(r"[*`]", "", cell))


def wide_colspec(base: str, header: list[str], body: list[list[str]]) -> tuple[str, bool]:
    """
    Decide the column specification, switching to tabularx when the table is too wide.

    Columns whose widest cell exceeds a third of the table's content are given X so they
    wrap; the rest keep their markdown alignment. Returns (spec, needs_tabularx).
    """
    n = len(header)
    widths = [plain_len(header[c]) for c in range(n)]
    for row in body:
        for c in range(min(n, len(row))):
            widths[c] = max(widths[c], plain_len(row[c]))
    if sum(widths) <= WIDE_TABLE_CHARS:
        return base, False

    total = max(sum(widths), 1)
    spec = []
    for c in range(n):
        if widths[c] / total > 0.30:
            spec.append("X")  # prose column: let it wrap
        else:
            spec.append(base[c] if c < len(base) else "l")
    if "X" not in spec:  # nothing dominant; wrap the widest
        spec[widths.index(max(widths))] = "X"
    return "".join(spec), True


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    # respect escaped pipes inside cells
    parts = re.split(r"(?<!\\)\|", line)
    return [p.replace(r"\|", "|").strip() for p in parts]


def convert(md: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i = 0
    table_n = 0
    fig_n = 0

    while i < len(lines):
        ln = lines[i]
        st = ln.strip()

        # ---- horizontal rule / blank
        if st in ("---", ""):
            if st == "":
                out.append("")
            i += 1
            continue

        # ---- headings
        m = re.match(r"^(#{1,4})\s+(.*)$", st)
        if m:
            lvl, txt = len(m.group(1)), m.group(2)
            txt = re.sub(r"^\d+(\.\d+)*\.?\s*", "", txt)  # LaTeX numbers sections itself
            cmd = {1: "title", 2: "section", 3: "subsection", 4: "subsubsection"}[lvl]
            if cmd == "title":
                out.append(r"%TITLE%" + inline(txt))
            else:
                # Front and back matter carry no section number, so that Introduction is
                # section 1 and the numbering matches the cross-references in the text.
                star = "*" if txt in UNNUMBERED else ""
                out.append("\\%s%s{%s}" % (cmd, star, inline(txt)))
            i += 1
            continue

        # ---- figure: ![...](path) followed by a **Figure N.** caption
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
                # caption may wrap over following lines
                k = j + 1
                while k < len(lines) and lines[k].strip() and not lines[k].strip().startswith(("#", "|", "!", "**")):
                    cap += " " + lines[k].strip()
                    k += 1
                i = k
            else:
                i = i + 1
            fig_n += 1
            out.append(r"\begin{figure}[htbp]\centering")
            out.append(r"\includegraphics[width=\linewidth]{%s}" % path)
            if cap:
                out.append(r"\caption{%s}" % inline(cap))
            out.append(r"\label{fig:%d}" % fig_n)
            out.append(r"\end{figure}")
            continue

        # ---- table caption line immediately preceding a pipe table
        cap_m = re.match(r"^\*\*Table (\d+)\.\s*(.*?)\*\*$", st)
        pending_caption = None
        if cap_m:
            nxt = i + 1
            while nxt < len(lines) and lines[nxt].strip() == "":
                nxt += 1
            if nxt < len(lines) and lines[nxt].strip().startswith("|"):
                pending_caption = cap_m.group(2)
                i = nxt
                st = lines[i].strip()

        # ---- pipe table
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
            spec, wide = wide_colspec(spec, header, body)
            env = "tabularx" if wide else "tabular"
            arg = r"{\linewidth}{%s}" % spec if wide else r"{%s}" % spec
            out.append(r"\begin{table}[htbp]\centering\small")
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
            out.append(r"\end{table}")
            continue

        # ---- blockquote
        if st.startswith(">"):
            block = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                block.append(lines[i].strip()[1:].strip())
                i += 1
            out.append(r"\begin{quote}" + inline(" ".join(block)) + r"\end{quote}")
            continue

        # ---- ordered list
        if re.match(r"^\d+\.\s", st):
            out.append(r"\begin{enumerate}[leftmargin=*,itemsep=2pt]")
            while i < len(lines) and (re.match(r"^\d+\.\s", lines[i].strip()) or
                                      (lines[i].startswith("   ") and lines[i].strip())):
                s2 = lines[i].strip()
                if re.match(r"^\d+\.\s", s2):
                    out.append(r"\item " + inline(re.sub(r"^\d+\.\s*", "", s2)))
                else:
                    out[-1] += " " + inline(s2)
                i += 1
            out.append(r"\end{enumerate}")
            continue

        # ---- bullet list
        if re.match(r"^[-*]\s", st):
            out.append(r"\begin{itemize}[leftmargin=*,itemsep=2pt]")
            while i < len(lines) and (re.match(r"^[-*]\s", lines[i].strip()) or
                                      (lines[i].startswith("   ") and lines[i].strip())):
                s2 = lines[i].strip()
                if re.match(r"^[-*]\s", s2):
                    out.append(r"\item " + inline(re.sub(r"^[-*]\s*", "", s2)))
                else:
                    out[-1] += " " + inline(s2)
                i += 1
            out.append(r"\end{itemize}")
            continue

        # ---- paragraph
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


PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
\usepackage{fontspec}
\setmainfont{@@FONT@@}
\usepackage[margin=2.5cm]{geometry}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{graphicx}
\usepackage{enumitem}
\usepackage{caption}
\usepackage[hidelinks]{hyperref}
\usepackage{microtype}
\captionsetup{font=small,labelfont=bf}
\setlength{\parskip}{0.5em}
\setlength{\parindent}{0pt}
\renewcommand{\arraystretch}{1.15}
\title{%s}
\author{%s}
\date{}
\begin{document}
\maketitle
"""


def pick_font() -> str:
    """
    First available serif font, Times-like preferred.

    Elsevier submissions are conventionally set in a Times face, but which Times clone a
    given TeX installation carries varies, so this probes instead of assuming and falls
    back to Latin Modern, which ships with every distribution.
    """
    import tempfile

    candidates = ["TeX Gyre Termes", "Times New Roman", "STIX Two Text",
                  "Cambria", "Latin Modern Roman"]
    engine = shutil.which("xelatex")
    if not engine:
        return "Latin Modern Roman"
    tmp = Path(tempfile.mkdtemp())
    probe = tmp / "probe.tex"
    doc = (r"\documentclass{article}" + "\n" +
           r"\usepackage{fontspec}" + "\n" +
           r"\setmainfont{%s}" + "\n" +
           r"\begin{document}x\end{document}")
    for f in candidates:
        probe.write_text(doc % f, encoding="utf-8")
        r = subprocess.run([engine, "-interaction=nonstopmode", "-halt-on-error",
                            "-output-directory", str(tmp), str(probe)],
                           capture_output=True, text=True, errors="replace")
        if r.returncode == 0:
            return f
    return "Latin Modern Roman"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tex-only", action="store_true")
    args = ap.parse_args()

    md = SRC.read_text(encoding="utf-8")
    body = convert(md)

    title = "Confidently Wrong: Cross-Network DDoS Detectors Invert Rather Than Degrade"
    author = "Rajveer Singh Pall"
    lines = [l for l in body.split("\n") if not l.startswith("%TITLE%")]
    # the author line survives as a lone \textbf{...}; drop the first one
    for idx, l in enumerate(lines):
        if l.strip() == r"\textbf{Rajveer Singh Pall}":
            lines.pop(idx)
            break
    body = "\n".join(lines)

    font = pick_font()
    print(f"main font: {font}")
    preamble = PREAMBLE.replace("@@FONT@@", font)
    TEX.write_text(preamble % (title, author) + body + "\n\\end{document}\n", encoding="utf-8")
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
            print("\n".join(tail[:20]) or (r.stdout or "")[-1500:])
            return 1
        print(f"  pass {run} ok")

    for ext in (".aux", ".log", ".out"):
        (PAPER / f"manuscript{ext}").unlink(missing_ok=True)
    size = PDF.stat().st_size / 1e6 if PDF.exists() else 0
    print(f"wrote {PDF} ({size:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
