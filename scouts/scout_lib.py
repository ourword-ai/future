#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Future scout — shared library.

First-party scouts that seed the commons with REAL, verifiable, dated findings.
Each scout builds candidate findings from a live public source, dedups against the
existing corpus using the SAME barter engine, opens a real `finding` issue, and lets
the engine pay it back + record it. Fault-tolerant by design: any single failure is
skipped, never aborts the run.
"""
from __future__ import annotations
import os, sys, time, json, re, subprocess as sp, urllib.request

# import the barter engine from repo root
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.getcwd())
import barter_engine as engine  # noqa: E402

MIN_NOVELTY = 0.30   # skip candidates too similar to something already in the commons
DRY = os.environ.get("SCOUT_DRY") == "1"

DOMAIN_KW = [
    ("edge-ai",     ["on-device", "on device", "edge", "local-first", "local model", "offline",
                     "quantiz", "ggml", "llama.cpp", "raspberry", "esp32", "gguf", "webgpu"]),
    ("agent-infra", ["agent", "mcp", "orchestrat", "tool-use", "tool use", "workflow", "harness",
                     "sdk", "framework", "runtime", "autonomous", "multi-agent"]),
    ("consumer-ai", ["app", "chat", "voice", "image", "video", "photo", "note", "browser",
                     "assistant", "editor", "desktop"]),
    ("research",    ["benchmark", "dataset", "paper", "arxiv", "sota", "fine-tun", "distill",
                     "diffusion", "transformer", "reasoning"]),
]

def has_kw(text: str, kws) -> bool:
    """Word-boundary keyword match (avoids 'ai' matching 'plain', 'app' matching 'mapped')."""
    t = (text or "").lower()
    return any(re.search(r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])", t) for k in kws)

def infer_domain(text: str, default="other") -> str:
    for dom, kws in DOMAIN_KW:
        if has_kw(text, kws):
            return dom
    return default

def http_get(url, headers=None, retries=3, timeout=30):
    h = {"User-Agent": "future-scout/1.0 (+https://github.com/ourword-ai/future)"}
    if headers: h.update(headers)
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            last = e; time.sleep(3 * (i + 1))
    raise last

def finding_to_body(f: dict) -> str:
    ev = "\n".join(f.get("evidence", []) or [])
    return (
        f"### Claim\n\n{f['claim']}\n\n"
        f"### Evidence\n\n{ev}\n\n"
        f"### Method\n\n{f.get('method','')}\n\n"
        f"### Domain\n\n{f.get('domain','other')}\n\n"
        f"### Confidence\n\n{f.get('confidence',0.6)}\n\n"
        f"### Model\n\n{f.get('model','future-scout')}\n\n"
        f"### Operator (optional handle)\n\n{f.get('operator','@ourword-ai')}\n"
    )

def _gh_create(title, body):
    p = sp.run(["gh", "issue", "create", "--title", title, "--label", "finding", "--body", body],
               capture_output=True, text=True)
    if p.returncode != 0:
        print(f"[gh create fail] {p.stderr.strip()[-300:]}", file=sys.stderr)
        return None
    return p.stdout.strip().splitlines()[-1].strip()

def _gh_comment(number):
    sp.run(["gh", "issue", "comment", str(number), "--body-file", "comment.md"],
           capture_output=True, text=True)

DOMAIN_LABEL = {
    "agent-infra": "Agent infrastructure", "edge-ai": "On-device / edge AI",
    "consumer-ai": "Consumer AI apps", "research": "Fresh research",
    "pain-points": "Pain points", "health": "Health", "other": "Other signals",
}

def rebuild_clusters():
    """Honest 'what agents are noticing': a theme only shows when >=2 DIFFERENT scouts
    independently land in the same domain this cycle (real convergence, never faked)."""
    path = "findings/feed.json"
    if not os.path.exists(path):
        return
    feed = json.load(open(path, encoding="utf-8"))
    finds = feed.get("findings", [])
    by_dom = {}
    for f in finds:
        by_dom.setdefault(f.get("domain", "other"), []).append(f)
    clusters = []
    for dom, items in sorted(by_dom.items(), key=lambda kv: -len(kv[1])):
        agents = sorted({i.get("agent") for i in items if i.get("agent")})
        if len(items) < 2 or len(agents) < 2:
            continue  # not convergence — a single source doesn't count
        clusters.append({
            "name": DOMAIN_LABEL.get(dom, dom),
            "desc": f"{len(agents)} independent scouts both surfaced {dom} signals this cycle.",
            "n": len(agents),
            "members": [i["id"] for i in items][:8],
        })
    feed["clusters"] = clusters
    json.dump(feed, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def refresh():
    """Rebuild feed.json AND clusters — used by the workflow commit step so the
    conflict-safe feed regeneration never drops the convergence view."""
    engine.rebuild_feed("findings")
    rebuild_clusters()

def emit(candidates, scout, cap=3):
    """Dedup, open a real finding issue, let the engine pay + record it. Returns posted list."""
    corpus = engine.load_corpus("findings")
    posted = []
    for f in candidates:
        if len(posted) >= cap:
            break
        try:
            if not f.get("claim") or len(f["claim"]) < 12:
                continue
            _, nov, _ = engine.rank(f, corpus)
            if corpus and nov < MIN_NOVELTY:
                continue  # already known to the commons
            body = finding_to_body(f)
            title = "finding: " + f["claim"][:60].strip()
            url = None
            if DRY:
                number = 90000 + len(posted)
                print(f"  DRY would post: {title}")
            else:
                url = _gh_create(title, body)
                number = int(url.rstrip("/").split("/")[-1]) if url else int(time.time())
            res = engine.run(body, number, scout, findings_dir="findings")
            if res.get("ok"):
                with open("comment.md", "w", encoding="utf-8") as fh:
                    fh.write(res["comment"])
                if url:
                    _gh_comment(number)
                corpus = engine.load_corpus("findings")   # include what we just posted
                posted.append((scout, f["claim"], url or f"(dry {number})"))
                print(f"  ✓ posted [{scout}] {f['claim'][:70]}")
        except Exception as e:
            print(f"  [skip one] {e!r}", file=sys.stderr)
            continue
    try:
        rebuild_clusters()
    except Exception as e:
        print(f"  [clusters skip] {e!r}", file=sys.stderr)
    return posted
