#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
geo_kit — shared SEO + GEO (generative engine optimization) generator for ourword.ai.

One file, no dependencies, deterministic output (unchanged data => byte-identical
files => no spurious commits). Every ourword.ai site drops this in `seo/` and calls
it from a tiny `seo/build_seo.py` adapter that turns that site's data into Items.

What it produces
  robots.txt        allow-list for search + AI answer engines, points at the sitemap
  sitemap.xml       every page, with lastmod
  llms.txt          short machine card: what this site is, how to read it, how to cite
  llms-full.txt     the ENTIRE corpus as plain text — this is what answer engines ingest
  feed.xml          RSS, for discovery
  /i/<slug>/        one static English page per item (answer-first, no JS)
  /zh/i/<slug>/     the Chinese twin, cross-linked with hreflang
  index.html        canonical/og fixed + JSON-LD + a <noscript> index of everything

Why it exists: GPTBot, ClaudeBot, PerplexityBot and friends do not execute JavaScript.
A client-rendered board is, to them, a blank page.
"""
import html as _html
import json
import os
import re
import unicodedata

SITE = "https://ourword.ai"

AI_AGENTS = [
    "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-Web", "anthropic-ai",
    "PerplexityBot", "Perplexity-User", "Google-Extended", "Googlebot", "Bingbot",
    "Applebot", "Applebot-Extended", "CCBot", "Amazonbot", "Bytespider", "YouBot",
    "cohere-ai", "Meta-ExternalAgent", "DuckAssistBot", "MistralAI-User",
]


# --------------------------------------------------------------------------- utils
def esc(x):
    return _html.escape(str(x or ""), quote=True)


def slugify(s, fallback="item"):
    s = unicodedata.normalize("NFKD", str(s or ""))
    out = []
    for ch in s.lower():
        if ch.isalnum() and ord(ch) < 128:
            out.append(ch)
        elif "一" <= ch <= "鿿":       # keep CJK, they are legal in URLs
            out.append(ch)
        elif ch in " -_/.":
            out.append("-")
    s = re.sub(r"-{2,}", "-", "".join(out)).strip("-")
    return (s or fallback)[:80]


def plain(s, limit=None):
    """Strip tags/whitespace down to something safe for a meta description."""
    s = re.sub(r"<[^>]+>", " ", str(s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit].rstrip() if limit else s


def _write(path, text):
    """Write only when changed, so reruns produce no commit noise."""
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            if f.read() == text:
                return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return True


# --------------------------------------------------------------------------- model
class Item(object):
    """One indexable thing: an idea, a skill, a person, a chapter.

    blocks / blocks_zh are [(heading, body_text)] and become the page's <section>s,
    the FAQ schema, and the llms-full.txt entry. Keep headings question-shaped where
    it is natural — answer engines quote those.
    """

    def __init__(self, slug, title, summary, blocks=None, title_zh="", summary_zh="",
                 blocks_zh=None, source_url="", updated="", tags=None, extra=None):
        self.slug = slugify(slug, "item")
        self.title = plain(title)
        self.summary = plain(summary)
        self.blocks = [(plain(h), plain(b)) for h, b in (blocks or []) if plain(b)]
        self.title_zh = plain(title_zh)
        self.summary_zh = plain(summary_zh)
        self.blocks_zh = [(plain(h), plain(b)) for h, b in (blocks_zh or []) if plain(b)]
        self.source_url = source_url or ""
        self.updated = (updated or "")[:10]
        self.tags = [plain(t) for t in (tags or []) if t]
        self.extra = extra or {}

    def has_zh(self):
        return bool(self.summary_zh or self.blocks_zh)

    def t(self, zh):
        return (self.title_zh or self.title) if zh else (self.title or self.title_zh)

    def s(self, zh):
        return (self.summary_zh or self.summary) if zh else (self.summary or self.summary_zh)

    def b(self, zh):
        return (self.blocks_zh or self.blocks) if zh else (self.blocks or self.blocks_zh)


class Site(object):
    def __init__(self, path, name, name_zh, tagline, tagline_zh, description,
                 description_zh, keywords="", item_type="Article", item_noun="entry",
                 item_noun_zh="条目", image="", lang="en", changefreq="daily"):
        self.path = path.strip("/")                       # "" for the apex
        self.base = SITE + ("/" + self.path + "/" if self.path else "/")
        self.name, self.name_zh = name, name_zh
        self.tagline, self.tagline_zh = tagline, tagline_zh
        self.description, self.description_zh = description, description_zh
        self.keywords = keywords
        self.item_type = item_type                        # schema.org type for items
        self.item_noun, self.item_noun_zh = item_noun, item_noun_zh
        self.image = image
        self.lang = lang
        self.changefreq = changefreq

    def url(self, rel=""):
        return self.base + rel.lstrip("/")


# --------------------------------------------------------------------- <head> patch
_HEAD_MARK = ("<!--GEO:HEAD:START-->", "<!--GEO:HEAD:END-->")
_BODY_MARK = ("<!--GEO:BODY:START-->", "<!--GEO:BODY:END-->")


def _strip_legacy(head):
    """Remove the tags we are about to own, so we never emit duplicates."""
    pats = [
        r'<link[^>]+rel=["\']canonical["\'][^>]*>',
        r'<link[^>]+rel=["\']alternate["\'][^>]*hreflang[^>]*>',
        r'<meta[^>]+property=["\']og:(url|title|description|image|site_name|type|locale)["\'][^>]*>',
        r'<meta[^>]+name=["\'](description|keywords|robots|twitter:[a-z:]+)["\'][^>]*>',
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>.*?</script>',
        r"<!--SEO:START-->.*?<!--SEO:END-->",
        _HEAD_MARK[0] + r".*?" + _HEAD_MARK[1],
    ]
    for p in pats:
        head = re.sub(p, "", head, flags=re.S | re.I)
    return head


def head_block(site, page_url, title, description, zh=False, alt_url="",
               ld=None, item=None):
    """The whole <head> contribution: canonical, hreflang, OG/Twitter, JSON-LD."""
    locale = "zh_CN" if zh else "en_US"
    out = [_HEAD_MARK[0]]
    out.append('<meta name="description" content="%s">' % esc(plain(description, 200)))
    if site.keywords:
        out.append('<meta name="keywords" content="%s">' % esc(site.keywords))
    out.append('<meta name="robots" content="index,follow,max-image-preview:large,'
               'max-snippet:-1,max-video-preview:-1">')
    out.append('<link rel="canonical" href="%s">' % esc(page_url))
    if alt_url:
        en_u, zh_u = (alt_url, page_url) if zh else (page_url, alt_url)
        out.append('<link rel="alternate" hreflang="en" href="%s">' % esc(en_u))
        out.append('<link rel="alternate" hreflang="zh-Hans" href="%s">' % esc(zh_u))
        out.append('<link rel="alternate" hreflang="x-default" href="%s">' % esc(en_u))
    out.append('<meta property="og:type" content="%s">'
               % ("article" if item else "website"))
    out.append('<meta property="og:site_name" content="%s">' % esc(site.name))
    out.append('<meta property="og:locale" content="%s">' % locale)
    out.append('<meta property="og:title" content="%s">' % esc(title))
    out.append('<meta property="og:description" content="%s">' % esc(plain(description, 200)))
    out.append('<meta property="og:url" content="%s">' % esc(page_url))
    if site.image:
        out.append('<meta property="og:image" content="%s">' % esc(site.image))
    out.append('<meta name="twitter:card" content="%s">'
               % ("summary_large_image" if site.image else "summary"))
    out.append('<meta name="twitter:title" content="%s">' % esc(title))
    out.append('<meta name="twitter:description" content="%s">' % esc(plain(description, 200)))
    if site.image:
        out.append('<meta name="twitter:image" content="%s">' % esc(site.image))
    for obj in (ld or []):
        out.append('<script type="application/ld+json">%s</script>'
                   % json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    out.append(_HEAD_MARK[1])
    return "".join(out)


def patch_index(path, site, items, zh=False, extra_ld=None):
    """Rewrite an existing hand-built index.html's head + inject a <noscript> index."""
    if not os.path.exists(path):
        return False
    src = open(path, encoding="utf-8").read()
    m = re.search(r"(<head[^>]*>)(.*?)(</head>)", src, flags=re.S | re.I)
    if not m:
        return False
    head = _strip_legacy(m.group(2))

    title = site.name_zh + " — " + site.tagline_zh if zh else site.name + " — " + site.tagline
    desc = site.description_zh if zh else site.description
    ld = [org_ld(), website_ld(site, zh)]
    if items:
        ld.append(itemlist_ld(site, items, zh))
    ld += (extra_ld or [])
    head = head + head_block(site, site.url(), title, desc, zh=zh, ld=ld)
    src = src[:m.start(2)] + head + src[m.end(2):]

    if items:
        src = _inject_body(src, noscript_index(site, items))
    return _write(path, src)


