"""Featured projects: one card per pinned repo, linked from the README.

Writes assets/projects/<repo>.svg and rewrites the README block between
<!-- PROJECTS:START --> and <!-- PROJECTS:END -->. Pin/unpin repos on your
profile to change what shows up. DEMO=1 renders fake data without a token.
"""
import datetime as dt
import hashlib
import json
import os
import re
import textwrap
import urllib.request
from html import escape

USER = os.environ.get("GH_USER", "mafns")
TOKEN = os.environ.get("GH_TOKEN", "")
DEMO = os.environ.get("DEMO") == "1"
ROOT = os.environ.get("REPO_ROOT", os.path.join(os.path.dirname(__file__), ".."))
OUTDIR = os.path.join(ROOT, "assets", "projects")
README = os.path.join(ROOT, "README.md")

REPO_FIELDS = """name description url stargazerCount forkCount pushedAt isFork
  parent{nameWithOwner} primaryLanguage{name color}
  repositoryTopics(first:4){nodes{topic{name}}}"""


def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]


if DEMO:
    repos = [
        {"name": "AI-Stock-Sentiment-Analyzer", "description": "Scores financial news headlines with an NLP model and lines sentiment up against daily price moves.",
         "url": "#", "stargazerCount": 3, "forkCount": 1, "pushedAt": "2026-11-10T10:00:00Z", "isFork": False,
         "parent": None, "primaryLanguage": {"name": "Python", "color": "#3572A5"},
         "repositoryTopics": {"nodes": [{"topic": {"name": t}} for t in ["nlp", "finance", "pandas"]]}},
        {"name": "Quickhire", "description": None, "url": "#", "stargazerCount": 0, "forkCount": 0,
         "pushedAt": "2026-06-02T10:00:00Z", "isFork": True, "parent": {"nameWithOwner": "theruknology/quickhire"},
         "primaryLanguage": {"name": "TypeScript", "color": "#3178c6"}, "repositoryTopics": {"nodes": []}},
    ]
else:
    u = gql(f"""query($u:String!){{user(login:$u){{
        pinnedItems(first:6, types:REPOSITORY){{nodes{{... on Repository{{{REPO_FIELDS}}}}}}}
        repositories(first:6, ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC,
                     orderBy:{{field:PUSHED_AT, direction:DESC}}){{nodes{{{REPO_FIELDS}}}}}}}}}""",
            {"u": USER})["user"]
    repos = u["pinnedItems"]["nodes"] or [r for r in u["repositories"]["nodes"] if r["name"].lower() != USER.lower()][:4]

today = dt.datetime.now(dt.timezone.utc)


def ago(iso):
    d = (today - dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))).days
    if d < 1:
        return "today"
    if d < 30:
        return f"{d}d ago"
    if d < 365:
        return f"{d // 30}mo ago"
    return f"{d // 365}y ago"


def pretty(name):
    return re.sub(r"[-_]+", " ", name)


W, H = 420, 170
BG, BORDER, MUTED, TEXT, PILL = "#0d1117", "#21262d", "#7d8590", "#e6edf3", "#161b22"
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
BOOK = ("M4 4.5A2.5 2.5 0 0 1 6.5 2H18a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H6.5a1 1 0 0 0 0 2H18a1 1 0 1 1 0 2H6.5"
        "A3.5 3.5 0 0 1 3 20.5v-16Z")
STAR = ("M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4l-5.9 3.1 1.2-6.5L2.5 9.4l6.6-.9z")
FORK = ("M6 3a3 3 0 0 1 1 5.8V10a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V8.8a3 3 0 1 1 2 0V10a4 4 0 0 1-4 4h-2v1.2"
        "a3 3 0 1 1-2 0V14H9a4 4 0 0 1-4-4V8.8A3 3 0 0 1 6 3z")


