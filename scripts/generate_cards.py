#!/usr/bin/env python3
"""Generate the terminal cards shown on the GitHub profile:

  assets/neofetch.svg       the neofetch card (edit INFO below)
  assets/contributions.svg  the contribution map for the last year
  assets/career.svg         the git-graph career timeline (edit CAREER below)

Run:  python3 scripts/generate_cards.py
Needs the `gh` CLI, authenticated (locally) or with GH_TOKEN set (in Actions).
Standard library only.
"""
import json
import subprocess
import textwrap
from datetime import date
from html import escape
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
LOGIN = "mnijhum"

USER, HOST = "mnijhum", "github"
INFO = [
    ("OS", "Full Stack Developer x86_64"),
    ("Host", "Oloodi · Montréal, QC, Canada"),
    ("Kernel", "MEng Information Systems Security, Concordia '26"),
    ("Uptime", "shipping production code since 2021"),
    ("Packages", "{repos} (github)"),
    ("Shell", "TypeScript, Python, JavaScript, Java"),
    ("DE", "Next.js, React, Tailwind CSS, shadcn/ui"),
    ("WM", "FastAPI, Flask, Node.js, Spring Boot"),
    ("Terminal", "Docker, Kubernetes, CI/CD, AWS S3"),
    ("CPU", "RAG, LangChain, LangGraph, Qdrant, OpenAI"),
    ("Memory", "PostgreSQL, MongoDB"),
    ("Locale", "mnijhum.com · blogs.mnijhum.com"),
]

# Newest first. rail: "main" for jobs, "side" for the branch that runs alongside them.
# ref: ("head", name) | ("branch", name) | ("tag", name) | ("root", name)
CAREER = [
    dict(rail="main", ref=("head", "oloodi"), title="Full Stack Developer",
         place="Oloodi · Montréal, QC", dates="Sept 2026 – present", desc=""),
    dict(rail="side", ref=("branch", "concordia"), title="MEng, Information Systems Security",
         place="Concordia University · Montréal, QC", dates="May 2024 – Apr 2026", desc=""),
    dict(rail="main", ref=("tag", "medistack"), title="Software Engineer",
         place="MediStack · Remote", dates="Jan 2025 – Feb 2026",
         desc="Healthcare SaaS. Shipped Next.js interfaces and Node.js APIs, a LangChain + LangGraph RAG "
              "assistant, a prescription builder covering 28k+ medicines, and real-time scheduling."),
    dict(rail="main", ref=("tag", "intercloud"), title="Software Engineer",
         place="Intercloud Limited · Dhaka, Bangladesh", dates="May 2022 – Apr 2024",
         desc="Brilliant Cloud, Bangladesh's first IaaS portal. Built IAM, the Kubernetes-as-a-Service "
              "frontend, monitoring for 15+ microservices, and a ticketing platform (1000+ requests a day)."),
    dict(rail="main", ref=("tag", "together"), title="Junior Software Engineer",
         place="Together Initiatives · Dhaka, Bangladesh", dates="Nov 2021 – Feb 2022",
         desc="Spring Boot backend for a point-of-sale system, plus RPA for telecom services."),
    dict(rail="main", ref=("root", "init"), title="BSc, Computer Science & Engineering",
         place="BRAC University · Dhaka, Bangladesh", dates="Jan 2017 – Jun 2021", desc=""),
]

# ---- theme ---------------------------------------------------------------
BG, BAR, BORDER = "#0d1117", "#161b22", "#30363d"
TEXT, DIM, ACCENT, PROMPT, LOGO_INK = "#c9d1d9", "#8b949e", "#5eead4", "#7ee787", "#f0f6fc"
LOGO_FROM, LOGO_TO = (94, 234, 212), (96, 165, 250)  # teal -> blue, top to bottom
SIDE, SOFT = "#bc8cff", "#9da7b3"  # side-branch rail, description text
GIT_YELLOW, GIT_CYAN, GIT_GREEN = "#e3b341", "#56d4dd", "#56d364"
LEVELS = {  # contribution map cells, empty -> busiest
    "NONE": "#161b22",
    "FIRST_QUARTILE": "#134e4a",
    "SECOND_QUARTILE": "#0f766e",
    "THIRD_QUARTILE": "#2dd4bf",
    "FOURTH_QUARTILE": "#99f6e4",
}
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