def _inject_body(src, block):
    if _BODY_MARK[0] in src:
        return re.sub(re.escape(_BODY_MARK[0]) + r".*?" + re.escape(_BODY_MARK[1]),
                      lambda _m: block, src, count=1, flags=re.S)
    return re.sub(r"</body>", block + "\n</body>", src, count=1, flags=re.I)


def noscript_index(site, items):
    """A crawlable table of contents that JS-less agents (i.e. all of them) can read."""
    rows = []
    for it in items:
        u = site.url("i/%s/" % it.slug)
        rows.append('<li><a href="%s">%s</a> — %s</li>'
                    % (esc(u), esc(it.title or it.title_zh),
                       esc(plain(it.summary or it.summary_zh, 220))))
    return (_BODY_MARK[0] +
            '<noscript><section id="geo-index"><h2>%s</h2><p>%s</p><ul>%s</ul>'
            '<p><a href="%s">llms.txt</a> · <a href="%s">llms-full.txt</a> · '
            '<a href="%s">sitemap.xml</a></p></section></noscript>'
            % (esc(site.name + " — " + site.tagline), esc(plain(site.description, 400)),
               "".join(rows), esc(site.url("llms.txt")),
               esc(site.url("llms-full.txt")), esc(site.url("sitemap.xml")))
            + _BODY_MARK[1])