def card(r):
    lang = r["primaryLanguage"] or {"name": "—", "color": "#8b949e"}
    desc = r["description"] or (f"Fork of {r['parent']['nameWithOwner']}" if r["isFork"] and r["parent"]
                                else "No description yet.")
    lines = textwrap.wrap(desc, 52)[:2]
    if len(textwrap.wrap(desc, 52)) > 2:
        lines[-1] = lines[-1].rstrip(".,; ") + "…"
    title = pretty(r["name"])
    if len(title) > 34:
        title = title[:33] + "…"

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
         "<style>@keyframes rise{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}"
         ".a{animation:rise .6s ease-out both}</style>",
         f'<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{lang["color"]}" stop-opacity=".9"/>'
         f'<stop offset="1" stop-color="{lang["color"]}" stop-opacity="0"/></linearGradient></defs>',
         f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
         f'<rect x="1" y="1" width="{W*0.6:.0f}" height="2" fill="url(#g)"/>',
         '<g class="a">',
         f'<path transform="translate(22 22) scale(.75)" d="{BOOK}" fill="none" stroke="{MUTED}" stroke-width="2"/>',
         f'<text x="46" y="37" fill="#58a6ff" font-size="16" font-weight="700">{escape(title)}</text>']
    if r["isFork"]:
        o.append(f'<text x="{W-22}" y="36" fill="{MUTED}" font-size="11" text-anchor="end">fork</text>')
    for i, ln in enumerate(lines):
        o.append(f'<text x="22" y="{66 + i*19}" fill="{TEXT}" font-size="13" opacity=".85">{escape(ln)}</text>')

    # topics
    x = 22
    for t in [n["topic"]["name"] for n in r["repositoryTopics"]["nodes"]][:4]:
        w = 16 + len(t) * 6.6
        if x + w > W - 22:
            break
        o.append(f'<rect x="{x}" y="104" width="{w:.0f}" height="20" rx="10" fill="#1f6feb" fill-opacity=".15"/>')
        o.append(f'<text x="{x + w/2:.1f}" y="118" fill="#58a6ff" font-size="11" text-anchor="middle">{escape(t)}</text>')
        x += w + 6

    # footer
    fy = 150
    o.append(f'<circle cx="28" cy="{fy-4}" r="6" fill="{lang["color"]}"/>')
    o.append(f'<text x="40" y="{fy}" fill="{MUTED}" font-size="12">{escape(lang["name"])}</text>')
    x = 48 + len(lang["name"]) * 7 + 14
    o.append(f'<path transform="translate({x} {fy-12}) scale(.6)" d="{STAR}" fill="none" stroke="{MUTED}" stroke-width="2.2"/>')
    o.append(f'<text x="{x+19}" y="{fy}" fill="{MUTED}" font-size="12">{r["stargazerCount"]}</text>')
    x += 19 + len(str(r["stargazerCount"])) * 7 + 14
    o.append(f'<path transform="translate({x} {fy-12}) scale(.6)" d="{FORK}" fill="{MUTED}"/>')
    o.append(f'<text x="{x+19}" y="{fy}" fill="{MUTED}" font-size="12">{r["forkCount"]}</text>')
    o.append(f'<text x="{W-22}" y="{fy}" fill="{MUTED}" font-size="12" text-anchor="end">updated {ago(r["pushedAt"])}</text>')
    o.append("</g></svg>")
    return "\n".join(o)


os.makedirs(OUTDIR, exist_ok=True)
for f in os.listdir(OUTDIR):
    os.remove(os.path.join(OUTDIR, f))

cells = []
for r in repos:
    svg = card(r)
    fname = re.sub(r"[^A-Za-z0-9_.-]", "_", r["name"]) + ".svg"
    open(os.path.join(OUTDIR, fname), "w").write(svg)
    v = hashlib.sha1(svg.encode()).hexdigest()[:8]  # changes only when the card changes
    cells.append(f'<a href="{r["url"]}"><img src="assets/projects/{fname}?v={v}" alt="{escape(r["name"])}" width="49%"/></a>')

block = "<!-- PROJECTS:START -->\n<p align=\"center\">\n  " + "\n  ".join(cells) + "\n</p>\n<!-- PROJECTS:END -->"
if os.path.exists(README):
    s = open(README).read()
    s2 = re.sub(r"<!-- PROJECTS:START -->.*?<!-- PROJECTS:END -->", lambda _: block, s, flags=re.S)
    if s2 != s:
        open(README, "w").write(s2)
print(f"{len(repos)} project card(s)")
