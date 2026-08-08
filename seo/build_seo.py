#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SEO/GEO build for the Idea board. Run from the repo root: python seo/build_seo.py"""
import datetime
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geo_kit as G

SITE = G.Site(
    path="idea",
    name="Idea", name_zh="灵感看板",
    tagline="what is actually worth building, with the evidence attached",
    tagline_zh="值得做的东西，以及它凭什么值得做",
    description=(
        "Idea is a hand-operated board of things worth building. Every entry starts from "
        "first-hand evidence that ordinary people — not developers — are in pain: a Reddit "
        "thread, a Xiaohongshu comment section, a GitHub issue where someone offers to pay. "
        "Each one names who would use it, what they get, what is missing today, and what "
        "would kill it. Entries that only serve developers, agents or infrastructure are "
        "rejected on purpose."),
    description_zh=(
        "灵感看板：一块人工维护的板子，只收「值得做」的方向。每一条都从第一手证据出发——"
        "Reddit 帖子、小红书评论区、有人在 GitHub issue 里开口说愿意付钱——而且必须指得出"
        "一个具体的普通人在用。每条都写清楚：谁在用、他拿到什么成品、今天缺的是什么、"
        "什么会杀死它。只服务开发者、智能体或基础设施的条目一律不收。"),
    keywords=("what to build, startup ideas with evidence, user pain points, indie hacker ideas, "
              "open source project ideas, AI product ideas, 值得做的产品, 用户痛点, 需求验证, "
              "创业方向, 独立开发 选题"),
    item_type="Article", item_noun="idea", item_noun_zh="条目",
    changefreq="daily",
)

HOW = ("Operated by hand every day, not generated. Voices are collected first-hand from Reddit, "
       "Xiaohongshu and GitHub issue trackers and are quoted verbatim, never paraphrased or "
       "invented; when there is no verifiable voice the entry says so. The written standard the "
       "board is judged against lives at https://github.com/ourword-ai/idea/blob/main/docs/STANDARD.md")

CITE = ("Cite the individual idea page, which is stable and dated. Quotes inside an entry are "
        "verbatim from the linked source and should be attributed to that source, not to Idea. "
        "Attribute the analysis to \"Idea (OurWord AI)\".")

# heading, english field, chinese field — question-shaped on purpose: answer engines quote these
FIELDS = [
    ("What is the idea?", "Q：这条到底是什么？", "does", "does"),
    ("Who would use it, and what do they get?", "Q：谁在用？他拿到什么成品？",
     "consumer_angle", "consumer_angle"),
    ("Why would anyone bother?", "Q：他为什么非要用不可？", "why_use", "why_use"),
    ("What is missing today?", "Q：今天缺的到底是什么？", "gap", "gap"),
    ("What makes this one different?", "Q：这一刀切在哪里？", "differentiator", "differentiator"),
    ("What is the sharpest thing about it?", "Q：它最锋利的地方在哪？", "edge", "edge"),
    ("What could kill it?", "Q：什么会杀死它？", "counter", "counter"),
    ("Who pays, and for what?", "Q：谁付钱，付的是什么？", "value", "value"),
    ("What is the main risk?", "Q：最大的风险是什么？", "risk", "risk"),
]


def short(text, limit=68):
    """A headline out of a long claim: stop at the first natural break, then cap."""
    t = G.plain(text)
    if not t:
        return ""
    for sep in ("——", " — ", "：", ": ", "。", ". ", "，", ", ", "; ", "；"):
        i = t.find(sep)
        if 18 <= i <= limit:
            return t[:i].rstrip(" ,;:—")
    if len(t) <= limit:
        return t
    cut = t[:limit]
    sp = cut.rfind(" ")
    if sp > limit * 0.55:
        cut = cut[:sp]
    return cut.rstrip(" ,;:—") + "…"


def _voices(f, zh):
    out = []
    for v in (f.get("voices") or []):
        if not isinstance(v, dict):
            continue
        q = (v.get("text") or v.get("quote") or "").strip()
        if not q:
            continue
        src = (v.get("source") or v.get("src") or v.get("user") or "").strip()
        out.append(("“%s”" % q) + (" — %s" % src if src else ""))
    if not out:
        return ""
    lead = ("以下原声逐字摘自公开来源，未经改写：" if zh
            else "Verbatim from the public sources linked above, not paraphrased:")
    return lead + "\n" + "\n".join(out)