# ------------------------------------------------------------------------ JSON-LD
def org_ld():
    return {"@context": "https://schema.org", "@type": "Organization", "name": "OurWord AI",
            "alternateName": "用 AI 触摸这个世界", "url": SITE + "/",
            "sameAs": ["https://github.com/ourword-ai"]}


def website_ld(site, zh=False):
    return {"@context": "https://schema.org", "@type": "WebSite",
            "name": site.name_zh if zh else site.name,
            "alternateName": site.name if zh else site.name_zh,
            "url": site.base, "inLanguage": ["en", "zh-Hans"],
            "description": plain(site.description_zh if zh else site.description, 500),
            "publisher": {"@type": "Organization", "name": "OurWord AI", "url": SITE + "/"}}


def itemlist_ld(site, items, zh=False):
    els = []
    for i, it in enumerate(items, 1):
        els.append({"@type": "ListItem", "position": i, "url": site.url("i/%s/" % it.slug),
                    "name": it.t(zh)})
    return {"@context": "https://schema.org", "@type": "ItemList",
            "name": (site.name_zh if zh else site.name) + " — " +
                    (site.tagline_zh if zh else site.tagline),
            "url": site.base, "numberOfItems": len(els), "itemListElement": els}


def breadcrumb_ld(site, it, zh):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "OurWord AI", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": site.name_zh if zh else site.name,
         "item": site.base},
        {"@type": "ListItem", "position": 3, "name": it.t(zh),
         "item": site.url(("zh/i/%s/" if zh else "i/%s/") % it.slug)}]}


def item_ld(site, it, zh, page_url):
    d = {"@context": "https://schema.org", "@type": site.item_type,
         "name": it.t(zh), "headline": it.t(zh), "url": page_url,
         "description": plain(it.s(zh), 500),
         "inLanguage": "zh-Hans" if zh else "en",
         "isPartOf": {"@type": "WebSite", "name": site.name_zh if zh else site.name,
                      "url": site.base},
         "publisher": {"@type": "Organization", "name": "OurWord AI", "url": SITE + "/"}}
    if it.updated:
        d["dateModified"] = it.updated
        d["datePublished"] = it.updated
    if it.tags:
        d["keywords"] = ", ".join(it.tags)
    if it.source_url:
        d["citation"] = it.source_url
        d["sameAs"] = it.source_url
    if site.item_type == "SoftwareApplication":
        d["applicationCategory"] = "DeveloperApplication"
        d.setdefault("offers", {"@type": "Offer", "price": "0", "priceCurrency": "USD"})
    return d


