// Cloudflare Worker: relays the NHL's public game feed to the GitHub Pages copy of Ice Tilt Live.
//
// The NHL feed doesn't let other websites read it from a browser, so the hosted page asks
// here instead. This does the same job as ice_tilt_live.py: only the five feeds the page
// uses are relayed, and each answer is cached for 5 seconds.

const ALLOWED_ORIGIN = "https://desktoptableau136-commits.github.io";
const API = "https://api-web.nhle.com/v1/";
const CACHE_SECONDS = 5;

const ROUTES = [
  [/^\/api\/score\/(\d{4}-\d{2}-\d{2})$/, (x) => API + `score/${x}`],
  [/^\/api\/pbp\/(\d{10})$/, (x) => API + `gamecenter/${x}/play-by-play`],
  [/^\/api\/box\/(\d{10})$/, (x) => API + `gamecenter/${x}/boxscore`],
  [/^\/api\/rail\/(\d{10})$/, (x) => API + `gamecenter/${x}/right-rail`],
  [/^\/api\/shifts\/(\d{10})$/, (x) => `https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId=${x}`],
];

function reply(status, body, extra = {}) {
  return new Response(body, {
    status,
    headers: {
      "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
      "X-Robots-Tag": "noindex, nofollow",
      ...extra,
    },
  });
}

export default {
  async fetch(request) {
    if (request.method === "OPTIONS") {
      return reply(204, null, { "Access-Control-Allow-Methods": "GET, OPTIONS" });
    }
    if (request.method !== "GET") return reply(405, JSON.stringify({ error: "GET only" }));

    const path = new URL(request.url).pathname;
    for (const [rx, target] of ROUTES) {
      const m = path.match(rx);
      if (!m) continue;
      try {
        const resp = await fetch(target(m[1]), {
          headers: { "User-Agent": "ice-tilt-live/1.0" },
          cf: { cacheTtl: CACHE_SECONDS, cacheEverything: true },
        });
        if (!resp.ok) return reply(resp.status, JSON.stringify({ error: `NHL feed returned ${resp.status}` }));
        return reply(200, resp.body);
      } catch (e) { // network down, timeout
        return reply(502, JSON.stringify({ error: String(e) }));
      }
    }
    return reply(404, JSON.stringify({ error: "Not found" }));
  },
};
