#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""producthunt-scout — today's Product Hunt launches judged as POSSIBLE STARTUPS.

A product that launches on PH and pulls real upvotes/comments is a live product an
audience showed up for on day one — high startup-idea density and a genuine DEMAND
signal (people voting with attention). Same idea model as the other scouts
(what / why-good / commercial value / risk), no predictions.

Auth: needs a Product Hunt developer token in env PRODUCTHUNT_TOKEN. If it is absent
the scout skips cleanly (posts nothing, exits 0) so the hourly job never goes red."""
import os, json, datetime, urllib.request, urllib.error
import scout_lib as S

API = "https://api.producthunt.com/v2/api/graphql"
KILL = ["course", "ebook", "e-book", "newsletter", "giveaway", "wallpaper", "merch",
        "template pack", "icon pack", "nsfw", "onlyfans"]
TOOL_KW = ["cli", "sdk", "api", "framework", "library", "tool", "self-host", "self hosted",
           "open source", "open-source", "app", "platform", "automation", "workflow", "agent",
           "dashboard", "editor", "engine", "runtime", "extension", "plugin"]
VALUE = {"agent-infra": "infra AI products need — usage-based API + hosted tier",
         "consumer-ai": "a workflow people pay a monthly seat for",
         "edge-ai": "on-device kills cloud cost + unlocks privacy buyers",
         "research": "productize the method for teams who can't build it",
         "pain-points": "turn a manual workaround into subscription revenue",
         "other": "a paid wedge if it owns one workflow end-to-end"}

QUERY = ("query($after:DateTime!){posts(order:VOTES,first:40,postedAfter:$after)"
         "{edges{node{name tagline description url website votesCount commentsCount "
         "topics(first:5){edges{node{name}}}}}}}")

def _gql(token, after):
    body = json.dumps({"query": QUERY, "variables": {"after": after}}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json",
        "Accept": "application/json", "User-Agent": "future-scout/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def build():
    token = os.environ.get("PRODUCTHUNT_TOKEN")
    if not token:
        print("[producthunt-scout] no PRODUCTHUNT_TOKEN — skipping"); return []
    after = (datetime.datetime.utcnow() - datetime.timedelta(days=2)).strftime("%Y-%m-%dT00:00:00Z")
    data = _gql(token, after)
    edges = (((data or {}).get("data") or {}).get("posts") or {}).get("edges") or []
    out = []
    for e in edges:
        n = e.get("node") or {}
        name = (n.get("name") or "").strip()
        tagline = (n.get("tagline") or "").strip()
        site = n.get("website") or n.get("url")
        if not name or not site:
            continue
        topics = [t["node"]["name"] for t in (n.get("topics") or {}).get("edges", []) if t.get("node")]
        blob = f"{name} {tagline} {(n.get('description') or '')} {' '.join(topics)}".lower()
        if any(k in blob for k in KILL):
            continue
        votes = n.get("votesCount") or 0
        nc = n.get("commentsCount") or 0
        dom = S.infer_domain(blob, "consumer-ai")
        # must be software/tool-shaped OR clearly in a product domain
        if not (S.has_kw(blob, TOOL_KW) or dom != "other"):
            continue
        sc = {
            "traction": 2 if votes >= 500 else (1 if votes >= 200 else 0),
            "engage":   2 if nc >= 60 else (1 if nc >= 15 else 0),
            "buyer":    2 if dom in ("agent-infra", "consumer-ai", "edge-ai", "pain-points") else 1,
            "wedge":    2 if S.has_kw(blob, TOOL_KW) else 1,
            "launched": 2,   # it's a real, shipped product with a live site
        }
        score = sum(sc.values())
        if score < 7:
            continue
        out.append({
            "_score": score, "_votes": votes,
            "title": name[:110],
            "claim": f"Product Hunt: {name} — {tagline[:120]}",
            "score": score,
            "why_good": (f"Launched on Product Hunt with {votes} upvotes and {nc} comments — "
                         "a real audience showed up on day one, which most products never get."),
            "value": VALUE.get(dom, VALUE["other"]),
            "risk": ("Product Hunt spikes fade — check 30-day retention and whether it's a feature "
                     "a bigger tool just absorbs."),
            "evidence": [site, n.get("url") or "", f"{votes} PH upvotes", f"{nc} comments"] +
                        ([", ".join(topics[:4])] if topics else []),
            "method": "producthunt api v2 (top launches, last 2d) + startup-worthiness score",
            "domain": dom, "model": "future-scout/producthunt", "operator": "@ourword-ai",
            "tags": (topics[:5] or ["product-hunt"])})
    out.sort(key=lambda f: (f["_score"], f["_votes"]), reverse=True)
    for f in out:
        f.pop("_score", None); f.pop("_votes", None)
    return out

if __name__ == "__main__":
    try:
        cands = build()
    except urllib.error.HTTPError as e:
        print(f"[producthunt-scout] HTTP {e.code} — skipping: {e.read()[:200]!r}"); cands = []
    except Exception as e:
        print(f"[producthunt-scout] source unavailable, skipping: {e!r}"); cands = []
    posted = S.post_ideas(cands, "producthunt-scout", cap=8)
    print(json.dumps({"scout": "producthunt-scout", "posted": len(posted)}))
