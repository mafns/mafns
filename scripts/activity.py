"""Generate assets/activity.svg — a GitHub activity card that matches the profile page.

Numbers come from GitHub's own contribution calendar (the same one behind
"N contributions in the last year"), so the card and the profile always agree.
Run with DEMO=1 to render with fake data (no token needed).
"""
import datetime as dt
import json
import os
import random
import urllib.request
from html import escape

USER = os.environ.get("GH_USER", "mafns")
TOKEN = os.environ.get("GH_TOKEN", "")
OUT = os.environ.get("OUT_FILE", "assets/activity.svg")
DEMO = os.environ.get("DEMO") == "1"


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


today = dt.datetime.now(dt.timezone.utc).date()
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

# ---------------------------------------------------------------- data
if DEMO:
    rnd = random.Random(7)
    start = today - dt.timedelta(days=today.weekday() + 1 + 52 * 7)
    weeks, d = [], start
    while d <= today:
        week = []
        for _ in range(7):
            if d > today:
                break
            c = rnd.choice([0] * 9 + [1, 2, 3, 5, 8]) if d < today - dt.timedelta(days=7) else rnd.randint(1, 6)
            week.append({"date": d.isoformat(), "contributionCount": c,
                         "contributionLevel": ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE",
                                               "THIRD_QUARTILE", "FOURTH_QUARTILE"][min(4, (c + 1) // 2)]})
            d += dt.timedelta(days=1)
        weeks.append({"contributionDays": week})
    total_year = sum(x["contributionCount"] for w in weeks for x in w["contributionDays"])
    commits, prs = 96, 7
    all_days = {dt.date.fromisoformat(x["date"]): x["contributionCount"] for w in weeks for x in w["contributionDays"]}
    langs = [("Python", 46.1, "#3572A5"), ("HTML", 37.6, "#e34c26"), ("JavaScript", 7.7, "#f1e05a"),
             ("TypeScript", 3.3, "#3178c6"), ("CSS", 3.2, "#663399"), ("Other", 2.1, "#8b949e")]
else:
    info = gql("""query($u:String!){user(login:$u){
        createdAt
        contributionsCollection{
          totalCommitContributions totalPullRequestContributions restrictedContributionsCount
          contributionCalendar{totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}
        repositories(first:100, ownerAffiliations:OWNER, isFork:false){nodes{
          languages(first:10, orderBy:{field:SIZE, direction:DESC}){edges{size node{name color}}}}}}}""",
               {"u": USER})["user"]
    cc = info["contributionsCollection"]
    weeks = cc["contributionCalendar"]["weeks"]
    total_year = cc["contributionCalendar"]["totalContributions"]
    commits = cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
    prs = cc["totalPullRequestContributions"]

    # Full history for streaks
    all_days = {}
    q = """query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){contributionsCollection(from:$f,to:$t){
           contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""
    for y in range(int(info["createdAt"][:4]), today.year + 1):
        r = gql(q, {"u": USER, "f": f"{y}-01-01T00:00:00Z", "t": f"{y}-12-31T23:59:59Z"})
        for w in r["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for x in w["contributionDays"]:
                dd = dt.date.fromisoformat(x["date"])
                if dd <= today:
                    all_days[dd] = x["contributionCount"]

    sizes = {}
    for repo in info["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            n = e["node"]["name"]
            s = sizes.setdefault(n, [0, e["node"]["color"] or "#8b949e"])
            s[0] += e["size"]
    tot = sum(v[0] for v in sizes.values()) or 1
    ranked = sorted(sizes.items(), key=lambda kv: -kv[1][0])
    langs = [(n, v[0] * 100 / tot, v[1]) for n, v in ranked[:5]]
    rest = 100 - sum(p for _, p, _ in langs)
    if rest >= 0.1:
        langs.append(("Other", rest, "#8b949e"))

# ---------------------------------------------------------------- streaks
dates = sorted(all_days)
longest, run = 0, 0
for d in dates:
    run = run + 1 if all_days[d] > 0 else 0
    longest = max(longest, run)

end = today if all_days.get(today, 0) > 0 else today - dt.timedelta(days=1)
current, d = 0, end
while all_days.get(d, 0) > 0:
    current += 1
    d -= dt.timedelta(days=1)

first_day = dt.date.fromisoformat(weeks[0]["contributionDays"][0]["date"])
active_days = sum(1 for w in weeks for x in w["contributionDays"] if x["contributionCount"] > 0)

# ---------------------------------------------------------------- render
W, PAD = 860, 32
BG, BORDER, MUTED, TEXT = "#0d1117", "#21262d", "#7d8590", "#e6edf3"
BLUE, BLUE2 = "#58a6ff", "#1f6feb"
HEAT = ["#161b22", "#0c2d6b", "#1158c7", "#388bfd", "#79c0ff"]

out = []
a = out.append

stats = [
    (f"{total_year:,}", "Contributions", f"since {first_day.strftime('%-d %b %Y')}", BLUE),
    (str(current), "Current streak", "days" if current != 1 else "day", "#ffa657" if current else TEXT),
    (str(longest), "Longest streak", "days" if longest != 1 else "day", TEXT),
    (f"{commits:,}", "Commits", "last 12 months", TEXT),
    (str(active_days), "Active days", "last 12 months", TEXT),
]

# Heatmap geometry
CELL, GAP = 11, 3
STEP = CELL + GAP
ncols = len(weeks)
grid_w = ncols * STEP - GAP
gx = (W - grid_w) / 2
gy = 196
H = 270

a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
  f'font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',Helvetica,Arial,sans-serif">')
a("""<style>
  @keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
  @keyframes pop{from{opacity:0}to{opacity:1}}
  @keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
  @keyframes pulse{0%,100%{opacity:.55}50%{opacity:1}}
  .s{animation:rise .6s ease-out both}
  .c{animation:pop .5s ease-out both}
  .bar{transform-origin:left;animation:grow 1s cubic-bezier(.2,.8,.2,1) both .4s}
  .live{animation:pulse 2s ease-in-out infinite}
</style>""")
a('<defs><linearGradient id="glow" x1="0" x2="1"><stop offset="0" stop-color="#1f6feb" stop-opacity=".0"/>'
  '<stop offset=".5" stop-color="#1f6feb" stop-opacity=".55"/><stop offset="1" stop-color="#1f6feb" stop-opacity="0"/>'
  '</linearGradient><clipPath id="barclip"><rect x="%d" y="%d" width="%d" height="8" rx="4"/></clipPath></defs>'
  % (PAD, H - 60, W - 2 * PAD))
a(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="{BG}" stroke="{BORDER}"/>')
a(f'<rect x="1" y="1" width="{W-2}" height="2" fill="url(#glow)"/>')

# Header
a(f'<text x="{PAD}" y="44" fill="{MUTED}" font-size="12" font-weight="700" letter-spacing="2">GITHUB ACTIVITY</text>')
updated = f'updated {dt.datetime.now(dt.timezone.utc).strftime("%-d %b %Y, %H:%M")} UTC'
a(f'<circle class="live" cx="{W-PAD-len(updated)*5.6-12:.0f}" cy="40" r="4" fill="#3fb950"/>')
a(f'<text x="{W-PAD}" y="44" fill="{MUTED}" font-size="11" text-anchor="end">{updated}</text>')

# Stats row
colw = (W - 2 * PAD) / len(stats)
for i, (num, label, sub, col) in enumerate(stats):
    cx = PAD + colw * i + colw / 2
    delay = i * 0.08
    a(f'<g class="s" style="animation-delay:{delay:.2f}s">')
    a(f'<text x="{cx:.1f}" y="104" fill="{col}" font-size="30" font-weight="700" text-anchor="middle">{escape(num)}</text>')
    a(f'<text x="{cx:.1f}" y="128" fill="{TEXT}" font-size="13" text-anchor="middle">{label}</text>')
    a(f'<text x="{cx:.1f}" y="146" fill="{MUTED}" font-size="11" text-anchor="middle">{escape(sub)}</text>')
    a('</g>')
    if i:
        x = PAD + colw * i
        a(f'<line x1="{x:.1f}" y1="80" x2="{x:.1f}" y2="148" stroke="{BORDER}"/>')

# Languages
by = H - 60
a(f'<text x="{PAD}" y="{by-14}" fill="{MUTED}" font-size="12" font-weight="700" letter-spacing="2">TOP LANGUAGES</text>')
a(f'<rect x="{PAD}" y="{by}" width="{W-2*PAD}" height="8" rx="4" fill="#161b22"/>')
a('<g clip-path="url(#barclip)"><g class="bar">')
x = PAD
for name, pct, color in langs:
    w_ = (W - 2 * PAD) * pct / 100
    a(f'<rect x="{x:.1f}" y="{by}" width="{w_+0.6:.1f}" height="8" fill="{color}"/>')
    x += w_
a('</g></g>')
x = PAD
for name, pct, color in langs:
    label = f"{name} {pct:.1f}%"
    a(f'<circle cx="{x+5}" cy="{by+30}" r="5" fill="{color}"/>')
    a(f'<text x="{x+15}" y="{by+34}" fill="{TEXT}" font-size="12">{escape(name)} '
      f'<tspan fill="{MUTED}">{pct:.1f}%</tspan></text>')
    x += 34 + len(label) * 6.6

a("</svg>")

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
with open(OUT, "w") as f:
    f.write("\n".join(out))
print(f"contributions={total_year} current={current} longest={longest} commits={commits}")
