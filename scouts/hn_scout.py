#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hn-scout — Show HN launches judged as POSSIBLE STARTUPS.
A Show HN with real traction = a launched product people showed up for — high
startup-idea density. Same idea model as gh-scout (what / why-good / commercial value /
risk), no predictions."""
import json, time, re
import scout_lib as S

KEEP = ["ai", "llm", "agent", "gpt", "model", "open source", "open-source", "self-host",
        "selfhost", "cli", "api", "sdk", "database", "kubernetes", "linux", "rust", "python",
        "compiler", "framework", "local-first", "privacy", "terminal", "tool", "developer",
        "code", "coding", "browser", "server", "parser", "inference", "embedding", "vector",
        "search", "security", "encrypt", "protocol", "runtime", "wasm", "editor", "app",
        "automation", "workflow", "analytics", "payments", "saas", "notes", "email"]
KILL = ["jailbreak", "torrent", "piracy", "warez", "nsfw", "keygen"]
VENDOR = ["microsoft", "google", "apple", "mozilla", "firefox", "meta", "amazon", "baidu",
          "alibaba", "tencent", "xiaomi", "huawei", "openai", "nvidia", "intel", "ibm"]
VALUE = {"agent-infra": "infra AI products need — usage-based API + hosted tier",
         "consumer-ai": "a workflow people pay a monthly seat for",
         "edge-ai": "on-device kills cloud cost + unlocks privacy buyers",
         "research": "productize the method for teams who can't build it",
         "pain-points": "turn a manual workaround into subscription revenue",
         "other": "a paid wedge if it owns one workflow end-to-end"}

def build():
    since = int(time.time()) - 30 * 24 * 3600
    url = ("https://hn.algolia.com/api/v1/search?tags=show_hn"
           f"&numericFilters=created_at_i>{since},points>50&hitsPerPage=60")
    hits = json.loads(S.http_get(url)).get("hits", [])
    hits.sort(key=lambda h: h.get("points", 0), reverse=True)
    out = []
    for h in hits:
        title = re.sub(r"^\s*show\s*hn:\s*", "", (h.get("title") or ""), flags=re.I).strip()
        ext = h.get("url")
        if not title or not ext:
            continue
        blob = (title + " " + ext).lower()
        if any(k in blob for k in KILL) or S.has_kw(blob, VENDOR):
            continue
        if not ("github.com" in ext or S.has_kw(blob, KEEP) or S.infer_domain(title) != "other"):
            continue
        pts = h.get("points", 0); nc = h.get("num_comments", 0)
        dom = S.infer_domain(title, "consumer-ai")
        score = (2 if pts >= 250 else 1 if pts >= 90 else 0) \
            + (2 if dom in ("agent-infra", "consumer-ai", "edge-ai", "pain-points") else 1) \
            + (2 if S.has_kw(blob, ["cli", "sdk", "api", "framework", "library", "tool", "self-host", "open source", "open-source"]) else 1) \
            + 2 \
            + (2 if nc >= 60 else 1 if nc >= 15 else 0)
        if score < 7:
            continue
        out.append({
            "_score": score, "title": title,
            "claim": f"Show HN: {title}",
            "score": score,
            "why_good": f"Launched on Show HN with real interest — {pts} points / {nc} comments. People turned up for it, which is rare.",
            "value": VALUE.get(dom, VALUE["other"]),
            "risk": "Show HN spikes fade — check whether anyone still uses it a month after launch day.",
            "evidence": [ext, f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                         f"{pts} HN points", f"{nc} comments"],
            "method": "hn show_hn (last 30d) + startup-worthiness score",
            "domain": dom, "model": "future-scout/hn", "operator": "@ourword-ai", "tags": ["show-hn"]})
    out.sort(key=lambda f: f["_score"], reverse=True)
    for f in out:
        f.pop("_score", None)
    return out

if __name__ == "__main__":
    try:
        cands = build()
    except Exception as e:
        print(f"[hn-scout] source unavailable, skipping: {e!r}"); cands = []
    posted = S.post_ideas(cands, "hn-scout", cap=8)
    print(json.dumps({"scout": "hn-scout", "posted": len(posted)}))