def faq_ld(it, zh):
    """Heading/body pairs become a FAQPage — the single highest-yield GEO schema."""
    qs = [{"@type": "Question", "name": h,
           "acceptedAnswer": {"@type": "Answer", "text": plain(b, 1200)}}
          for h, b in it.b(zh) if h and len(plain(b)) > 40]
    if len(qs) < 2:
        return None
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": qs}


# --------------------------------------------------------------------- item pages
_PAGE_CSS = (
    "*{box-sizing:border-box}body{margin:0;background:#f0f0ec;color:#2a2e2c;"
    "font:16px/1.75 -apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC',"
    "'Noto Sans SC',sans-serif;-webkit-font-smoothing:antialiased}"
    "main{max-width:720px;margin:0 auto;padding:24px 24px 72px}"
    "a{color:#3a5f3a}nav.bc{font-size:13px;color:#767c76;margin:8px 0 24px}"
    "nav.bc a{color:#767c76;text-decoration:none}nav.bc a:hover{text-decoration:underline}"
    "h1{font-size:26px;line-height:1.3;margin:0 0 12px;letter-spacing:-.01em}"
    "h2{font-size:16px;margin:28px 0 6px;letter-spacing:-.005em}"
    ".lede{font-size:17px;color:#4c524e;margin:0 0 20px}"
    ".meta{font-size:13px;color:#767c76;margin:0 0 24px}"
    ".tags{margin:20px 0 0}.tags span{display:inline-block;font-size:12px;color:#4c524e;"
    "background:rgba(42,46,44,.05);border-radius:999px;padding:3px 10px;margin:0 6px 6px 0}"
    "footer{margin-top:40px;padding-top:20px;border-top:1px solid rgba(42,46,44,.12);"
    "font-size:13px;color:#767c76}footer a{color:#4c524e}"
    "p{margin:0 0 14px}.sib{margin-top:28px;font-size:14px}"
)


def _sib_links(site, items, idx, zh):
    pre = "zh/i/%s/" if zh else "i/%s/"
    out = []
    if idx > 0:
        p = items[idx - 1]
        out.append('← <a href="%s">%s</a>' % (esc(site.url(pre % p.slug)), esc(p.t(zh))))
    if idx < len(items) - 1:
        n = items[idx + 1]
        out.append('<a href="%s">%s</a> →' % (esc(site.url(pre % n.slug)), esc(n.t(zh))))
    return ('<p class="sib">%s</p>' % " &nbsp;·&nbsp; ".join(out)) if out else ""


