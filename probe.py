import csv, io, urllib.request
from collections import Counter
def get(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30)
        return r.status, r.geturl(), r.read()
    except Exception as e:
        return getattr(e, "code", str(e)), u, b""
for u in ["https://reel-shelf.github.io/Matchday-Egde/", "https://reel-shelf.github.io/Matchday-Edge/",
          "https://raw.githubusercontent.com/reel-shelf/Matchday-Egde/live-data/data/live.json"]:
    s, final, body = get(u)
    print("URL", u, "->", s, final, len(body), "bytes")
s, _, body = get("https://www.football-data.co.uk/fixtures.csv")
rows = list(csv.DictReader(io.StringIO(body.decode("utf-8-sig", "replace"))))
print("fixtures.csv:", s, len(rows), "rows; columns:", list(rows[0])[:12] if rows else None)
ours = {"E0", "E1", "SP1", "I1", "D1", "F1", "N1", "P1"}
print("by division:", Counter(r.get("Div") for r in rows).most_common(30))
for r in [r for r in rows if r.get("Div") in ours][:12]:
    print("  ", r.get("Div"), r.get("Date"), r.get("Time"), r.get("HomeTeam"), "v", r.get("AwayTeam"), r.get("B365H"), r.get("B365D"), r.get("B365A"), r.get("B365>2.5"))