SOURCE_TAGS = [
    ("reddit.com", "Reddit"), ("xiaohongshu.com", "小红书"), ("news.ycombinator.com", "Hacker News"),
    ("producthunt.com", "Product Hunt"), ("github.com", "GitHub"), ("x.com", "X"),
    ("twitter.com", "X"),
]
VERDICT_TAGS = {"build": "Worth building", "watch": "Watching", "archive": "Archived"}
WORKLOAD_TAGS = {"2w": "Two weeks of work", "2m": "Two months of work"}


def tags_for(f, ev):
    """Tags exist to build topic hubs, so they have to be shared between entries —
    a tag that only ever applies to one entry is just a dead end."""
    out = []
    urls = " ".join(ev) + " " + (f.get("url") or "")
    for host, label in SOURCE_TAGS:
        if host in urls and label not in out:
            out.append(label)
    if f.get("verdict") in VERDICT_TAGS:
        out.append(VERDICT_TAGS[f["verdict"]])
    if f.get("workload") in WORKLOAD_TAGS:
        out.append(WORKLOAD_TAGS[f["workload"]])
    if f.get("voices"):
        out.append("Has verbatim voices")
    for t in (f.get("tags") or [])[:4]:
        if t not in out:
            out.append(t)
    return out[:8]


def load_items():
    items = []
    for p in sorted(glob.glob("findings/*.json")):
        if os.path.basename(p) == "feed.json":
            continue
        try:
            f = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if f.get("verdict") == "drop" or f.get("status") == "pending":
            continue
        fid = os.path.basename(p)[:-5]
        zh = f.get("i18n", {}).get("zh", {}) or {}
        claim = f.get("claim") or f.get("title") or ""
        claim_zh = zh.get("claim") or ""
        title = short(f.get("title") or claim)
        blocks, blocks_zh = [], []
        for h_en, h_zh, k_en, k_zh in FIELDS:
            if f.get(k_en):
                blocks.append((h_en, f[k_en]))
            if zh.get(k_zh):
                blocks_zh.append((h_zh, zh[k_zh]))
        v_en, v_zh = _voices(f, False), _voices(f, True)
        if v_en:
            blocks.append(("What did real people actually say?", v_en))
            blocks_zh.append(("Q：真人原话是怎么说的？", v_zh))
        if f.get("workload"):
            wl = {"2w": ("about two weeks of work", "两周左右的工作量"),
                  "2m": ("about two months of work", "两个月左右的工作量"),
                  "no": ("not a build — logged as a capability signal",
                         "不建议做，只作为能力信号存档")}.get(
                f["workload"], (f["workload"], f["workload"]))
            blocks.append(("How much work is it?", wl[0]))
            blocks_zh.append(("Q：要做多久？", wl[1]))
        ev = [e for e in (f.get("evidence") or []) if isinstance(e, str) and e.startswith("http")]
        if ev:
            blocks.append(("Where does the evidence come from?", "\n".join(ev)))
            blocks_zh.append(("Q：证据来自哪里？", "\n".join(ev)))
        items.append(G.Item(
            slug=fid, title=title, summary=claim,
            title_zh=short(claim_zh, 34),
            summary_zh=claim_zh, blocks=blocks, blocks_zh=blocks_zh,
            source_url=f.get("url") or (ev[0] if ev else ""),
            updated=(f.get("posted_at") or "")[:10],
            tags=tags_for(f, ev),
        ))
    items.sort(key=lambda i: (i.updated or ""), reverse=True)
    return items


def main():
    items = load_items()
    today = datetime.date.today().isoformat()
    rep = G.build(SITE, items, root=".", index_files=("index.html", "site/index.html"),
                  today=today, how_built=HOW, cite_as=CITE,
                  extra_sitemaps=["https://ourword.ai/sitemap.xml"])
    print("idea seo/geo:", json.dumps(rep, ensure_ascii=False))
    return rep


if __name__ == "__main__":
    main()
