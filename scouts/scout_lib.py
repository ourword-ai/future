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

def _gh_create(title, body, label="finding"):
    try:
        p = sp.run(["gh", "issue", "create", "--title", title, "--label", label, "--body", body],
                   capture_output=True, text=True)
    except FileNotFoundError:
        return None                       # no gh CLI (e.g. backfill) — finding still gets written
    if p.returncode != 0:
        print(f"[gh create fail] {p.stderr.strip()[-300:]}", file=sys.stderr)
        return None
    return p.stdout.strip().splitlines()[-1].strip()

def _gh_headers():
    h = {"Accept": "application/vnd.github+json", "User-Agent": "future-scout/1.0"}
    tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h

def metric_value(pred):
    """Fetch the current real value of a prediction's metric (the verification oracle)."""
    m = pred.get("metric")
    if m == "github_stars":
        d = json.loads(http_get(f"https://api.github.com/repos/{pred['target_id']}", _gh_headers()))
        return d.get("stargazers_count")
    return None  # unknown metric -> resolver skips (stays pending)

def _agent_accuracy(findings, agent):
    res = [f for f in findings if f.get("agent") == agent and f.get("status") in ("hit", "miss")]
    hits = sum(1 for f in res if f.get("status") == "hit")
    return hits, len(res)

def prediction_body(f):
    p = f.get("prediction") or {}
    ev = "\n".join(f.get("evidence", []) or [])
    return (
        f"### Claim\n\n{f['claim']}\n\n"
        f"### Prediction (auto-resolved)\n\n"
        f"- metric: `{p.get('metric')}`\n- subject: `{p.get('target_id')}`\n"
        f"- resolves: **{p.get('target_id')} {p.get('op')} {p.get('target')}** on **{p.get('resolve_on')}**\n\n"
        f"### Evidence\n\n{ev}\n\n"
        f"### Method\n\n{f.get('method','')}\n\n"
        f"### Domain\n\n{f.get('domain','other')}\n\n"
        f"### Operator\n\n{f.get('operator','@ourword-ai')}\n"
    )

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

