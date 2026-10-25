# Ice Tilt Live

A live Ice Tilt dashboard for any NHL game. It approximates the NHL/AWS "Ice Tilt" stat using the NHL's public play-by-play feed.

## Run it

```
python ice_tilt_live.py
```

This opens http://127.0.0.1:8765 in your browser. Phones and tablets on the same Wi-Fi can open the address printed in the terminal, like `http://192.168.x.x:8765/`. It needs Python 3 and nothing else. Press Ctrl+C to stop.

- The first time, allow Python through Windows Firewall on **Private** networks. On Public networks, like hotels and cafés, Windows keeps blocking other devices.
- `python ice_tilt_live.py --local` makes it work on this computer only
- `python ice_tilt_live.py 9000` runs it on a different port
- `python ice_tilt_live.py --no-browser` starts it without opening a browser
- On a touch screen, tap a goal once for details and again for the highlight.

## What's on the dashboard

- Pick any date and game. Live games refresh every 5 seconds.
- **Ice Tilt meter:** the official two-minute rolling tilt with a label (Even, Leaning, Tilted, Hemmed in), plus **5 and 10 minute** comparison boxes. The verdict line points out when the short and long windows disagree.
- **Rink:** where the events of the last two minutes happened, in team colors, with a dashed line marking the average position of play over those two minutes.
- **Score effect:** late in a game, the team that's behind usually pushes while the leader sits back, so the tilt can make the losing team look dominant. When the trailing team is tilting the ice in the 3rd (or the 2nd, down by 2+), the verdict says so and a **Score effect** tag appears. With the goalie pulled it shows **Goalie pulled** instead.
- **Score-adjusted tilt** (Tilt menu in the top bar, remembered): takes away the push a trailing team usually gets. All 1,312 games of the 2025–26 regular season were run through the same method to find the average tilt for a team down 1, or down 2+, at each minute of regulation. That's subtracted second by second from the meter, the 5/10 min boxes, the chart and the period table. Home ice is averaged out and overtime is unadjusted, since it's always tied. The rink always shows raw position.
- **Replay follows everywhere:** when you rewind or replay, the scoreboard, period table, box score and player stats all show the game as of that moment. They're rebuilt from the play-by-play, with ice time and +/− from the NHL shift charts.
- **Tilt over the game:** a timeline of the 2 min tilt (shaded) with 5 min (solid) and 10 min (dashed) lines you can toggle, plus goals, power plays (PP) and pulled-goalie stretches (EN). EN is the extra-attacker advantage. It's read from the feed's on-ice situation, and brief pulls for a delayed penalty are left out.
  - Hover a goal for the scorer, assists, strength, score and the tilt just before it. Click it to open the NHL highlight video.
  - Drag across the chart, or use the arrow keys, to rewind. **Replay** plays the whole game back.
- **Team logos** on the scoreboard, game list, tilt meter and at center ice. Goal hovers show the **scorer's headshot**. Both come from the NHL's own image server.
- **By period** (under the Ice Tilt meter): average tilt, offensive-zone events, shots and goals for each period.
- **Stats column** (full height on the right) has two tabs. Your choice is remembered.
  - **Box score:** goals by period with totals and shots, team stats (shots, faceoffs, power play, hits, blocks, penalty minutes, giveaways, takeaways), and a scoring summary with each scorer's headshot. Click a scorer's name to watch the goal.
  - **Players:** skater and goalie stats with headshots for either team (switch with the logo buttons). Click a column heading to sort.
- **TV delay** (top bar, off by default) holds the feed back so it doesn't run ahead of your broadcast. It delays the game list scores too, so nothing gets spoiled. Set it to 10–60 s to match your provider. Your choice is remembered.
- On laptop and desktop windows it fits on one screen. Narrow windows get a scrolling layout.

## How the number is made

The official stat uses private player tracking at about 100 positions per second. This version uses the public NHL game feed instead. That feed logs every shot, hit, faceoff, takeaway, giveaway, goal and penalty with its spot on the ice, about one event every 10–15 seconds. Each event's spot counts as where play was until the next event. Those spots are averaged over the last two minutes of game clock, and the average restarts each period.

The direction and the swings follow the official idea. The size of the number won't match a broadcast graphic.

## Files

- `ice_tilt_live.py`: a small local server that serves the page and relays `api-web.nhle.com`. The relay is needed because browsers can't call that API directly from a page.
- `ice_tilt_live.html`: the dashboard.
- `tap-along-tracker.html`: the manual Ice Tilt Tap-Along. Open it straight in a browser (no Python needed) and tap where play is to track a game by hand.
