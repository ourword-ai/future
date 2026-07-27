#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gh-scout — discovers repos and judges them as POSSIBLE STARTUPS.
Two-pass: cheap prefilter (stars/forks/velocity, kill-gates, drop vendor-owned) →
enrich the survivors with the signals that really say "people use & build on this"
(fork ratio, contributors, recent commits, npm/pypi downloads) → keep only ideas that
could plausibly become a startup worth doing, with clear copy. Every enrichment call is
best-effort; a failure never breaks the run."""
import os, re, json, datetime, urllib.parse, urllib.request, urllib.error
import scout_lib as S

KILL_KW = ["linkedin", "instagram", "tiktok bot", "twitter bot", "auto-dm", "mass dm",
           "follower bot", "engagement bot",
           "jailbreak", "torrent", "piracy", "warez", "nsfw", "crack ", "keygen"]  # junk / legal risk
BIG_VENDORS = {"google", "google-research", "google-deepmind", "openai", "microsoft", "meta",
               "facebook", "facebookresearch", "baidu", "xai-org", "alibaba", "alibaba-inc",
               "bytedance", "tencent", "nvidia", "apple", "amazon", "aws", "anthropics",
               "deepseek-ai", "moonshotai", "qwenlm", "x-ai",
               # funded companies — their repos are their product, not an opening for a new founder
               "vercel", "vercel-labs", "cloudflare", "supabase", "hashicorp", "netlify",
               "stripe", "shopify", "langchain-ai", "run-llama", "llama-index", "huggingface",
               "replicate", "modal-labs", "langgenius", "elastic", "grafana",
               "xiaomimimo", "xiaomi", "mistralai", "cohere", "cohereai", "databricks",
               "mozilla", "huawei", "intel", "ibm", "salesforce", "snowflakedb"}
TOOL_KW = ["cli", "sdk", "api", "framework", "library", "tool", "runtime", "engine", "mcp",
           "self-host", "self host", "open-source", "open source", "app", "editor"]
HEAVY_KW = ["enterprise", "at scale", "kubernetes operator", "data center", "datacenter",
            "gpu cluster", "foundation model training"]
VALUE = {  # 商业价值 — the commercial angle
    "agent-infra": "infra every AI product needs — monetizes as a usage-based API + a hosted/managed tier",
    "consumer-ai": "a finished workflow prosumers pay a monthly seat for, with a team upsell",
    "edge-ai": "on-device kills cloud cost and unlocks privacy-regulated buyers who pay a premium",
    "research": "first to productize the method captures the teams who can't reproduce it themselves",
    "pain-points": "people already spend time/tools on this — a product turns that into subscription revenue"}

def _get(url, hdr=None, timeout=15):
    req = urllib.request.Request(url, headers=hdr or {"User-Agent": "future-scout"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), dict(r.headers)

def _count_via_link(url, hdr):
    """Total items of a paginated endpoint via the Link rel=last page (per_page=1)."""
    try:
        u = url + ("&" if "?" in url else "?") + "per_page=1"
        body, headers = _get(u, hdr)
        link = headers.get("Link") or headers.get("link") or ""
        m = re.search(r'[?&]page=(\d+)>;\s*rel="last"', link)
        if m:
            return int(m.group(1))
        return len(json.loads(body))
    except Exception:
        return 0

def enrich(full, hdr):
    contribs = _count_via_link(f"https://api.github.com/repos/{full}/contributors?anon=true", hdr)
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    commits30 = _count_via_link(f"https://api.github.com/repos/{full}/commits?since={since}", hdr)
    return contribs, commits30, _npm_downloads_verified(full)

def _npm_downloads_verified(full):
    """npm weekly downloads, but ONLY if the package's repository points back to THIS repo
    (kills false name-collision matches like the generic 'eve' package)."""
    name = full.split("/")[-1]
    try:
        meta, _ = _get(f"https://registry.npmjs.org/{urllib.parse.quote(name)}", timeout=8)
        repo = json.loads(meta).get("repository") or {}
        repourl = (repo.get("url") if isinstance(repo, dict) else str(repo)) or ""
        if full.lower() not in repourl.lower():
            return None                       # different package with the same name — ignore
        b, _ = _get(f"https://api.npmjs.org/downloads/point/last-week/{name}", timeout=8)
        n = json.loads(b).get("downloads")
        return ("npm", n) if n else None
    except Exception:
        return None

def judge(name, desc, topics, stars, age, vel, forks, contribs, commits30, dl, dom):
    text = f"{name} {desc} {' '.join(topics)}".lower()
    if any(k in text for k in KILL_KW):
        return None
    fork_ratio = forks / max(stars, 1)
    forks_used = forks >= 250 or (forks >= 60 and fork_ratio >= 0.10)
    installed = bool(dl and dl[1] >= 2000)
    maintained = contribs >= 12 or commits30 >= 40
    some_maint = contribs >= 4 or commits30 >= 10
    sc = {
        "pull":    2 if (stars >= 4000 or installed or forks >= 500) else (1 if (stars >= 700 or forks_used or forks >= 80) else 0),
        "buyer":   2 if dom in ("agent-infra", "consumer-ai", "edge-ai", "pain-points") else 1,
        "wedge":   2 if any(k in text for k in TOOL_KW) else 1,
        "build":   0 if any(k in text for k in HEAVY_KW) else 2,
        "durable": 2 if (vel >= 600 and maintained) else (1 if (vel >= 120 or some_maint) else 0),
    }
    total = sum(sc.values())
    r = []
    if dl and dl[1] >= 300:
        r.append(f"{dl[1]:,}/wk downloads on {dl[0]} — really installed, not just starred")
    if sc["pull"] == 2 and not installed:
        r.append(f"real usage ({stars:,}★ in {age}d)")
    elif sc["pull"] == 1:
        r.append(f"early traction ({stars:,}★)")
    if forks_used:
        r.append(f"{forks:,} forks ({int(fork_ratio*100)}% of stars) — people build on it")
    if maintained:
        r.append(f"{contribs} contributors, {commits30} commits/30d — actively maintained")
    elif sc["durable"] == 2:
        r.append(f"strong momentum (~{int(vel)}★/day)")
    why = "; ".join(r) or f"{stars:,}★, {forks:,} forks, ~{int(vel)}★/day"
    return total, why, VALUE.get(dom, "a clear paid wedge if it owns one workflow end-to-end"), \
        "could be a feature, not a company — check the moat and whether the incumbent just absorbs it"

def build():
    today = datetime.date.today()
    since = (today - datetime.timedelta(days=90)).isoformat()
    q = urllib.parse.quote(f"created:>{since} stars:>120")
    url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page=100"
    hdr = {"Accept": "application/vnd.github+json"}
    tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if tok:
        hdr["Authorization"] = f"Bearer {tok}"
    data = json.loads(S.http_get(url, hdr))
    # pass 1 — cheap prefilter
    pre = []
    for it in data.get("items", []):
        desc = (it.get("description") or "").strip()
        stars = it.get("stargazers_count", 0)
        forks = it.get("forks_count", 0)
        if not desc or it["full_name"].split("/")[0].lower() in BIG_VENDORS:
            continue
        try:
            age = max(1, (today - datetime.date.fromisoformat(it["created_at"][:10])).days)
        except Exception:
            continue
        vel = stars / age
        if vel < 15:
            continue
        it["_age"], it["_vel"], it["_forks"] = age, vel, forks
        pre.append((stars + forks * 3, it))          # forks weighted in the prelim rank
    pre.sort(key=lambda x: x[0], reverse=True)
    # pass 2 — enrich only the top survivors, then judge
    out = []
    for _, it in pre[:30]:
        stars = it.get("stargazers_count", 0)
        topics = it.get("topics", []) or []
        dom = S.infer_domain(f"{it['full_name']} {(it.get('description') or '')} {' '.join(topics)}", "agent-infra")
        try:
            contribs, commits30, dl = enrich(it["full_name"], hdr)
        except Exception:
            contribs, commits30, dl = 0, 0, None
        j = judge(it["full_name"], it.get("description") or "", topics, stars, it["_age"], it["_vel"],
                  it["_forks"], contribs, commits30, dl, dom)
        if not j:
            continue
        total, why, value, risk = j
        if total < 7:
            continue
        ev = [it["html_url"], f"{stars:,}★", f"{it['_forks']:,} forks"]
        if contribs:
            ev.append(f"{contribs} contributors")
        if commits30:
            ev.append(f"{commits30} commits/30d")
        if dl:
            ev.append(f"{dl[1]:,}/wk on {dl[0]}")
        ev.append(f"created {it['created_at'][:10]}")
        out.append({"_score": total, "title": it["full_name"],
                    "claim": f"{it['full_name']} — {(it.get('description') or '')[:120]}",
                    "score": total, "why_good": why, "value": value, "risk": risk,
                    "evidence": ev, "method": "discovery + usage signals (forks/contributors/commits/downloads)",
                    "domain": dom, "model": "future-scout/github", "operator": "@ourword-ai",
                    "tags": (topics[:5] or [])})
    out.sort(key=lambda f: f["_score"], reverse=True)
    for f in out:
        f.pop("_score", None)
    return out

if __name__ == "__main__":
    try:
        cands = build()
    except Exception as e:
        print(f"[gh-scout] source unavailable, skipping: {e!r}"); cands = []
    posted = S.post_ideas(cands, "gh-scout", cap=12)
    print(json.dumps({"scout": "gh-scout", "posted": len(posted)}))
