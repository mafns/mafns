import datetime as dt
import json
import os
import urllib.request

USER = os.environ["GH_USER"]
TOKEN = os.environ["GH_TOKEN"]
OUT = os.environ.get("OUT_FILE", "assets/streak.svg")


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


created = gql("query($u:String!){user(login:$u){createdAt}}", {"u": USER})["user"]["createdAt"]
start_year = int(created[:4])
today = dt.datetime.now(dt.timezone.utc).date()

CAL_Q = """
query($u:String!,$from:DateTime!,$to:DateTime!){
  user(login:$u){contributionsCollection(from:$from,to:$to){
    contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}
"""

days = {}
for year in range(start_year, today.year + 1):
    cal = gql(CAL_Q, {"u": USER, "from": f"{year}-01-01T00:00:00Z", "to": f"{year}-12-31T23:59:59Z"})
    for w in cal["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
        for d in w["contributionDays"]:
            date = dt.date.fromisoformat(d["date"])
            if date <= today:
                days[date] = d["contributionCount"]

dates = sorted(days)
total = sum(days.values())
first_contrib = next((d for d in dates if days[d] > 0), dates[0])

longest = (0, None, None)
run_start, run_len = None, 0
for d in dates:
    if days[d] > 0:
        if run_len == 0:
            run_start = d
        run_len += 1
        if run_len > longest[0]:
            longest = (run_len, run_start, d)
    else:
        run_len = 0

cur_len, cur_end = 0, today
if days.get(today, 0) == 0:
    cur_end = today - dt.timedelta(days=1)
d = cur_end
while days.get(d, 0) > 0:
    cur_len += 1
    d -= dt.timedelta(days=1)
cur_start = d + dt.timedelta(days=1)


def fmt(x):
    return x.strftime("%b %-d") if x.year == today.year else x.strftime("%b %-d, %Y")


def rng(a, b, n):
    if n == 0:
        return "—"
    return fmt(a) if a == b else f"{fmt(a)} - {fmt(b)}"


total_range = f"{first_contrib.strftime('%b %-d, %Y')} - Present"
cur_range = rng(cur_start, cur_end, cur_len)
long_range = rng(longest[1], longest[2], longest[0])

BG, BLUE, TXT, SUB, LINE = "#0d1117", "#58a6ff", "#ffffff", "#8b949e", "#30363d"
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195">
<style>
  .num{{font:700 28px 'Segoe UI',Ubuntu,sans-serif;fill:{BLUE}}}
  .big{{font:700 28px 'Segoe UI',Ubuntu,sans-serif;fill:{TXT}}}
  .lbl{{font:400 14px 'Segoe UI',Ubuntu,sans-serif;fill:{TXT}}}
  .lblb{{font:700 14px 'Segoe UI',Ubuntu,sans-serif;fill:{TXT}}}
  .sub{{font:400 12px 'Segoe UI',Ubuntu,sans-serif;fill:{SUB}}}
</style>
<rect width="495" height="195" rx="4.5" fill="{BG}"/>
<line x1="165" y1="28" x2="165" y2="170" stroke="{LINE}"/>
<line x1="330" y1="28" x2="330" y2="170" stroke="{LINE}"/>
<text x="82.5" y="79" text-anchor="middle" class="num">{total}</text>
<text x="82.5" y="118" text-anchor="middle" class="lbl">Total Contributions</text>
<text x="82.5" y="145" text-anchor="middle" class="sub">{total_range}</text>
<circle cx="247.5" cy="71" r="40" fill="none" stroke="#1f6feb" stroke-width="5"/>
<text x="247.5" y="81" text-anchor="middle" class="big">{cur_len}</text>
<text x="247.5" y="140" text-anchor="middle" class="lblb">Current Streak</text>
<text x="247.5" y="164" text-anchor="middle" class="sub">{cur_range}</text>
<text x="412.5" y="79" text-anchor="middle" class="num">{longest[0]}</text>
<text x="412.5" y="118" text-anchor="middle" class="lbl">Longest Streak</text>
<text x="412.5" y="145" text-anchor="middle" class="sub">{long_range}</text>
</svg>
"""

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
with open(OUT, "w") as f:
    f.write(svg)
print(f"total={total} current={cur_len} longest={longest[0]}")
