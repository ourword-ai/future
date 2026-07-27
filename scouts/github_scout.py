#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gh-scout — posts FALSIFIABLE GitHub-star predictions. The resolver auto-grades them."""
import os, json, datetime, urllib.parse
import scout_lib as S

HORIZON_DAYS = 5   # short horizon so predictions resolve quickly in the MVP

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
        try:
            created = datetime.date.fromisoformat(it["created_at"][:10])
            age = max(1, (today - created).days)
        except Exception:
            continue
        vel = stars / age
        if vel < 20:                       # need real momentum for a meaningful call
            continue
        target = stars + int(round(vel * HORIZON_DAYS))   # "will it keep this pace?" — a genuine bet
        if target <= stars:
            continue
        topics = it.get("topics", []) or []
        out.append({
            "_vel": vel,
            "claim": f"{it['full_name']} will hit ≥{target:,}★ by {resolve_on} (now {stars:,}, ~{int(round(vel))}/day)",
            "evidence": [it["html_url"], f"stars_now: {stars}", f"velocity: ~{int(round(vel))}/day",
                         f"created: {it['created_at'][:10]}"],
            "method": f"github star-velocity extrapolation · {HORIZON_DAYS}-day horizon",
            "domain": S.infer_domain(f"{it['full_name']} {desc} {' '.join(topics)}", "agent-infra"),
            "model": "future-scout/github",
            "operator": "@ourword-ai",
            "tags": (topics[:5] or []),
            "prediction": {"metric": "github_stars", "target_id": it["full_name"],
                           "op": ">=", "target": target, "resolve_on": resolve_on},
        })
    out.sort(key=lambda f: f["_vel"], reverse=True)
    for f in out:
        f.pop("_vel", None)
    return out

if __name__ == "__main__":
    try:
        cands = build()
    except Exception as e:
        print(f"[gh-scout] source unavailable, skipping: {e!r}"); cands = []
    posted = S.post_predictions(cands, "gh-scout", cap=3)
    print(json.dumps({"scout": "gh-scout", "posted": len(posted)}))
