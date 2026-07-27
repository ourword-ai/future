#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gh-scout — discovers repos and judges them as POSSIBLE STARTUPS.
No star-count guessing. Surfaces only ideas that could plausibly become a startup
worth doing (>=7/10, no kill-gate), each with clear copy: what it is, why it's good,
who'd pay, the wedge, the risk. Heuristic copy is v1; the autopilot (an LLM) rewrites
the copy to real quality."""
import os, json, datetime, urllib.parse
import scout_lib as S

KILL_KW = ["linkedin", "instagram", "tiktok bot", "twitter bot", "auto-dm", "mass dm",
           "follower bot", "engagement bot"]                 # platform-parasite
BIG_VENDORS = {"google", "google-research", "google-deepmind", "openai", "microsoft", "meta",
               "facebook", "facebookresearch", "baidu", "xai-org", "alibaba", "alibaba-inc",
               "bytedance", "tencent", "nvidia", "apple", "amazon", "aws", "anthropics",
               "deepseek-ai", "moonshotai", "qwenlm", "x-ai"}   # vendor-owned = not a startup opening
TOOL_KW = ["cli", "sdk", "api", "framework", "library", "tool", "runtime", "engine",
           "mcp", "self-host", "self host", "open-source", "open source", "app", "editor"]
HEAVY_KW = ["enterprise", "at scale", "kubernetes operator", "data center", "datacenter",
            "gpu cluster", "foundation model training"]
BUYER = {"agent-infra": "developers building agents / AI product teams",
         "consumer-ai": "prosumers & small teams who'd pay for the finished workflow",
         "edge-ai": "privacy-sensitive users & on-device / offline app builders",
         "research": "engineers who need the method as a usable, supported tool",
         "pain-points": "the people already hacking a manual workaround"}
WEDGE = {"agent-infra": 'be the hosted / easy version; own "<x> alternative" search',
         "consumer-ai": "win one vertical the general tool ignores, with better UX",
         "edge-ai": "own the local / offline / privacy angle end-to-end",
         "research": "wrap the research into a paid, reliable product",
         "pain-points": "productize the workaround people already cobble together"}

def judge(name, desc, topics, stars, age, vel, dom):
    text = f"{name} {desc} {' '.join(topics)}".lower()
    if any(k in text for k in KILL_KW):
        return None
    sc = {
        "pull":    2 if stars >= 2000 else (1 if stars >= 500 else 0),      # real usage
        "buyer":   2 if dom in ("agent-infra", "consumer-ai", "edge-ai", "pain-points") else 1,
        "wedge":   2 if any(k in text for k in TOOL_KW) else 1,            # a small team can own an angle
        "build":   0 if any(k in text for k in HEAVY_KW) else 2,           # buildable by a small team
        "durable": 2 if vel >= 300 else (1 if vel >= 80 else 0),           # momentum, not a one-day toy
    }
    total = sum(sc.values())
    reasons = []
    if sc["pull"] == 2: reasons.append(f"already pulling real usage ({stars:,}★ in {age}d)")
    elif sc["pull"] == 1: reasons.append(f"early traction ({stars:,}★)")
    if sc["durable"] == 2: reasons.append(f"strong momentum (~{int(vel)}★/day)")
    if sc["build"] == 2: reasons.append("small team could ship a real version")
    why = "; ".join(reasons) or f"{stars:,}★, ~{int(vel)}★/day and rising"
    return total, why, BUYER.get(dom, "a definable niche willing to pay"), \
        WEDGE.get(dom, "own an underserved niche + comparison-page SEO"), \
        "could be a feature, not a company — check the moat and whether the incumbent just absorbs it"

def build():
    today = datetime.date.today()
    since = (today - datetime.timedelta(days=45)).isoformat()
    q = urllib.parse.quote(f"created:>{since} stars:>150")
    url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page=50"
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
        if it["full_name"].split("/")[0].lower() in BIG_VENDORS:
            continue                                    # vendor-owned = not a startup opening
        try:
            created = datetime.date.fromisoformat(it["created_at"][:10])
            age = max(1, (today - created).days)
        except Exception:
            continue
        vel = stars / age
        if vel < 15:
            continue
        topics = it.get("topics", []) or []
        dom = S.infer_domain(f"{it['full_name']} {desc} {' '.join(topics)}", "agent-infra")
        j = judge(it["full_name"], desc, topics, stars, age, vel, dom)
        if not j:
            continue
        total, why, who, wedge, risk = j
        if total < 7:
            continue
        out.append({
            "_score": total,
            "title": it["full_name"],
            "claim": f"{it['full_name']} — {desc[:120]}",
            "score": total, "why_good": why, "who_pays": who, "wedge": wedge, "risk": risk,
            "evidence": [it["html_url"], f"{stars:,}★", f"~{int(round(vel))}★/day", f"created {it['created_at'][:10]}"],
            "method": "github discovery + startup-worthiness score (heuristic v1)",
            "domain": dom, "model": "future-scout/github", "operator": "@ourword-ai",
            "tags": (topics[:5] or []),
        })
    out.sort(key=lambda f: f["_score"], reverse=True)
    for f in out:
        f.pop("_score", None)
    return out

if __name__ == "__main__":
    try:
        cands = build()
    except Exception as e:
        print(f"[gh-scout] source unavailable, skipping: {e!r}"); cands = []
    posted = S.post_ideas(cands, "gh-scout", cap=6)
    print(json.dumps({"scout": "gh-scout", "posted": len(posted)}))
