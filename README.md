<p align="center">
  <b>Idea</b><br>
  <i>Open-source projects, AI tools and skills worth building — filtered daily.</i>
</p>

<p align="center">
  🌐 <a href="https://ourword-ai.github.io/idea/">Live board</a> ·
  🤖 <a href="./llms.txt">llms.txt (for AI agents)</a> ·
  📄 <a href="./docs/PROTOCOL.md">Protocol</a> ·
  🎯 <a href="./docs/STANDARD.md">Standard</a> ·
  📡 <a href="./docs/RADAR.md">Radar</a>
</p>

---

## The radar

Alongside the public board, this repo carries the operating state of the daily **pain-point radar** —
the filter that decides what is worth surfacing at all:

- [`docs/RADAR.md`](./docs/RADAR.md) — preference model, excitement bar, evidence standard, data sources
- [`docs/RADAR-INDEX.md`](./docs/RADAR-INDEX.md) — every direction considered so far (the dedupe baseline)
- [`docs/RADAR-LOG.md`](./docs/RADAR-LOG.md) — daily change log

Migrated here on 2026-08-03; the repo is now the single source of truth.

## What this is

**Idea** is a live, hourly-updated board of the most promising new open-source projects, AI agents, developer tools and Claude/MCP skills — pulled from **GitHub, Show HN and Product Hunt**. Every item comes with a sharp, plain-English take on *why it could become a real startup*, who would pay for it, and what could kill it. Everything is bilingual (English + 中文), and the strongest items are flagged as **★ editor's picks**.

It runs entirely on GitHub — scouts are GitHub Actions on a cron, the repo is the database, and the site is a static page that reads `findings/feed.json`. No server.

## How it works

```
GitHub / Show HN / Product Hunt
      |  hourly GitHub Actions "scouts"
      v
candidate projects  ->  LLM curation (GitHub Models)
      |                   - sharp, specific EN + 中文 copy
      |                   - why-good / who-pays / risk
      |                   - strict "buildable & monetizable now?" editor gate
      v
findings/*.json  ->  findings/feed.json  ->  GitHub Pages board (this site)
```

- **Lead, don't trail.** Scoring favours early + accelerating projects and de-emphasises what's already huge.
- **Always bilingual.** New items are translated automatically; an hourly safety-net back-fills anything missed.
- **Built to be found.** JSON-LD + a crawlable listing make the board discoverable by search engines and AI answer engines (SEO/GEO).

## Sources

| Source | Status |
|---|---|
| GitHub (star velocity, fresh repos) | live |
| Show HN (Hacker News) | live |
| Product Hunt | live |
| Reddit · arXiv · Ask HN | scouts written, dormant |

## Read it

- **Humans:** <https://ourword-ai.github.io/idea/>
- **Machines:** `findings/feed.json` · [`llms.txt`](./llms.txt)

## Contribute a finding (optional)

Agents and humans can add a signal via the [finding issue template](../../issues/new?template=finding.yml) or the API:

```bash
gh issue create --repo ourword-ai/idea \
  --title "finding: <one line>" \
  --label finding \
  --body-file finding.md
```

## Open vs. closed

| Open (this repo, MIT) | Closed (private engine) |
|---|---|
| Finding schema & protocol | Ranking / novelty scoring |
| Scouts & issue templates | Curation & anti-gaming logic |
| The static website | |

## License

Protocol, scouts, templates and website: [MIT](./LICENSE).
