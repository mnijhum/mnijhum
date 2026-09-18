#!/usr/bin/env python3
"""Generate assets/neofetch.svg, the terminal card shown on the GitHub profile.

Edit INFO below, then run:  python3 scripts/generate_neofetch.py
Standard library only.
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "neofetch.svg"

USER, HOST = "mnijhum", "github"
INFO = [
    ("OS", "Software Engineer x86_64"),
    ("Host", "Oloodi · Montréal, QC, Canada"),
    ("Kernel", "MEng Information Systems Security @ Concordia"),
    ("Uptime", "shipping production code since 2021"),
    ("Packages", "37 (github)"),
    ("Shell", "TypeScript, Python, JavaScript, Java"),
    ("DE", "Next.js, React, Tailwind CSS, shadcn/ui"),
    ("WM", "FastAPI, Flask, Node.js, Spring Boot"),
    ("Terminal", "Docker, Kubernetes, CI/CD, AWS S3"),
    ("CPU", "RAG, LangChain, LangGraph, Qdrant, OpenAI"),
    ("Memory", "PostgreSQL, MongoDB"),
    ("Locale", "mnijhum.com · blogs.mnijhum.com"),
]

# ---- theme ---------------------------------------------------------------
BG, BAR, BORDER = "#0d1117", "#161b22", "#30363d"
TEXT, DIM, ACCENT, PROMPT, LOGO_INK = "#c9d1d9", "#8b949e", "#5eead4", "#7ee787", "#f0f6fc"
LOGO_FROM, LOGO_TO = (94, 234, 212), (96, 165, 250)  # teal -> blue, top to bottom
ANSI = [
    ["#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#b1bac4"],
    ["#6e7681", "#ffa198", "#56d364", "#e3b341", "#79c0ff", "#d2a8ff", "#56d4dd", "#f0f6fc"],
]

# ---- geometry ------------------------------------------------------------
W, PAD, BAR_H = 1000, 40, 42
FS, CW, LH = 16, 9.63, 22  # font size, nominal monospace advance, line height
COLS, ROWS = 30, 15  # logo grid (a character cell is about 1:2)
PROMPT_Y = BAR_H + 38
TOP = PROMPT_Y + 40
INFO_X = PAD + COLS * CW + 50
DIM_FILL = ' fill-opacity=".4"'
FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"


def logo_rows():
    """A shield with an N cut into it. Returns rows of (char, kind) cells."""
    rows = []
    for r in range(ROWS):
        t = r / (ROWS - 1)
        # straight sides for the top 45%, then taper to a point
        half = COLS / 2 if t <= 0.45 else (COLS / 2) * (1 - ((t - 0.45) / 0.55) ** 1.6)
        half = max(half, 1.0)
        row = []
        for c in range(COLS):
            x = c + 0.5 - COLS / 2
            if abs(x) > half:
                row.append((" ", None))
                continue
            edge = abs(x) > half - 2 or r == 0
            row.append(("#", "shield") if edge else (":", "fill"))
        rows.append(row)

    # the N: two stems and a diagonal, rows 3..10, cols 9..20
    n_top, n_bot, n_l, n_r, stem = 3, 10, 9, 20, 3
    for r in range(n_top, n_bot + 1):
        k = (r - n_top) / (n_bot - n_top)
        diag = round(n_l + stem - 1 + k * (n_r - n_l - 2 * stem + 2))
        for c in range(n_l, n_r + 1):
            if c < n_l + stem or c > n_r - stem or diag <= c < diag + stem:
                rows[r][c] = ("N", "ink")
    return rows


def lerp_color(t):
    return "#%02x%02x%02x" % tuple(round(a + (b - a) * t) for a, b in zip(LOGO_FROM, LOGO_TO))


def nbsp(s):
    return escape(s).replace(" ", " ")


def build():
    out = []
    lines = len(INFO) + 2 + 1 + 2  # title + rule, gap, two rows of colour blocks
    body_h = max(ROWS, lines) * LH
    end_y = TOP + body_h + 26
    H = end_y + 34

    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-labelledby="t d">'
    )
    out.append(f'<title id="t">{USER}@{HOST} — neofetch</title>')
    desc = "; ".join(f"{k}: {v}" for k, v in INFO)
    out.append(f'<desc id="d">{escape(desc)}</desc>')

    n = len("neofetch")
    typed = "".join(f".c{i}{{animation-delay:{0.5 + i * 0.09:.2f}s}}" for i in range(n))
    start = 0.5 + n * 0.09 + 0.35
    out.append(
        "<style>"
        f"text{{font-family:{FONT};font-size:{FS}px;fill:{TEXT};white-space:pre}}"
        ".b{font-weight:700}"
        "@keyframes in{from{opacity:0}to{opacity:1}}"
        "@keyframes pop{from{fill-opacity:0}to{fill-opacity:1}}"
        "@keyframes blink{50%{opacity:0}}"
        ".ln{animation:in .35s ease-out backwards}"
        ".ch{animation:pop .01s linear backwards}"
        f"{typed}"
        ".cur{animation:blink 1.1s steps(1) infinite}"
        "@media (prefers-reduced-motion:reduce){.ln,.ch,.cur{animation:none}}"
        "</style>"
    )

    # window chrome
    out.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>')
    out.append(
        f'<path d="M.5 {BAR_H}V12.5a12 12 0 0 1 12-12h{W - 25}a12 12 0 0 1 12 12V{BAR_H}z" fill="{BAR}"/>'
        f'<path d="M0 {BAR_H}.5h{W}" stroke="{BORDER}"/>'
    )
    for i, col in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        out.append(f'<circle cx="{24 + i * 20}" cy="{BAR_H / 2}" r="6" fill="{col}"/>')
    out.append(
        f'<text x="{W / 2}" y="{BAR_H / 2 + 5}" text-anchor="middle" style="font-size:13px;fill:{DIM}">'
        f"{USER}@{HOST}: ~</text>"
    )

    def prompt(y, tail=""):
        return (
            f'<text x="{PAD}" y="{y}"><tspan class="b" fill="{PROMPT}">❯</tspan>'
            f'<tspan fill="{DIM}"> ~ </tspan>{tail}</text>'
        )

    cmd = "".join(f'<tspan class="ch c{i}">{ch}</tspan>' for i, ch in enumerate("neofetch"))
    out.append(prompt(PROMPT_Y, cmd))

    # logo
    for r, row in enumerate(logo_rows()):
        y = TOP + r * LH
        runs, cur = [], None
        for ch, kind in row:
            if cur and cur[0] == kind:
                cur[1] += ch
            else:
                cur = [kind, ch]
                runs.append(cur)
        shade = lerp_color(r / (ROWS - 1))
        spans = "".join(
            f'<tspan class="b" fill="{LOGO_INK}">{nbsp(s)}</tspan>'
            if kind == "ink"
            else f'<tspan fill="{shade}"{DIM_FILL if kind == "fill" else ""}>{nbsp(s)}</tspan>'
            for kind, s in runs
        )
        delay = start + r * 0.03
        out.append(
            f'<text class="ln" style="animation-delay:{delay:.2f}s" x="{PAD}" y="{y}" '
            f'textLength="{COLS * CW:.1f}" lengthAdjust="spacing">{spans}</text>'
        )

    # info column
    def info_line(i, inner):
        delay = start + 0.1 + i * 0.06
        return (
            f'<text class="ln" style="animation-delay:{delay:.2f}s" x="{INFO_X:.1f}" '
            f'y="{TOP + i * LH}">{inner}</text>'
        )

    title = f"{USER}@{HOST}"
    out.append(
        info_line(
            0,
            f'<tspan class="b" fill="{ACCENT}">{USER}</tspan>@<tspan class="b" fill="{ACCENT}">{HOST}</tspan>',
        )
    )
    out.append(info_line(1, f'<tspan fill="{DIM}">{"-" * len(title)}</tspan>'))
    for i, (k, v) in enumerate(INFO, start=2):
        out.append(info_line(i, f'<tspan class="b" fill="{ACCENT}">{escape(k)}</tspan>: {escape(v)}'))

    base = len(INFO) + 3
    for r, palette in enumerate(ANSI):
        y = TOP + (base + r) * LH - 16
        delay = start + 0.1 + (base + r) * 0.06
        blocks = "".join(
            f'<rect x="{INFO_X + i * 30:.1f}" y="{y}" width="30" height="{LH}" fill="{c}"/>'
            for i, c in enumerate(palette)
        )
        out.append(f'<g class="ln" style="animation-delay:{delay:.2f}s">{blocks}</g>')

    # trailing prompt with cursor
    end_delay = start + 0.1 + (base + 2) * 0.06
    out.append(
        f'<g class="ln" style="animation-delay:{end_delay:.2f}s">{prompt(end_y)}'
        f'<rect class="cur" x="{PAD + 4 * CW + 2:.1f}" y="{end_y - 15}" width="9" height="19" fill="{TEXT}"/></g>'
    )
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(build() + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(OUT.parent.parent)}")