def item_page(site, it, items, idx, zh):
    page_url = site.url(("zh/i/%s/" if zh else "i/%s/") % it.slug)
    alt_url = site.url(("i/%s/" if zh else "zh/i/%s/") % it.slug) if it.has_zh() else ""
    title = "%s — %s" % (it.t(zh), site.name_zh if zh else site.name)
    ld = [org_ld(), item_ld(site, it, zh, page_url), breadcrumb_ld(site, it, zh)]
    f = faq_ld(it, zh)
    if f:
        ld.append(f)

    secs = []
    for h, b in it.b(zh):
        secs.append("<h2>%s</h2>" % esc(h) if h else "")
        for para in str(b).split("\n"):
            if para.strip():
                secs.append("<p>%s</p>" % esc(para.strip()))

    lbl = {
        True: ("首页", "本页可直接引用", "来源", "更新于", "返回", "英文版"),
        False: ("Home", "Cite this page", "Source", "Updated", "Back to", "中文版"),
    }[zh]

    body = [
        '<nav class="bc"><a href="%s">%s</a> › <a href="%s">%s</a> › %s</nav>'
        % (esc(SITE + "/"), lbl[0], esc(site.base), esc(site.name_zh if zh else site.name),
           esc(it.t(zh))),
        "<h1>%s</h1>" % esc(it.t(zh)),
        '<p class="lede">%s</p>' % esc(it.s(zh)),
    ]
    meta = []
    if it.updated:
        meta.append("%s %s" % (lbl[3], esc(it.updated)))
    if it.source_url:
        meta.append('%s <a href="%s" rel="nofollow noopener">%s</a>'
                    % (lbl[2], esc(it.source_url), esc(it.source_url[:70])))
    if alt_url:
        meta.append('<a href="%s">%s</a>' % (esc(alt_url), lbl[5]))
    if meta:
        body.append('<p class="meta">%s</p>' % " · ".join(meta))
    body += secs
    if it.tags:
        body.append('<p class="tags">%s</p>'
                    % "".join("<span>%s</span>" % esc(t) for t in it.tags))
    body.append(_sib_links(site, items, idx, zh))
    body.append('<footer><p>%s <a href="%s">%s</a>.</p>'
                '<p>%s: <code>%s</code></p>'
                '<p><a href="%s">llms.txt</a> · <a href="%s">llms-full.txt</a> · '
                '<a href="%s">OurWord AI</a></p></footer>'
                % (lbl[4], esc(site.base), esc(site.name_zh if zh else site.name),
                   lbl[1], esc(page_url), esc(site.url("llms.txt")),
                   esc(site.url("llms-full.txt")), esc(SITE + "/")))

    return ("<!DOCTYPE html>\n<html lang=\"%s\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
            "<title>%s</title>\n%s\n<style>%s</style>\n</head>\n<body>\n<main>\n%s\n"
            "</main>\n</body>\n</html>\n"
            % ("zh-Hans" if zh else "en", esc(title),
               head_block(site, page_url, title, it.s(zh), zh=zh, alt_url=alt_url,
                          ld=ld, item=it),
               _PAGE_CSS, "\n".join(x for x in body if x)))


def write_item_pages(site, items, root="."):
    n = 0
    for i, it in enumerate(items):
        if _write(os.path.join(root, "i", it.slug, "index.html"),
                  item_page(site, it, items, i, False)):
            n += 1
        if it.has_zh():
            if _write(os.path.join(root, "zh", "i", it.slug, "index.html"),
                      item_page(site, it, items, i, True)):
                n += 1
    return n


# -------------------------------------------------------------- robots / sitemap
def write_robots(site, root=".", extra_sitemaps=()):
    lines = ["# %s — we want to be crawled, indexed, and cited by search and AI answer engines."
             % site.name, "", "User-agent: *", "Allow: /", ""]
    for a in AI_AGENTS:
        lines += ["User-agent: %s" % a, "Allow: /", ""]
    lines.append("Sitemap: %s" % site.url("sitemap.xml"))
    for s in extra_sitemaps:
        lines.append("Sitemap: %s" % s)
    lines.append("")
    return _write(os.path.join(root, "robots.txt"), "\n".join(lines))


def write_sitemap(site, items, root=".", today="", extra_urls=()):
    urls = [(site.base, "1.0", site.changefreq)]
    for u in extra_urls:
        urls.append((u, "0.7", site.changefreq))
    for it in items:
        urls.append((site.url("i/%s/" % it.slug), "0.8", "weekly"))
        if it.has_zh():
            urls.append((site.url("zh/i/%s/" % it.slug), "0.8", "weekly"))
    seen, rows = set(), []
    for u, pri, cf in urls:
        if u in seen:
            continue
        seen.add(u)
        rows.append("  <url><loc>%s</loc>%s<changefreq>%s</changefreq>"
                    "<priority>%s</priority></url>"
                    % (esc(u), ("<lastmod>%s</lastmod>" % today) if today else "", cf, pri))
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(rows) + "\n</urlset>\n")
    return _write(os.path.join(root, "sitemap.xml"), xml)


