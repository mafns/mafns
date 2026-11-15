"""Watch the contribution count and rebuild the profile card the moment it changes.

Runs inside one long GitHub Actions job: polls GitHub's contribution calendar
(the same number as "N contributions in the last year") every POLL seconds and
dispatches the "Update profile stats" workflow when the count changes or the
day rolls over (streaks change at midnight UTC). Near the job's time limit it
starts a fresh copy of itself, so it runs around the clock.
"""
import datetime as dt
import json
import os
import re
import time
import urllib.request

USER = os.environ["GH_USER"]
REPO = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["GH_TOKEN"]
POLL = int(os.environ.get("POLL_SECONDS", "30"))
RUN_FOR = int(os.environ.get("RUN_MINUTES", "340")) * 60
BUILD_WORKFLOW = "profile.yml"
SELF_WORKFLOW = "watch.yml"


def api(url, body=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"bearer {TOKEN}", "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    return json.loads(raw) if raw else None


def total():
    d = api("https://api.github.com/graphql", {
        "query": "query($u:String!){user(login:$u){contributionsCollection{"
                 "contributionCalendar{totalContributions}}}}",
        "variables": {"u": USER}})
    return d["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]


def dispatch(workflow):
    api(f"https://api.github.com/repos/{REPO}/actions/workflows/{workflow}/dispatches", {"ref": "main"})


def card_total():
    """The number currently shown on the card, so a restart doesn't rebuild needlessly."""
    try:
        svg = open("assets/activity.svg").read()
        return int(re.search(r'font-size="30"[^>]*>([\d,]+)<', svg).group(1).replace(",", ""))
    except Exception:
        return None


last = card_total()
day = dt.datetime.now(dt.timezone.utc).date()
start = time.time()
print(f"watching {USER}: card shows {last}, polling every {POLL}s", flush=True)

while time.time() - start < RUN_FOR:
    try:
        now_total = total()
        today = dt.datetime.now(dt.timezone.utc).date()
        if now_total != last or today != day:
            print(f"{dt.datetime.now(dt.timezone.utc):%H:%M:%S} {last} -> {now_total} (day {today}); rebuilding",
                  flush=True)
            dispatch(BUILD_WORKFLOW)
            last, day = now_total, today
    except Exception as e:  # network blips / rate limits: just try again next tick
        print(f"poll failed: {e}", flush=True)
    time.sleep(POLL)

print("time limit reached, handing over to a fresh watcher", flush=True)
dispatch(SELF_WORKFLOW)
