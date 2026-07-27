#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""arxiv-scout — fresh, builder-relevant AI research (cs.AI/LG/CL, last submissions)."""
import json
import xml.etree.ElementTree as ET
import scout_lib as S

SIGNAL = ["agent", "llm", "language model", "on-device", "on device", "edge", "inference",
          "efficient", "retrieval", "rag", "multimodal", "reasoning", "code generation",
          "fine-tun", "distill", "quantiz", "diffusion", "robot", "tool-use", "tool use",
          "planning", "memory", "long-context", "long context"]

def build():
    url = ("https://export.arxiv.org/api/query?search_query="
           "cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL"
           "&sortBy=submittedDate&sortOrder=descending&max_results=50")
    xml = S.http_get(url, retries=5)   # arxiv rate-limits cloud IPs; back off harder
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml)
    out = []
    for e in root.findall("a:entry", ns):
        title = " ".join((e.findtext("a:title", "", ns) or "").split())
        summ = " ".join((e.findtext("a:summary", "", ns) or "").split())
        link = (e.findtext("a:id", "", ns) or "").strip()
        pub = (e.findtext("a:published", "", ns) or "")[:10]
        cat_el = e.find("a:category", ns)
        cat = cat_el.get("term") if cat_el is not None else "cs.AI"
        blob = (title + " " + summ).lower()
        if not title or not link:
            continue
        if not any(k in blob for k in SIGNAL):
            continue  # keep only builder-relevant papers
        # one-line "why": first sentence of abstract, trimmed
        why = summ.split(". ")[0][:150]
        out.append({
            "claim": f"New arXiv ({cat}): {title[:130]}",
            "evidence": [link, f"submitted: {pub}", f"category: {cat}"],
            "method": "arxiv_api cat:cs.AI/LG/CL sortBy=submittedDate",
            "domain": "research",
            "confidence": 0.5,
            "model": "future-scout/arxiv",
            "operator": "@ourword-ai",
            "tags": ["arxiv", cat, "why:" + why[:60]],
        })
    return out

if __name__ == "__main__":
    try:
        cands = build()
    except Exception as e:
        print(f"[arxiv-scout] source unavailable, skipping: {e!r}"); cands = []
    posted = S.emit(cands, "arxiv-scout", cap=2)
    print(json.dumps({"scout": "arxiv-scout", "posted": len(posted)}))
