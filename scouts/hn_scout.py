#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hn-scout — what builders are shipping (Show HN, last 48h, by traction)."""
import json, time, re
import scout_lib as S

# keep builder / AI / dev-tool launches; drop viral human-interest noise
KEEP = ["ai", "llm", "agent", "gpt", "model", " ml ", "open source", "open-source", "self-host",
        "selfhost", "cli", "api", "sdk", "database", "kubernetes", "linux", "rust", "python",
        "compiler", "framework", "local-first", "privacy", "terminal", "tool", "developer",
        "code", "coding", "browser", "server", "parser", "inference", "embedding", "vector",
        "search engine", "security", "encrypt", "open-source", "protocol", "runtime", "wasm"]

def _relevant(title, url):
    b = title + " " + (url or "")
    return ("github.com" in (url or "")) or S.has_kw(b, KEEP) or S.infer_domain(title) != "other"

def build():
    since = int(time.time()) - 48 * 3600
    url = ("https://hn.algolia.com/api/v1/search?tags=show_hn"
           f"&numericFilters=created_at_i>{since},points>50&hitsPerPage=30")
    data = json.loads(S.http_get(url))
    hits = sorted(data.get("hits", []), key=lambda h: h.get("points", 0), reverse=True)
    out = []
    for h in hits:
        title = (h.get("title") or "").strip()
        title = re.sub(r"^\s*show\s*hn:\s*", "", title, flags=re.I).strip()  # de-dupe prefix
        ext = h.get("url")
        if not title or not ext:
            continue
        if not _relevant(title, ext):
            continue
        pts = h.get("points", 0); nc = h.get("num_comments", 0)
        item = f"https://news.ycombinator.com/item?id={h.get('objectID')}"
        out.append({
            "claim": f"Show HN: {title} — {pts} points / {nc} comments in <48h",
            "evidence": [ext, item, f"points: {pts}", f"comments: {nc}"],
            "method": "hn_algolia tags=show_hn points>50 window=48h",
            "domain": S.infer_domain(title, "consumer-ai"),
            "confidence": round(min(0.9, 0.5 + pts / 800), 2),
            "model": "future-scout/hn",
            "operator": "@ourword-ai",
            "tags": ["show-hn"],
        })
    return out

if __name__ == "__main__":
    try:
        cands = build()
    except Exception as e:
        print(f"[hn-scout] source unavailable, skipping: {e!r}"); cands = []
    posted = S.emit(cands, "hn-scout", cap=3)
    print(json.dumps({"scout": "hn-scout", "posted": len(posted)}))
