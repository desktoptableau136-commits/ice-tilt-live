# Ice Tilt Live

A live Ice Tilt dashboard for any NHL game. It approximates the NHL/AWS "Ice Tilt" stat using the NHL's public play-by-play feed.

## Run it

```
python ice_tilt_live.py
```

This opens http://127.0.0.1:8765 in your browser. It needs Python 3 and nothing else. Press Ctrl+C to stop.

- `python ice_tilt_live.py 9000` runs it on a different port
- `python ice_tilt_live.py --no-browser` starts it without opening a browser

## What's on the dashboard

- Pick any date and game. Live games refresh every 5 seconds.
- **Ice Tilt meter:** a two-minute rolling tilt with a label (Even, Leaning, Tilted, Hemmed in) and each team's territorial share.
- **Rink:** where the events of the last two minutes happened, in team colors.
- **Tilt over the game:** a timeline of the tilt with goals and power plays marked.
  - Hover a goal for the scorer, assists, strength, score and the tilt just before it. Click it to open the NHL highlight video.
  - Drag across the chart, or use the arrow keys, to rewind. **Replay game** plays the whole game back.
- **By period:** average tilt, offensive-zone events, shots and goals for each period.
- **TV delay** (top bar, off by default) holds the feed back so it doesn't run ahead of your broadcast. It delays the game list scores too, so nothing gets spoiled. Set it to 10–60 s to match your provider. Your choice is remembered.
- On laptop and desktop windows it fits on one screen. Narrow windows get a scrolling layout.

## How the number is made

The official stat uses private player tracking at about 100 positions per second. This version uses the public NHL game feed instead. That feed logs every shot, hit, faceoff, takeaway, giveaway, goal and penalty with its spot on the ice, about one event every 10–15 seconds. Each event's spot counts as where play was until the next event. Those spots are averaged over the last two minutes of game clock, and the average restarts each period.

The direction and the swings follow the official idea. The size of the number won't match a broadcast graphic.

## Files

- `ice_tilt_live.py`: a small local server that serves the page and relays `api-web.nhle.com`. The relay is needed because browsers can't call that API directly from a page.
- `ice_tilt_live.html`: the dashboard.
- `ice-tilt.html`: a manual tap-along tracker for when you want to track a game by hand.