def fetch():
    """Public repo count and the last year's contribution calendar."""
    query = (
        "query($login:String!){user(login:$login){"
        "repositories(ownerAffiliations:OWNER,privacy:PUBLIC){totalCount}"
        "contributionsCollection{contributionCalendar{totalContributions "
        "weeks{contributionDays{date contributionCount contributionLevel}}}}}}"
    )
    res = subprocess.run(
        ["gh", "api", "graphql", "-f", f"login={LOGIN}", "-f", f"query={query}"],
        check=True, capture_output=True, text=True,
    )
    user = json.loads(res.stdout)["data"]["user"]
    return user["repositories"]["totalCount"], user["contributionsCollection"]["contributionCalendar"]


def prompt(y, tail=""):
    return (
        f'<text x="{PAD}" y="{y}"><tspan class="b" fill="{PROMPT}">❯</tspan>'
        f'<tspan fill="{DIM}"> ~ </tspan>{tail}</text>'
    )


def window(H, title, desc, command):
    """Opening tags, styles, window chrome and the typed command. Returns (svg lines, reveal start time)."""
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-labelledby="t d">',
        f'<title id="t">{escape(title)}</title>',
        f'<desc id="d">{escape(desc)}</desc>',
    ]
    n = len(command)
    typed = "".join(f".c{i}{{animation-delay:{0.5 + i * 0.07:.2f}s}}" for i in range(n))
    start = 0.5 + n * 0.07 + 0.35
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

    cmd = "".join(f'<tspan class="ch c{i}">{nbsp(ch)}</tspan>' for i, ch in enumerate(command))
    out.append(prompt(PROMPT_Y, cmd))
    return out, start


def closing_prompt(y, delay):
    return (
        f'<g class="ln" style="animation-delay:{delay:.2f}s">{prompt(y)}'
        f'<rect class="cur" x="{PAD + 4 * CW + 2:.1f}" y="{y - 15}" width="9" height="19" fill="{TEXT}"/></g>'
    )


def build_neofetch(repos):
    info = [(k, v.format(repos=repos)) for k, v in INFO]
    lines = len(info) + 2 + 1 + 2  # title + rule, gap, two rows of colour blocks
    end_y = TOP + max(ROWS, lines) * LH + 26
    H = end_y + 34
    out, start = window(
        H, f"{USER}@{HOST} — neofetch", "; ".join(f"{k}: {v}" for k, v in info), "neofetch"
    )

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
    for i, (k, v) in enumerate(info, start=2):
        out.append(info_line(i, f'<tspan class="b" fill="{ACCENT}">{escape(k)}</tspan>: {escape(v)}'))

    base = len(info) + 3
    for r, palette in enumerate(ANSI):
        y = TOP + (base + r) * LH - 16
        delay = start + 0.1 + (base + r) * 0.06
        blocks = "".join(
            f'<rect x="{INFO_X + i * 30:.1f}" y="{y}" width="30" height="{LH}" fill="{c}"/>'
            for i, c in enumerate(palette)
        )
        out.append(f'<g class="ln" style="animation-delay:{delay:.2f}s">{blocks}</g>')

    out.append(closing_prompt(end_y, start + 0.1 + (base + 2) * 0.06))
    out.append("</svg>")
    return "\n".join(out)


def streaks(days):
    """(longest, current) runs of consecutive days with at least one contribution."""
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] else 0
        longest = max(longest, run)
    # today may simply not have happened yet, so an empty last day doesn't break the current streak
    tail = days[:-1] if days and not days[-1]["contributionCount"] else days
    current = 0
    for d in reversed(tail):
        if not d["contributionCount"]:
            break
        current += 1
    return longest, current


