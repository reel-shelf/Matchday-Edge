#!/usr/bin/env python3
"""
Matchday Edge: bookmaker odds for upcoming club games, refreshed every 30 minutes.

1. Bet365, from football-data.co.uk's free fixtures file (posted a few days before
   each round). Matched to our games through the spreadsheet team names predict.py
   saves in predictions.json ("csvNames").
2. Where Bet365 isn't there yet: DraftKings, from ESPN's free (unofficial) scoreboard,
   which lists club odds further ahead. Matched by kick-off time and team names.

Writes club-odds.json in LIVE_DIR; the app and tracker.py use it alongside the other odds.
Run every 5 minutes by .github/workflows/team-news.yml (it only works every 30 minutes).
"""
import csv
import io
import json
import os
import time
from datetime import datetime, timedelta, timezone

from intl import get, espn_odds
from predict import csv_odds, parse_csv_date, CORNER_FILES, FIXTURES_URL
from team_news import similar

OUT_DIR = os.environ.get("OUT_DIR", "data")
LIVE_DIR = os.environ.get("LIVE_DIR", OUT_DIR)
PATH = os.path.join(LIVE_DIR, "club-odds.json")
EVERY = timedelta(minutes=30)
AHEAD = timedelta(days=4)
ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer"
SLUGS = {"PL": "eng.1", "ELC": "eng.2", "PD": "esp.1", "SA": "ita.1", "BL1": "ger.1", "FL1": "fra.1",
         "DED": "ned.1", "PPL": "por.1", "CL": "uefa.champions"}


def load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def parse(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def main():
    now = datetime.now(timezone.utc)
    old = load(PATH, {"updated": None, "matches": {}})
    if old.get("updated") and now - parse(old["updated"]) < EVERY:
        return
    preds = load(os.path.join(OUT_DIR, "predictions.json"), {"matches": []})
    games = [m for m in preds.get("matches", []) if m.get("league") in SLUGS and m.get("homeId")
             and now < parse(m["date"]) < now + AHEAD]
    out = {}

    # 1. Bet365 from the fixtures file
    names = preds.get("csvNames") or {}
    div_code = {f: c for c, f in CORNER_FILES.items()}
    text = get(FIXTURES_URL, raw=True)
    for r in csv.DictReader(io.StringIO(text or "")):
        code = div_code.get((r.get("Div") or "").strip())
        d, o = parse_csv_date(r.get("Date")), csv_odds(r)
        if not code or not d or not o:
            continue
        hid = (names.get(code) or {}).get((r.get("HomeTeam") or "").strip())
        aid = (names.get(code) or {}).get((r.get("AwayTeam") or "").strip())
        for m in games:
            if m["league"] == code and m["homeId"] == hid and m["awayId"] == aid \
                    and abs((parse(m["date"]).date() - d).days) <= 1:
                out[str(m["id"])] = {"book": "Bet365", **o}

    # 2. DraftKings from ESPN for the rest (ESPN files games by US date, so ask for both days)
    rest = [m for m in games if str(m["id"]) not in out]
    days = set()
    for m in rest:
        k = parse(m["date"])
        days |= {(m["league"], k.strftime("%Y%m%d")), (m["league"], (k - timedelta(hours=6)).strftime("%Y%m%d"))}
    for code, day in sorted(days):
        sb = get(f"{ESPN}/{SLUGS[code]}/scoreboard?dates={day}") or {}
        time.sleep(0.2)
        for e in sb.get("events") or []:
            c = e["competitions"][0]
            side = {x.get("homeAway"): x for x in c["competitors"]}
            if "home" not in side or "away" not in side:
                continue
            o = espn_odds(c)
            if not o:
                continue
            when = parse(e["date"])
            for m in rest:
                if m["league"] != code or str(m["id"]) in out or abs((parse(m["date"]) - when).total_seconds()) > 3 * 3600:
                    continue
                score = similar(m["home"]["name"], side["home"]["team"]["displayName"]) \
                    + similar(m["away"]["name"], side["away"]["team"]["displayName"])
                if score >= 1.5:
                    out[str(m["id"])] = o
                    break

    os.makedirs(LIVE_DIR, exist_ok=True)
    with open(PATH, "w") as f:
        json.dump({"updated": now.isoformat().replace("+00:00", "Z"), "matches": out}, f, separators=(",", ":"))
    books = {}
    for v in out.values():
        books[v.get("book")] = books.get(v.get("book"), 0) + 1
    print(f"Club odds: {len(out)} of {len(games)} upcoming games {books}")


if __name__ == "__main__":
    main()