# ------------------------------------------------------------------ llms.txt / RSS
def write_llms(site, items, root=".", how_built="", cite_as=""):
    L = ["# %s (%s)" % (site.name, site.name_zh), "",
         "> %s" % plain(site.tagline), "> %s" % plain(site.tagline_zh), "",
         plain(site.description), "", plain(site.description_zh), "",
         "## Read it", "",
         "- Site: %s" % site.base,
         "- Every %s has its own static page: %si/<slug>/ (English) and %szh/i/<slug>/ (中文)"
         % (site.item_noun, site.base, site.base),
         "- Full text of everything, one file: %s" % site.url("llms-full.txt"),
         "- All URLs: %s" % site.url("sitemap.xml"),
         "- Part of OurWord AI: %s/" % SITE, ""]
    if how_built:
        L += ["## How it is built", "", plain(how_built), ""]
    L += ["## Citing", "",
          cite_as or ("Cite the individual page URL, not the homepage — each %s page is "
                      "stable and dated. Attribute to \"%s (OurWord AI)\"."
                      % (site.item_noun, site.name)), "",
          "## Index (%d %s)" % (len(items), site.item_noun + "s"), ""]
    for it in items:
        L.append("- [%s](%s): %s" % (it.title or it.title_zh, site.url("i/%s/" % it.slug),
                                     plain(it.summary or it.summary_zh, 200)))
    L.append("")
    ok = _write(os.path.join(root, "llms.txt"), "\n".join(L))

    F = ["# %s — %s" % (site.name, site.tagline),
         "# %s — %s" % (site.name_zh, site.tagline_zh),
         "# %s" % site.base,
         "# Full corpus, plain text. %d %ss." % (len(items), site.item_noun), ""]
    for it in items:
        F += ["=" * 72, "## %s" % (it.title or it.title_zh)]
        if it.title_zh and it.title and it.title_zh != it.title:
            F.append("## %s" % it.title_zh)
        F.append("URL: %s" % site.url("i/%s/" % it.slug))
        if it.has_zh():
            F.append("URL (中文): %s" % site.url("zh/i/%s/" % it.slug))
        if it.source_url:
            F.append("Source: %s" % it.source_url)
        if it.updated:
            F.append("Updated: %s" % it.updated)
        if it.tags:
            F.append("Tags: %s" % ", ".join(it.tags))
        F.append("")
        if it.summary:
            F += [plain(it.summary), ""]
        for h, b in it.blocks:
            F += ["### %s" % h if h else "", plain(b), ""]
        if it.has_zh():
            F.append("--- 中文 ---")
            if it.summary_zh:
                F += [plain(it.summary_zh), ""]
            for h, b in it.blocks_zh:
                F += ["### %s" % h if h else "", plain(b), ""]
    ok = _write(os.path.join(root, "llms-full.txt"), "\n".join(F)) or ok
    return ok


def write_rss(site, items, root=".", limit=50):
    xs = []
    for it in items[:limit]:
        u = site.url("i/%s/" % it.slug)
        xs.append("    <item><title>%s</title><link>%s</link><guid isPermaLink=\"true\">%s"
                  "</guid><description>%s</description></item>"
                  % (esc(it.title or it.title_zh), esc(u), esc(u),
                     esc(plain(it.summary or it.summary_zh, 400))))
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n  <channel>\n'
           "    <title>%s</title>\n    <link>%s</link>\n    <description>%s</description>\n"
           "    <language>en</language>\n%s\n  </channel>\n</rss>\n"
           % (esc(site.name + " — " + site.tagline), esc(site.base),
              esc(plain(site.description, 400)), "\n".join(xs)))
    return _write(os.path.join(root, "feed.xml"), xml)


# ----------------------------------------------------------------------- one call
def build(site, items, root=".", index_files=("index.html",), today="",
          how_built="", cite_as="", extra_urls=(), extra_sitemaps=()):
    """Everything, in the right order. Returns a small report dict."""
    rep = {"items": len(items),
           "zh_items": sum(1 for i in items if i.has_zh()),
           "pages": write_item_pages(site, items, root),
           "robots": write_robots(site, root, extra_sitemaps),
           "sitemap": write_sitemap(site, items, root, today, extra_urls),
           "llms": write_llms(site, items, root, how_built, cite_as),
           "rss": write_rss(site, items, root)}
    rep["index"] = sum(1 for f in index_files
                       if patch_index(os.path.join(root, f), site, items))
    return rep