def build_contributions(calendar):
    weeks = calendar["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    total = calendar["totalContributions"]
    longest, current = streaks(days)
    active = sum(1 for d in days if d["contributionCount"])

    label_w, cell, gap = 44, 13, 3.6
    pitch = cell + gap
    grid_x, months_y = PAD + label_w, PROMPT_Y + 40
    grid_y = months_y + 12
    summary_y = grid_y + 7 * pitch + 30
    end_y = summary_y + 40
    H = end_y + 34

    desc = f"{total} contributions in the last year; {active} active days; longest streak {longest} days"
    out, start = window(H, f"{USER}@{HOST} — contributions", desc, "git log --since=1.year --graph")
    small = f'style="font-size:12px;fill:{DIM}"'

    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="{PAD}" y="{grid_y + row * pitch + 11:.1f}" {small}>{name}</text>')

    last_label_col = -4
    for col, week in enumerate(weeks):
        x = grid_x + col * pitch
        first = date.fromisoformat(week["contributionDays"][0]["date"])
        cells = []
        for d in week["contributionDays"]:
            day = date.fromisoformat(d["date"])
            row = (day.weekday() + 1) % 7  # Sunday on top, like github.com
            n = d["contributionCount"]
            tip = f'{n} contribution{"" if n == 1 else "s"} on {day:%b} {day.day}, {day.year}'
            cells.append(
                f'<rect x="{x:.1f}" y="{grid_y + row * pitch:.1f}" width="{cell}" height="{cell}" rx="2.5" '
                f'fill="{LEVELS[d["contributionLevel"]]}"><title>{tip}</title></rect>'
            )
        # month label above the first week that starts in a new month
        starts_month = any(date.fromisoformat(d["date"]).day == 1 for d in week["contributionDays"])
        # a partial first month only gets a label when there is room before the next one
        leading = col == 0 and first.day <= 10
        if (leading or starts_month) and col - last_label_col >= 3 and col < len(weeks) - 1:
            label = first if leading and not starts_month else next(
                date.fromisoformat(d["date"]) for d in week["contributionDays"] if d["date"].endswith("-01")
            )
            out.append(f'<text x="{x:.1f}" y="{months_y}" {small}>{label:%b}</text>')
            last_label_col = col
        out.append(f'<g class="ln" style="animation-delay:{start + col * 0.018:.2f}s">{"".join(cells)}</g>')

    done = start + len(weeks) * 0.018 + 0.2
    plural = lambda n, word: f"{n:,} {word}{'' if n == 1 else 's'}"
    summary = (
        f'<tspan class="b" fill="{ACCENT}">{total:,}</tspan> contributions in the last year'
        f'<tspan fill="{DIM}"> · </tspan><tspan class="b" fill="{ACCENT}">{active}</tspan> active days'
        f'<tspan fill="{DIM}"> · </tspan>longest streak <tspan class="b" fill="{ACCENT}">{plural(longest, "day")}</tspan>'
    )
    out.append(f'<text class="ln" style="animation-delay:{done:.2f}s" x="{PAD}" y="{summary_y:.1f}">{summary}</text>')

    # legend, right-aligned with the grid
    right = grid_x + len(weeks) * pitch - gap
    lx = right - 5 * pitch - 40
    legend = [f'<text x="{lx - 8:.1f}" y="{summary_y:.1f}" text-anchor="end" {small}>less</text>']
    for i, colour in enumerate(LEVELS.values()):
        legend.append(
            f'<rect x="{lx + i * pitch:.1f}" y="{summary_y - 11:.1f}" width="{cell}" height="{cell}" rx="2.5" fill="{colour}"/>'
        )
    legend.append(f'<text x="{lx + 5 * pitch + 4:.1f}" y="{summary_y:.1f}" {small}>more</text>')
    out.append(f'<g class="ln" style="animation-delay:{done:.2f}s">{"".join(legend)}</g>')

    out.append(closing_prompt(end_y, done + 0.2))
    out.append("</svg>")
    return "\n".join(out)


def decoration(kind, name):
    """The (HEAD -> branch) / (tag: x) suffix, coloured the way git colours it."""
    y = f'fill="{GIT_YELLOW}"'
    if kind == "head":
        inner = f'<tspan class="b" fill="{GIT_CYAN}">HEAD -&gt; </tspan><tspan class="b" fill="{GIT_GREEN}">{name}</tspan>'
    elif kind == "branch":
        inner = f'<tspan class="b" fill="{SIDE}">{name}</tspan>'
    elif kind == "tag":
        inner = f'<tspan class="b" {y}>tag: {name}</tspan>'
    else:
        inner = f'<tspan fill="{DIM}">{name}</tspan>'
    return f'<tspan {y}> (</tspan>{inner}<tspan {y}>)</tspan>'


def build_career():
    mx, sx, tx = PAD + 7, PAD + 31, PAD + 58
    desc_style = f'style="font-size:14.5px;fill:{SOFT}"'

    # lay out first so the rails know where the nodes are
    y, rows = TOP, []
    for e in CAREER:
        wrapped = textwrap.wrap(e["desc"], 92)
        rows.append((e, y, wrapped))
        y += (2 + len(wrapped)) * LH + 16
    end_y = y + 10
    H = end_y + 34

    summary = "; ".join(f'{e["title"]}, {e["place"]}, {e["dates"]}' for e in CAREER)
    out, start = window(H, f"{USER}@{HOST} — career", summary, "git log --graph --career")

    node_y = lambda ty: ty - 5.5
    mains = [node_y(ty) for e, ty, _ in rows if e["rail"] == "main"]
    rails = [f'<path d="M{mx} {mains[0]}V{mains[-1]}" stroke="{ACCENT}" stroke-width="2" fill="none"/>']
    for i, (e, ty, _) in enumerate(rows):
        if e["rail"] != "side":
            continue
        # merges into the nearest main node above, forks from the second main node below
        top = max(node_y(t) for r, t, _ in rows[:i] if r["rail"] == "main")
        below = [node_y(t) for r, t, _ in rows[i + 1:] if r["rail"] == "main"]
        bottom = below[1] if len(below) > 1 else below[0]
        rails.append(
            f'<path d="M{mx} {bottom}C{mx} {bottom - 20} {sx} {bottom - 14} {sx} {bottom - 34}'
            f'V{top + 34}C{sx} {top + 14} {mx} {top + 20} {mx} {top}" '
            f'stroke="{SIDE}" stroke-width="2" fill="none"/>'
        )
    out.append(f'<g class="ln" style="animation-delay:{start:.2f}s">{"".join(rails)}</g>')

    for i, (e, ty, wrapped) in enumerate(rows):
        side = e["rail"] == "side"
        cx, colour = (sx, SIDE) if side else (mx, ACCENT)
        hollow = side or e["ref"][0] == "root"
        parts = [
            f'<circle cx="{cx}" cy="{node_y(ty)}" r="6" fill="{BG if hollow else colour}" '
            f'stroke="{colour if hollow else BG}" stroke-width="2"/>',
            f'<text x="{tx}" y="{ty}"><tspan class="b" fill="{LOGO_INK}">{escape(e["title"])}</tspan>'
            f'{decoration(*e["ref"])}</text>',
            f'<text x="{W - PAD}" y="{ty}" text-anchor="end" style="font-size:14.5px;fill:{DIM}">{escape(e["dates"])}</text>',
            f'<text x="{tx}" y="{ty + LH}" style="fill:{colour}">'
            f'{escape(e["place"])}</text>',
        ]
        for j, line in enumerate(wrapped):
            parts.append(f'<text x="{tx}" y="{ty + (2 + j) * LH}" {desc_style}>{escape(line)}</text>')
        out.append(f'<g class="ln" style="animation-delay:{start + 0.15 + i * 0.12:.2f}s">{"".join(parts)}</g>')

    out.append(closing_prompt(end_y, start + 0.15 + len(rows) * 0.12 + 0.1))
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    repos, calendar = fetch()
    ASSETS.mkdir(exist_ok=True)
    cards = {
        "neofetch.svg": build_neofetch(repos),
        "contributions.svg": build_contributions(calendar),
        "career.svg": build_career(),
    }
    for name, svg in cards.items():
        (ASSETS / name).write_text(svg + "\n", encoding="utf-8")
        print(f"wrote assets/{name}")