def rebuild_scoreboard():
    """Board summary for the Idea list: how many ideas, across how many domains &
    sources, and the average startup-worthiness score."""
    path = "findings/feed.json"
    if not os.path.exists(path):
        return
    feed = json.load(open(path, encoding="utf-8"))
    fs = feed.get("findings", [])
    from collections import Counter
    per = Counter(f.get("agent") for f in fs if f.get("agent"))
    scores = [f.get("score") for f in fs if isinstance(f.get("score"), (int, float))]
    feed["scoreboard"] = [{"agent": a, "ideas": n} for a, n in per.most_common()]
    feed["board"] = {"ideas": len(fs),
                     "domains": len({f.get("domain") for f in fs if f.get("domain")}),
                     "sources": len(per),
                     "avg_score": round(sum(scores) / len(scores), 1) if scores else 0}
    json.dump(feed, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def idea_body(f):
    ev = "\n".join(f.get("evidence", []) or [])
    return (f"### What\n\n{f['claim']}\n\n"
            f"### Why it's good\n\n{f.get('why_good','')}\n\n"
            f"### Commercial value\n\n{f.get('value','')}\n\n"
            f"### Risk\n\n{f.get('risk','')}\n\n"
            f"### Startup-worthiness\n\n{f.get('score','')}/10\n\n"
            f"### Evidence\n\n{ev}\n")

def llm_copy(f):
    """Sharp, specific, BILINGUAL (EN + 中文) card copy in ONE GitHub Models call.
    Bans generic filler; forces project-specific why/value/risk. Returns EN fields plus
    f['i18n']['zh']; returns None on failure so the caller keeps the heuristic copy."""
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not tok:
        return None
    model = os.environ.get("GH_MODELS_MODEL", "openai/gpt-4o-mini")
    ev = ", ".join(f.get("evidence", []) or [])
    prompt = (
        "You curate a public board of GitHub / Show HN projects that could become real startups. "
        "Write SHARP, SPECIFIC copy about THIS project. Never generic.\n"
        "BANNED phrases (never output any): 'could pay for premium features', 'subscription model', "
        "'a bigger player could integrate', 'could easily integrate', 'could be absorbed', "
        "'the market is competitive', 'leverages ... technology', 'streamline workflows', "
        "'premium features or support'. If you are about to write one, replace it with the concrete, "
        "project-specific point: name the exact buyer, the exact wedge, the exact incumbent, or the "
        "exact weakness.\n"
        "BAR to match (why_good): \"Attacks the #1 complaint about coding agents - overengineered "
        "slop - and the pull is real: ~90k stars in six weeks.\"\n\n"
        "Reply with ONLY a JSON object; each English value is ONE tight, concrete sentence:\n"
        "  hook: a punchy, scroll-stopping one-line headline — a COMPLETE but concise sentence that makes someone want to click; you may fold in the standout number (e.g. stars). Not hype, not a fragment.\n"
        "  why_good: the non-obvious, project-specific reason this could be a real startup.\n"
        "  value: who EXACTLY pays and for what specific outcome (name the buyer and the wedge).\n"
        "  risk: the concrete, specific reason it might fail (name the incumbent or exact weakness).\n"
        "  claim_zh: 中文翻译 of the one-line description (keep repo/product names in latin).\n"
        "  hook_zh: faithful 中文 translation of the hook.\n"
        "  why_good_zh, value_zh, risk_zh: faithful 中文 translations of the three English lines.\n\n"
        f"Project: {f.get('title','')} — {f.get('claim','')}\n"
        f"Signals: {ev}\nDomain: {f.get('domain','')}\n\nJSON only.")
    body = json.dumps({"model": model, "temperature": 0.5, "max_tokens": 650,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    try:
        req = urllib.request.Request("https://models.github.ai/inference/chat/completions", data=body,
              headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json",
                       "User-Agent": "future-scout"})
        with urllib.request.urlopen(req, timeout=40) as r:
            txt = json.loads(r.read())["choices"][0]["message"]["content"]
        m = re.search(r"\{.*\}", txt, re.S)
        obj = json.loads(m.group(0))
        if all(obj.get(k) for k in ("why_good", "value", "risk")):
            out = {k: str(obj[k]).strip()[:400] for k in ("why_good", "value", "risk")}
            if obj.get("hook"):
                out["hook"] = str(obj["hook"]).strip()[:200]
            zh = {}
            for src, dst in (("claim_zh", "claim"), ("hook_zh", "hook"), ("why_good_zh", "why_good"),
                             ("value_zh", "value"), ("risk_zh", "risk")):
                if obj.get(src):
                    zh[dst] = str(obj[src]).strip()[:400]
            if zh:
                out["i18n"] = {"zh": zh}
            return out
    except Exception as e:
        print(f"  [llm_copy fallback -> heuristic: {e!r}]", file=sys.stderr)
    return None
def editor_pick(f):
    """Strict editorial gate: is this genuinely a buildable, monetizable startup a small
    founder could start NOW? Via GitHub Models (free in Actions w/ models:read). Returns
    (True/False, reason) or (None, None) if the model is unavailable -> caller leaves it unset."""
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not tok:
        return None, None
    model = os.environ.get("GH_MODELS_MODEL", "openai/gpt-4o-mini")
    ev = ", ".join(f.get("evidence", []) or [])
    prompt = (
        "You are a hard-nosed startup scout. Decide if the project below is something a small "
        "founder could realistically turn into a real, monetizable startup RIGHT NOW.\n"
        "Answer FALSE if it is any of: a skills/prompt/awesome/content collection or list; a course, "
        "book, or newsletter; a demo/toy/joke; an already-huge or famous project or a big company's "
        "product (no opening left); or too vague to be a business.\n"
        "Answer TRUE only if there is a clear product a team could build and charge money for.\n\n"
        f"Project: {f.get('title','')} - {f.get('claim','')}\n"
        f"Why: {f.get('why_good','')}\nSignals: {ev}\nDomain: {f.get('domain','')}\n\n"
        "Reply with ONLY JSON: {\"pick\": true|false, \"reason\": \"one short sentence\"}")
    body = json.dumps({"model": model, "temperature": 0, "max_tokens": 120,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    try:
        req = urllib.request.Request("https://models.github.ai/inference/chat/completions", data=body,
              headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json",
                       "User-Agent": "future-scout"})
        with urllib.request.urlopen(req, timeout=30) as r:
            txt = json.loads(r.read())["choices"][0]["message"]["content"]
        m = re.search(r"\{.*\}", txt, re.S)
        obj = json.loads(m.group(0))
        return bool(obj.get("pick")), str(obj.get("reason", ""))[:200]
    except Exception as e:
        print(f"  [editor_pick skip: {e!r}]", file=sys.stderr)
        return None, None

def post_ideas(cands, scout, cap=6):
    """Write vetted startup-worthy ideas to the board (no predictions). Dedup by repo."""
    corpus = engine.load_corpus("findings")
    have = {(f.get("title") or (f.get("evidence") or [""])[0]) for f in corpus}
    posted = []
    for f in cands:
        if len(posted) >= cap:
            break
        try:
            key = f.get("title") or (f.get("evidence") or [""])[0]
            if key in have:
                continue
            body = idea_body(f)
            title = "idea: " + (f.get("title") or f["claim"][:50])
            url = None
            if DRY:
                number = 90000 + len(posted); print(f"  DRY idea: {f['claim'][:70]}")
            else:
                url = _gh_create(title, body, label="idea")
                number = int(url.rstrip("/").split("/")[-1]) if url else int(time.time())
            import datetime as _dt
            fid = f"{number}-{engine.slugify(f.get('title') or f['claim'])}"
            rec = dict(f)
            rec.update({"id": fid, "agent": scout,
                        "posted_at": _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"})
            if (rec.get("score") or 0) >= 9:   # ration free LLM quota to the top tier only
                c = llm_copy(rec)                # sharp bilingual EN/中文
                if c:
                    rec.update(c)
                pk, why = editor_pick(rec)
                if pk is not None:
                    rec["pick"] = pk
                    if why:
                        rec["pick_reason"] = why
            os.makedirs("findings", exist_ok=True)
            json.dump(rec, open(f"findings/{fid}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            if url and not DRY:
                with open("comment.md", "w", encoding="utf-8") as fh:
                    fh.write(f"💡 added to the Idea board: **{f.get('title','')}** — {f.get('why_good','')[:160]}")
                _gh_comment(number)
            have.add(key)
            posted.append((scout, f.get("title"), url or f"(dry {number})"))
            print(f"  ✓ idea [{scout}] {f.get('title')}")
        except Exception as e:
            print(f"  [skip one] {e!r}", file=sys.stderr)
            continue
    return posted

def post_predictions(cands, scout, cap=3):
    """Log falsifiable predictions as findings (status=pending) + open a public issue.
    No barter/similarity — value comes later when the resolver grades them."""
    corpus = engine.load_corpus("findings")
    open_targets = {(f.get("prediction") or {}).get("target_id")
                    for f in corpus if f.get("status") == "pending"}
    posted = []
    for f in cands:
        if len(posted) >= cap:
            break
        try:
            pred = f.get("prediction") or {}
            if not pred.get("target_id") or pred["target_id"] in open_targets:
                continue  # already an open call on this subject
            body = prediction_body(f)
            title = "prediction: " + f["claim"][:64].strip()
            url = None
            if DRY:
                number = 90000 + len(posted); print(f"  DRY predict: {f['claim'][:72]}")
            else:
                url = _gh_create(title, body, label="prediction")
                number = int(url.rstrip("/").split("/")[-1]) if url else int(time.time())
            import datetime as _dt
            fid = f"{number}-{engine.slugify(f['claim'])}"
            rec = dict(f)
            rec.update({"id": fid, "agent": scout,
                        "posted_at": _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
                        "status": "pending", "observed": None, "resolved_at": None})
            os.makedirs("findings", exist_ok=True)
            json.dump(rec, open(f"findings/{fid}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            if url and not DRY:
                hits, tot = _agent_accuracy(corpus, scout)
                acc = f"{round(100*hits/tot)}% ({hits}/{tot})" if tot else "no track record yet — this is how it starts"
                with open("comment.md", "w", encoding="utf-8") as fh:
                    fh.write(f"⏳ **prediction logged** — auto-resolves **{pred.get('resolve_on')}** by re-checking "
                             f"`{pred.get('metric')} {pred.get('op')} {pred.get('target')}`.\n\n_{scout} track record: {acc}._")
                _gh_comment(number)
            open_targets.add(pred["target_id"])
            posted.append((scout, f["claim"], url or f"(dry {number})"))
            print(f"  ✓ predicted [{scout}] {f['claim'][:70]}")
        except Exception as e:
            print(f"  [skip one] {e!r}", file=sys.stderr)
            continue
    return posted

def refresh():
    """Rebuild feed.json + clusters + scoreboard — used by workflow commit steps and the
    resolver so the conflict-safe feed regeneration never drops derived views."""
    engine.rebuild_feed("findings")
    rebuild_clusters()
    rebuild_scoreboard()

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
