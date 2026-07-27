#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""askhn-scout — Ask HN threads mined as UNMET NEEDS worth building.

A high-engagement "Ask HN: is there a tool for X / how do you deal with Y" is a
demand signal: many people surfacing the SAME gap = a warm, pre-qualified audience
for whoever ships the fix. We keep only the tool/workflow-shaped needs (not career /
personal / hiring chatter) and score them for startup-worthiness. Same idea model as
the other scouts (what / why-good / commercial value / risk), no predictions."""
import json, time, re
import scout_lib as S

# the "is there a product for this" shape — a buildable, recurring need
NEED_KW = ["is there a", "are there any", "how do you", "how do i", "what do you use",
           "what's the best", "what is the best", "what's a good", "whats a good", "best way to",
           "tool for", "tools for", "alternative to", "alternatives to", "how to manage",
           "how do people", "anyone found", "anyone know of", "anyone know any", "recommend a",
           "recommendations for", "looking for a", "self-host", "self hosted", "workflow for",
           "automate", "way to track", "where are the", "where is the", "why is there no",
           "why isn't there", "wish there was", "suggest a"]
TOOL_KW = ["tool", "app", "software", "service", "platform", "api", "cli", "dashboard",
           "tracker", "automation", "workflow", "self-host", "self hosted", "saas", "system",
           "search engine", "website", "site", "product", "solution", "alternative"]
SKIP_PREFIX = ("tell hn", "thanks hn", "show hn", "launch hn")
# not a startup: hiring/jobs/personal/opinion threads
KILL = ["who is hiring", "who's hiring", "who wants to be hired", "freelancer? seeking",
        "seeking freelancer", "salary", "get a job", "getting a job", "job search", "laid off",
        "layoff", "interview", "visa", "green card", "relocat", "relationship", "married",
        "divorce", "depress", "anxiety", "therapy", "burnout", "book recommend", "reading list",
        "favorite book", "career advice", "should i quit", "life advice", "roast my",
        "review my resume", "am i", "how much do you make", "what are you working on"]

def build():
    since = int(time.time()) - 90 * 24 * 3600     # 90d — genuine "is there a tool" needs are rare
    url = ("https://hn.algolia.com/api/v1/search?tags=ask_hn"
           f"&numericFilters=created_at_i>{since},points>30&hitsPerPage=100")
    hits = json.loads(S.http_get(url)).get("hits", [])
    out = []
    for h in hits:
        raw = (h.get("title") or "").strip()
        title = re.sub(r"^\s*ask\s*hn:\s*", "", raw, flags=re.I).strip().rstrip("?").strip()
        if not title:
            continue
        low = raw.lower()
        if low.startswith(SKIP_PREFIX) or any(k in low for k in KILL):
            continue
        # must look like a recurring, buildable need — not generic musing/opinion
        if not (any(k in low for k in NEED_KW) and S.has_kw(low, TOOL_KW)):
            continue
        pts = h.get("points", 0); nc = h.get("num_comments", 0)
        # a need is only interesting if a CROWD felt it (comments) with real interest (points)
        if nc < 15:
            continue
        sc = {
            "interest": 2 if pts >= 120 else (1 if pts >= 50 else 0),
            "crowd":    2 if nc >= 80 else (1 if nc >= 20 else 0),
            "shape":    2,   # passed the need-phrase gate above
            "buildable": 2 if S.has_kw(low, TOOL_KW) else 1,
            "real":     2 if (nc >= 20 and pts >= 50) else (1 if pts >= 40 else 0),
        }
        score = sum(sc.values())
        if score < 7:
            continue
        item = f"https://news.ycombinator.com/item?id={h.get('objectID')}"
        out.append({
            "_score": score, "_pts": pts,
            "title": title[:110],
            "claim": f"Unmet need (Ask HN): {title[:150]}",
            "score": score,
            "why_good": (f"{pts} points and {nc} comments on HN — that many people surfacing the "
                         f"same gap is a warm, pre-qualified audience for whoever ships the fix."),
            "value": "turn the manual workaround people describe here into a paid tool or subscription.",
            "risk": ("asking on a forum is not paying — validate willingness to pay before building; "
                     "some of these are niche or already half-solved by an existing tool."),
            "evidence": [item, f"{pts} HN points", f"{nc} comments", "Ask HN (last 30d)"],
            "method": "hn ask_hn (last 30d), tool/workflow-need filter + startup-worthiness score",
            "domain": "pain-points", "model": "future-scout/askhn",
            "operator": "@ourword-ai", "tags": ["ask-hn", "demand-signal"]})
    out.sort(key=lambda f: (f["_score"], f["_pts"]), reverse=True)
    for f in out:
        f.pop("_score", None); f.pop("_pts", None)
    return out

if __name__ == "__main__":
    try:
        cands = build()
    except Exception as e:
        print(f"[askhn-scout] source unavailable, skipping: {e!r}"); cands = []
    posted = S.post_ideas(cands, "askhn-scout", cap=6)
    print(json.dumps({"scout": "askhn-scout", "posted": len(posted)}))
