#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gh-scout — fast-rising new GitHub repos (real momentum, dated)."""
import os, json, datetime, urllib.parse
import scout_lib as S

def build():
    today = datetime.date.today()
    since = (today - datetime.timedelta(days=14)).isoformat()
    q = urllib.parse.quote(f"created:>{since} stars:>80")
    url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page=40"
    hdr = {"Accept": "application/vnd.github+json"}
    tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if tok:
        hdr["Authorization"] = f"Bearer {tok}"
    data = json.loads(S.http_get(url, hdr))
    out = []
    for it in data.get("items", []):
        desc = (it.get("description") or "").strip()
        if not desc:
            continue
        try:
            created = datetime.date.fromisoformat(it["created_at"][:10])
            age = max(1, (today - created).days)
        except Exception:
            continue
        stars = it.get("stargazers_count", 0)
        vel = round(stars / age, 1)
        topics = it.get("topics", []) or []
        text = f"{it['full_name']} {desc} {' '.join(topics)}"
        out.append({
            "_vel": vel,
            "claim": f"{it['full_name']}: {desc[:120]} — {stars}★ in {age}d (~{vel}/day)",
            "evidence": [it["html_url"], f"stars: {stars}", f"created: {it['created_at'][:10]}",
                         f"star_velocity: ~{vel}/day"],
            "method": f"github_search created:>{since} sort:stars",
            "domain": S.infer_domain(text, "agent-infra"),
            "confidence": round(min(0.95, 0.55 + vel / 2000), 2),
            "model": "future-scout/github",
            "operator": "@ourword-ai",
            "tags": (topics[:6] or []),
        })
    # prioritize by star velocity (real momentum), not raw count
    out.sort(key=lambda f: f["_vel"], reverse=True)
    for f in out:
        f.pop("_vel", None)
    return out

if __name__ == "__main__":
    try:
        cands = build()
    except Exception as e:
        print(f"[gh-scout] source unavailable, skipping: {e!r}"); cands = []
    posted = S.emit(cands, "gh-scout", cap=3)
    print(json.dumps({"scout": "gh-scout", "posted": len(posted)}))
