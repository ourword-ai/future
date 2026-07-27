#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gh-scout — discovers repos and SCORES them against the selection standard.
Only surfaces ideas that pass (>=7/10, no kill-gate), each with why / wedge / risk
and one falsifiable, auto-verified prediction. Heuristic v1; the autopilot layers
real judgment on top."""
import os, json, datetime, urllib.parse
import scout_lib as S

HORIZON_DAYS = 2
KILL_KW = ["linkedin", "instagram", "tiktok bot", "twitter bot", "auto-dm", "mass dm",
           "follower bot", "engagement bot"]   # platform-parasite proxies
TOOL_KW = ["cli", "sdk", "api", "framework", "library", "tool", "runtime", "engine",
           "mcp", "self-host", "self host", "open-source", "open source"]
HEAVY_KW = ["enterprise", "at scale", "kubernetes operator", "data center", "datacenter",
            "gpu cluster", "foundation model training"]
WEDGE = {"agent-infra": 'slot into existing agent stacks; ride "<x> alternative" search',
         "consumer-ai": "win a vertical the general tool ignores",
         "edge-ai": "lean into the local / offline / privacy angle",
         "research": "turn the method into a usable tool",
         "pain-points": "package the workaround people already hack together"}

def evaluate(name, desc, topics, stars, age, vel, dom):
    text = f"{name} {desc} {' '.join(topics)}".lower()
    if any(k in text for k in KILL_KW):
        return None  # kill-gate: platform-parasite
    sc = {
        "pull": 2 if stars >= 2000 else (1 if stars >= 500 else 0),
        "early": 2 if age <= 14 else (1 if age <= 30 else 0),
        "wedge": 2 if any(k in text for k in TOOL_KW) else 1,
        "solo": 0 if any(k in text for k in HEAVY_KW) else 2,
        "edge": 2 if vel >= 500 else (1 if vel >= 100 else 0),
    }
    total = sum(sc.values())
    bits = []
    if sc["pull"] == 2: bits.append(f"strong pull ({stars:,}★)")
    if sc["early"] == 2: bits.append(f"very early ({age}d old)")
    if sc["edge"] == 2: bits.append(f"high momentum (~{int(vel)}/day)")
    why = "; ".join(bits) or f"{stars:,}★, ~{int(vel)}/day"
    return total, why, WEDGE.get(dom, "underserved niche + comparison-page SEO"), \
        "momentum may be a launch spike, not durable demand"

def build():
    today = datetime.date.today()
    since = (today - datetime.timedelta(days=30)).isoformat()
    resolve_on = (today + datetime.timedelta(days=HORIZON_DAYS)).isoformat()
    q = urllib.parse.quote(f"created:>{since} stars:>200")
    url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page=40"
    hdr = {"Accept": "application/vnd.github+json"}
    tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if tok:
        hdr["Authorization"] = f"Bearer {tok}"
    data = json.loads(S.http_get(url, hdr))
    out = []
    for it in data.get("items", []):
        desc = (it.get("description") or "").strip()
        stars = it.get("stargazers_count", 0)
        if not desc:
            continue
        try:
            created = datetime.date.fromisoformat(it["created_at"][:10])
            age = max(1, (today - created).days)
        except Exception:
            continue
        vel = stars / age
        if vel < 20:
            continue
        topics = it.get("topics", []) or []
        dom = S.infer_domain(f"{it['full_name']} {desc} {' '.join(topics)}", "agent-infra")
        ev = evaluate(it["full_name"], desc, topics, stars, age, vel, dom)
        if not ev:
            continue
        total, why, wedge, risk = ev
        if total < 7:          # selection bar
            continue
        target = stars + int(round(vel * HORIZON_DAYS))
        out.append({
            "_score": total,
            "claim": f"{it['full_name']} — {desc[:100]}",
            "score": total, "why": why, "wedge": wedge, "risk": risk,
            "evidence": [it["html_url"], f"stars_now: {stars}", f"velocity: ~{int(round(vel))}/day",
                         f"created: {it['created_at'][:10]}"],
            "method": "github discovery + selection-standard score (heuristic v1)",
            "domain": dom, "model": "future-scout/github", "operator": "@ourword-ai",
            "tags": (topics[:5] or []),
            "prediction": {"metric": "github_stars", "target_id": it["full_name"],
                           "op": ">=", "target": target, "resolve_on": resolve_on},
        })
    out.sort(key=lambda f: (f["_score"], f["prediction"]["target"]), reverse=True)
    for f in out:
        f.pop("_score", None)
    return out

if __name__ == "__main__":
    try:
        cands = build()
    except Exception as e:
        print(f"[gh-scout] source unavailable, skipping: {e!r}"); cands = []
    posted = S.post_predictions(cands, "gh-scout", cap=5)
    print(json.dumps({"scout": "gh-scout", "posted": len(posted)}))
