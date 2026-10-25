"""Build the score-adjusted Ice Tilt table (SCORE_EFFECT in ice_tilt_live.html).

For every regular-season game it rebuilds the per-second tilt the same way analyze() does in the
page, then averages it by score margin and minute of regulation. The result is the tilt a team
usually gets just from being behind: down 1, or down 2 or more, at each minute 0-59. Home ice is
averaged out (home-trailing and away-trailing are combined), so a tied game expects 0.

Run:  python tools/score_curve.py                      (2025-26, prints the table)
      python tools/score_curve.py 20262027             (another season)
      python tools/score_curve.py --update-page        (also rewrites the table in ice_tilt_live.html)
Play-by-play downloads are cached in tools/cache/<season>/, so re-runs only fetch new games.
"""
import gzip
import json
import pathlib
import re
import sys
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
PAGE = HERE.parent / "ice_tilt_live.html"
API = "https://api-web.nhle.com/v1/"
SHRINK = 6000  # seconds of weight that thin down-2+ minutes borrow from the down-1 curve


def get(path):
    for attempt in range(4):
        try:
            req = urllib.request.Request(API + path, headers={"User-Agent": "ice-tilt-live/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.load(resp)
        except Exception as e:
            err = e
            time.sleep(2 + attempt * 3)
    raise err


def download(season, cache):
    cache.mkdir(parents=True, exist_ok=True)
    teams = [t["teamAbbrev"]["default"] for t in get(f"standings/{season[4:]}-04-01")["standings"]]
    ids = set()
    for t in teams:
        for g in get(f"club-schedule-season/{t}/{season}")["games"]:
            if g["gameType"] == 2 and g.get("gameState") in ("OFF", "FINAL"):
                ids.add(g["id"])
    todo = [i for i in sorted(ids) if not (cache / f"{i}.json.gz").exists()]
    print(f"{len(ids)} finished games, {len(todo)} to download", flush=True)

    def one(gid):
        d = get(f"gamecenter/{gid}/play-by-play")
        with gzip.open(cache / f"{gid}.json.gz", "wt", encoding="utf-8") as fh:
            json.dump(d, fh)

    with ThreadPoolExecutor(6) as ex:
        for i, _ in enumerate(ex.map(one, todo), 1):
            if i % 200 == 0:
                print(f"  downloaded {i}/{len(todo)}", flush=True)
    return sorted(cache / f"{i}.json.gz" for i in ids)


def mmss(s):
    return int(s.split(":")[0]) * 60 + int(s.split(":")[1]) if s else 0


def accumulate(files):
    """(minute 0-59, home goal diff clamped to -2..2) -> [sum of home tilt, seconds]"""
    acc = defaultdict(lambda: [0.0, 0])
    for i, f in enumerate(files):
        if i % 200 == 0:
            print(f"  {i}/{len(files)} games", flush=True)
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            d = json.load(fh)
        if d.get("gameType") != 2:
            continue
        home = d["homeTeam"]["id"]
        goals, per = [], {}
        for p in sorted(d.get("plays") or [], key=lambda p: p["sortOrder"]):
            pd = p.get("periodDescriptor") or {}
            n = pd.get("number")
            if pd.get("periodType") != "REG":
                continue
            P = per.setdefault(n, {"raw": [], "votes": 0, "end": None})
            t = mmss(p.get("timeInPeriod"))
            det = p.get("details") or {}
            is_home = det.get("eventOwnerTeamId") == home
            if p["typeDescKey"] == "period-end":
                P["end"] = t
            if p["typeDescKey"] == "goal":
                goals.append((n, t, is_home))
            if isinstance(det.get("xCoord"), (int, float)):
                P["raw"].append((t, det["xCoord"], p.get("homeTeamDefendingSide")))
                # fallback orientation vote, as in the page
                if det.get("zoneCode") == "O" and det.get("eventOwnerTeamId") is not None and det["xCoord"] != 0:
                    P["votes"] += (1 if is_home else -1) * (1 if det["xCoord"] > 0 else -1)
        for n, P in per.items():
            fallback = "left" if P["votes"] >= 0 else "right"
            ev = [(t, max(-1, min(1, x * (-1 if (side or fallback) == "right" else 1) / 89))) for t, x, side in P["raw"]]
            elapsed = P["end"] if P["end"] is not None else (ev[-1][0] if ev else 1200)
            period_goals = sorted((g[1], g[2]) for g in goals if g[0] == n)
            diff = sum((1 if g[2] else -1) for g in goals if g[0] < n)
            j = gi = 0
            val = 0.0
            for s in range(min(elapsed, 1200)):
                while j < len(ev) and ev[j][0] <= s:  # each event's spot holds until the next
                    val = ev[j][1]
                    j += 1
                while gi < len(period_goals) and period_goals[gi][0] <= s:
                    diff += 1 if period_goals[gi][1] else -1
                    gi += 1
                a = acc[((n - 1) * 20 + s // 60, max(-2, min(2, diff)))]
                a[0] += val
                a[1] += 1
    return acc


def curves(acc):
    raw = {}
    for m in range(60):
        for dd in (1, 2):
            behind, ahead = acc.get((m, -dd)), acc.get((m, dd))  # home trailing / home leading by dd
            raw[(m, dd)] = (((behind[0] / behind[1]) - (ahead[0] / ahead[1])) / 2, min(behind[1], ahead[1])) if behind and ahead else (0.0, 0)

    def smooth(dd):
        out = []
        for m in range(60):
            lo, hi = (m // 20) * 20, (m // 20) * 20 + 19
            w = 1 if m >= 54 else 2  # the end of the 3rd changes fast (pulled goalies); smooth more elsewhere
            num = den = 0
            for k in range(max(lo, m - w), min(hi, m + w) + 1):
                v, c = raw[(k, dd)]
                num += v * c
                den += c
            out.append((num / den if den else 0.0, den))
        return out

    one = smooth(1)
    two = [((v * c + one[m][0] * SHRINK) / (c + SHRINK), c) for m, (v, c) in enumerate(smooth(2))]
    return [round(v * 100) for v, _ in one], [round(v * 100) for v, _ in two]


def block(season, games, m1, m2):
    label = f"{season[:4]}-{season[6:]}"
    row = lambda xs: "[" + ", ".join(str(x) for x in xs) + "]"
    return (
        f"  // League-average tilt for the trailing team by regulation minute (0-59), from all {games:,} games of the\n"
        f"  // {label} regular season run through analyze(). Home ice is averaged out, so a tied game expects 0.\n"
        f"  // Down 1 and down 2 or more; the late climb is mostly pulled goalies. Overtime is always tied.\n"
        f"  // Rebuilt by tools/score_curve.py.\n"
        f"  const SCORE_EFFECT = {{\n"
        f"    1: {row(m1)},\n"
        f"    2: {row(m2)},\n"
        f"  }};"
    )


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    season = args[0] if args else "20252026"
    if not re.fullmatch(r"\d{8}", season):
        sys.exit("Season looks like 20252026")
    files = download(season, HERE / "cache" / season)
    print("Building the tilt series...", flush=True)
    m1, m2 = curves(accumulate(files))
    print("down 1 :", " ".join(f"{x:+d}" for x in m1))
    print("down 2+:", " ".join(f"{x:+d}" for x in m2))
    text = block(season, len(files), m1, m2)
    if "--update-page" in sys.argv:
        with open(PAGE, encoding="utf-8", newline="") as fh:  # keep the file's own line endings
            page = fh.read()
        nl = "\r\n" if "\r\n" in page else "\n"
        new, count = re.subn(r"  // League-average tilt for the trailing team.*?\n  const SCORE_EFFECT = \{.*?\n  \};", lambda _: text.replace("\n", nl), page, flags=re.S)
        if count != 1:
            sys.exit("Couldn't find the SCORE_EFFECT block in ice_tilt_live.html")
        with open(PAGE, "w", encoding="utf-8", newline="") as fh:
            fh.write(new)
        print(f"Updated {PAGE.name}")
    else:
        print("\n" + text)


if __name__ == "__main__":
    main()
