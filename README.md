# Ice Tilt Live

A live Ice Tilt dashboard for every NHL game, built from the NHL's public play-by-play feed. It approximates the NHL/AWS "Ice Tilt" stat: where the play has been over the last two minutes.

## Run it

```
python ice_tilt_live.py
```

Opens http://127.0.0.1:8765 on the day's games. Phones and tablets on the same Wi-Fi can use the address printed in the terminal. Needs Python 3 only; Ctrl+C stops it.

| Option | Does |
| --- | --- |
| `--local` | this computer only |
| `9000` | a different port |
| `--no-browser` | don't open a browser |

The first time, allow Python through Windows Firewall on **Private** networks. On Public networks (hotels, cafés) other devices stay blocked.

## Hosted copy

The page also runs on this repo's GitHub Pages site, with no Python needed. Browsers can't read the NHL feed from another website, so the hosted page goes through a small Cloudflare Worker (`worker/worker.js`) that does the same relay job as `ice_tilt_live.py`. The pages and the Worker tell search engines not to list them.

To update the Worker, paste `worker/worker.js` into the Cloudflare dashboard (Workers & Pages → ice-tilt-live → Edit code) and click **Deploy**.

## All games

The page opens on a tile for every game on the date. Click a tile to open that game. **All games** or Back returns. A link like `#2026020180` opens a game directly.

- **Live tiles:** score, clock and period (with an intermission countdown), and a small rink of the last two minutes that tips up to 5° toward the end under pressure. They also show the 2 min and whole-game tilt, a tilt strip for the game, and shots, attempts and hits (the date's highest is marked **most**).
- **Latest play** in a few words ("NJD hit · Hughes on Benn · 9:31"), ringed on the small rink.
- **Tags:** PP with time left, EN (goalie pulled), 4 on 4, Close & late (one-goal or tied game, last 10 min of the 3rd), Overtime, Shootout, and a **flurry** (4+ shots on goal by one team in 2 minutes).
- **Goals** flash their tile in the scorer's color for a minute. The latest goal stays on the tile with a **Watch** link once the highlight is up. The **Goals** strip on top lists the date's goals, newest first.
- **Pins** put a game first in its section and in the game list. NJD and PIT games start pinned.
- **Goal banners:** while you watch one game, goals elsewhere pop up bottom right for 15 s (30 s if pinned). Hovering holds them, and on phones you can swipe them away.
- **Replay all** plays every started game back on one shared clock at 1×, 2× or 3× (a full night takes about 40 s at 3×). Goals flash as they happen, games move to Final as they end, and the Goals strip hides until it's over.
- **Later** tiles show start time, records, arena and TV. **Final** tiles show the tilt strip, game tilt and counters.
- Scores refresh every 5 s and live play-by-play every 10 s.

## One game

- **Ice Tilt meter:** the 2 min rolling tilt, labeled Even, Leaning, Tilted or Dominant, with **5 and 10 min** boxes. The verdict line notes when short and long windows disagree.
- **Rink:** the last two minutes of events in team colors, with dashed lines at the average position of play over 2, 5 and 10 minutes.
- **Score effect:** a trailing team usually pushes late while the leader sits back. When that's what the tilt shows, a **Score effect** tag says so, or **Goalie pulled** with an extra attacker.
- **Tilt over the game:** the 2 min tilt (shaded) with 5 and 10 min lines, goals, power plays (PP) and pulled goalies (EN). Hover a goal for the details; click it for the highlight.
- **Rewind and replay:** drag across the chart, or use ←/→ (Shift for a minute, Home for the start, Esc for live). **Replay** plays the game back at 1×, 2× or 3×. The scoreboard, period table and stats all follow, rebuilt from the play-by-play, with ice time, +/− and who's on the ice from the NHL shift charts.
- **By period:** average tilt, offensive-zone events, shots and goals per period.
- **Stats column:** **Box score** (linescore, team stats, scoring summary), **Players** (sortable skater and goalie stats) and **Events** (every play, filterable; click one to rewind there).
- Live games refresh every 5 s. On laptop and desktop windows it fits on one screen; narrow windows scroll.

## Top bar settings

- **TV delay** (off, 10–60 s) holds the feed back so the page doesn't spoil your broadcast, including scores in the game list and tiles.
- **Tilt: Score-adjusted** subtracts the push a trailing team usually gets (see below). The rinks always show raw position.
- These are remembered per browser, as are replay speed, pins, the stats tab, the Players team and sort, the Events filter, and the 5/10 min line toggles. The hosted and local pages keep separate settings.

## How the number is made

The official stat uses private player tracking at about 100 positions a second. This one uses the public game feed, which logs every shot, hit, faceoff, takeaway, giveaway, goal and penalty with its spot on the ice, roughly one every 10–15 seconds. Each event's spot counts as where play was until the next event. Those spots are averaged over the last two minutes of game clock, and the average restarts each period. The direction and the swings follow the official idea; the size won't match a broadcast graphic.

**Score-adjusted:** all 1,312 games of the 2025–26 regular season were run through the same method to find the average tilt for a team down 1, or down 2+, at each minute of regulation. That's subtracted second by second. Home ice is averaged out; overtime is always tied, so it's unadjusted.

## How it fits together

The page is one self-contained file. It asks for five feeds under `/api/…` (scores, play-by-play, box score, team stats, shift charts). Locally `ice_tilt_live.py` answers them, and on GitHub Pages the Worker does. Either relay passes the request to the NHL's API and caches each answer for 5 seconds.

| File | What it is |
| --- | --- |
| `ice_tilt_live.html` | the whole app: HTML, CSS and JavaScript |
| `ice_tilt_live.py` | local server: serves the page and relays the NHL feed |
| `worker/worker.js` | Cloudflare Worker: the same relay for the hosted page |
| `index.html` | GitHub Pages entry; forwards to the dashboard |
| `manifest.webmanifest`, `icons/` | Add to Home Screen support |
| `tools/score_curve.py` | rebuilds the score-adjusted table from a season (below) |
| `tap-along-tracker.html` | Ice Tilt Tap-Along: track a game by hand by tapping where play is. Open it straight in a browser. |

`python tools/score_curve.py --update-page` downloads the 2025–26 season, rebuilds the table and writes it into `ice_tilt_live.html`. Add a season like `20262027` for another year. Downloads are cached in `tools/cache/` (not committed), so a re-run only fetches new games; the first run takes a few minutes.
