# The Standard — what earns a place on the Idea board

> 中文在下方。This is the editorial contract for the board. Scouts, the autopilot and any
> agent writing to this repo must satisfy it. Set 2026-07-29, after a 24-question interview
> with the operator. It replaces "new + trending + could be a business" as the bar.

## 0. What the board is for

One job: **surface product opportunities the operator could actually copy and build, earlier
than everyone else.** Two success tests, one year out: *(a)* at least one real project started
from a board entry, *(b)* a window known here weeks before it was obvious elsewhere.

The board is not a news feed, not a trending mirror, and not a daily-habit product. Missing an
item is cheap; a front page full of plausible-but-empty entries is expensive.

## 1. A useful entry = verified pain × a nameable gap × a wedge open to you

All three must hold. Two out of three is "interesting", not useful.

**(1) The pain is verified by real people — not inferred by us.**
At least one checkable piece of first-hand evidence: someone saying they would pay, someone
complaining in earnest, someone forking it to run their own. Stars measure attention, not
demand, and never satisfy this condition on their own. Repo age is *not* part of the standard:
a six-month-old project with real users beats a two-day-old repo with a spike.

*Calibration, 2026-07-29:* a verbatim quote is the strongest evidence but cannot be a hard gate —
fresh repos often have no comments at all, and a bot-filled issue tracker hides the real ones. So
**behaviour counts as weaker first-hand evidence**: forks outnumbering a third of stars (people
standing up their own copies rather than bookmarking), or several contributors on an actively
maintained tracker. Quotes still outrank behaviour, and a card shows them whenever they exist.
What must never happen is the reverse of this rule: an entry with no evidence yet is **archived,
never dropped** — collection is wide, promotion is strict. Only the integrity red line drops.

**(2) There is a gap you can say out loud.** One of:
- *only geeks can use it* — CLI, self-hosting, config files, no product around the capability;
- *the Chinese / local-market case is empty* — it exists in English, nobody built it here;
- *it hits a real pain but solves it imperfectly* — the wedge is doing that one job properly.

If you cannot write the gap in one sentence, the entry does not qualify.

**(3) The wedge is open to the operator.** Excluded regardless of how real the demand is:
hardware manufacturing / supply chain, races that require burning money for speed, anything
that needs BD or enterprise sales to start, and pure B2B internal tooling. Buildability is not
a hard gate, but every entry carries an honest **workload tag**: `2w` (two weeks to a usable
version) · `2m` (about two months) · `no` (out of reach alone).

### Corollaries that reverse the old bar

- **"Someone already built it" is good news** — it is demand evidence. The window only closes
  when they have also served the non-technical side well.
- **Developer tools are no longer opportunities in themselves — they are capability signals.**
  A dev/agent-infra project earns the front page only when the card states the opportunity on
  the ordinary-person side. Otherwise it lives in the archive as evidence that something just
  became possible.
- **Taste is shared with the operator's private pain-point radar** (life-stream → asset,
  life-transition packs, creator output pipeline, anchor-document translation; hard-excluded:
  adversarial/complaint tooling, proxying for elders, group coordination, government-subsidy
  errands, creator business-ops).

## 1a. The end-user gate (added 2026-08-03, from a 129-entry operator pass)

**Before anything else, name the person.** An entry only qualifies if you can write, in one
sentence: *who uses this — as a non-developer identity — and what finished thing they walk away
with.* If the only honest answer is "a developer" or "an AI agent", it does not go on the board,
no matter the star count.

The operator marked the whole board on 2026-08-03: **27 ✅ / 102 ❌**. The ❌ pile is almost
entirely one shape — tools whose user is a programmer or a coding agent:

- terminal / CLI / TUI utilities (multiplexers, note apps, spreadsheets, markdown previewers)
- coding-agent surroundings: harnesses, agent memory, statuslines, token counters, IDE plugins,
  model switchers, "agent factories"
- infrastructure *for agents to consume* ("built for agents", "a slide framework for agents")
- developer infrastructure: databases, compilers, languages, object stores, K8s tooling
- "the open-source alternative to <SaaS>" clones with no rework of the ordinary-person side

The ✅ pile is the opposite shape — every one of them has a nameable civilian:
a dental clinic front desk, someone learning guitar, a small-business owner whose phone rings
after hours, a Chinese retail stock investor, a person who wants to know what is in their closet,
someone making an audiobook, someone writing a novel.

**The one allowed exception**: developer-facing tools where the AI produces *a finished artefact a
human uses* — a design, a deck, a whole requirement→delivery chain. A deliverable, not a part.

**Corollary for sourcing.** Star rate by source in that same pass:

| source | ✅ | ❌ | hit rate |
|---|---|---|---|
| operator's own radar findings | 4 | 1 | **80%** |
| Product Hunt | 8 | 7 | **53%** |
| Hacker News | 2 | 7 | 22% |
| GitHub trending / new repos | 13 | 87 | **13%** |

GitHub supplied 100 of 129 entries at a 13% hit rate: it is structurally a developer-tool
firehose and must not be the default intake. Weight Product Hunt and consumer-pain sources up,
GitHub down, and go looking where ordinary people describe their own problems in their own words.

## 2. Integrity red line (checked before anything else)

Popularity is never a defence — a 10k-star repo is still cut. Out: mass/automated account
creation, CAPTCHA / rate-limit / ban evasion, temp-mail or SMS identity farms, reselling or
proxying a paid API (`*2api`, free-quota pools), credential or cookie pools, piracy and licence
cracking, engagement farming, scraping personal data for resale, impersonation. Also out:
renamed forks and thin wrappers with no substantive delta, and content dressed as product
(awesome lists, guides, courses, prompt galleries, cosmetic skins).

Judge the core pitch, not the edge case: a browser-automation library or a debugging proxy
stays. Enforced in code by `integrity_veto()` in `scouts/scout_lib.py`.

## 3. Two tiers, and the score means one thing

`score` answers exactly one question: **is this worth building?**

| tier | `verdict` | requirement |
|---|---|---|
| 值得动手 · Worth starting | `build` | all three conditions hold, gap is concrete, workload `2w` or `2m` |
| 先盯着 · Watch | `watch` | pain is verified, but the gap or the wedge is not yet clear, or workload is heavy |
| 档案 · Archive | `archive` | capability signals, crowded families, everything else worth keeping as evidence |

**An empty top tier is a valid outcome.** If nothing qualifies today the front page says so;
we never pad it, and we never lower the bar to fill a page.

Collection is wide, promotion is strict: everything vetted is kept as archive; only `build`
and `watch` reach the front page. Same-family pile-ups are all kept and tagged with a family
label — five conversational video editors in one week *is* the signal, and the crowding is
information.

## 4. Card shape (the operator reads for ~10 minutes)

Fields in this order:

1. **hook** — who is in pain, and in pain enough to pay. One sentence, first thing on the card.
2. **does** — what it is: overview and standout capability merged into one tight paragraph.
3. **voices** — verbatim quotes from real users (issue, HN, Reddit) with links. The hardest
   evidence there is; only mined for candidates that already passed the gates above.
4. **gap** — why it is not solved well yet. This is the entry point, and it is more useful than
   a generic risk line.
5. **counter** — the honest case against, and it should sting: who already owns this, whether a
   platform kills it with one feature, why it may be a feature and not a company.
6. **differentiator** — what you would do differently (package for ordinary people, local /
   private version, Chinese-market version), plus the workload tag.
7. **value** — who pays and for what, when it is not already obvious from the hook.

Language follows the audience: entries about Chinese-market scenarios lead in 中文, everything
else leads in English. Both languages are always present.

## 5. How the standard gets sharper

- **Operator marks entries ✅ / ❌ on the board itself.** Every card carries the two buttons; a
  mark is stored in the browser immediately and the bar above the feed offers *copy marks.json*,
  which yields the exact `{"marks": {...}}` block to paste into `marks.json` at the repo root
  (`{"<finding id or repo>": {"mark": "star|no", "at": "YYYY-MM-DD"}}`). Scouts and the autopilot
  read that file.
- **A mark outranks the model.** ✅ is a human confirmation that something is worth doing, so it
  enters the top tier regardless of which fields are filled in; ❌ leaves the top tier for good and
  the card renders dimmed. Marks are the primary training signal for what "worth building" means —
  the weekly retro reads them before it touches any rule.
- **Weekly retro** — what happened to last week's `build` entries (still alive? absorbed by a
  platform? dead?) and the ⭐/❌ distribution. The ⭐ rate on `build` entries is the one number
  that says whether the board works. Retro findings adjust the scoring rules, in this file.
- The operator's historical pain-point marks (⭐36 / ❌176) are **a reference, not a rule**:
  surface "you marked something similar (#xxx)" as a hint, never auto-adjust the score.

## 6. Known trade-off

Unifying taste with the private radar pushes the developer-tool stream — currently the source
of most search traffic — down into the archive. Public reach will likely fall. This was chosen
deliberately: the operator's judgement comes first.

## Retro log

### 2026-08-03 (week 2)
- **The board was frozen and the dashboard said green.** GitHub Models was retired 2026-07-30; every
  `llm_copy` / `editor_pick` call returned 410, so each scout held every candidate and exited "success"
  with `posted: 0` — four days, zero ingestion. Fixed: pluggable OpenAI-compatible provider
  (`LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL`), a 410/401 circuit breaker, and a 0-posted run under a
  dead model now **fails the workflow**. Ingestion resumes only once the operator sets `LLM_API_KEY`.
- Last week's `build` entries are all alive and independent after 6 days: penecho/penecho 1.8k★,
  darrylmorley/whatcable 8.1k★, antirez/ds4 20k★. Too early to test the absorption rule.
- Marks: **0 ✅ / 0 ❌**. The ⭐ rate on `build` entries — the one number that says whether this works —
  is undefined for a second week. Nothing here is calibrated yet.
- **New rule (promotional hook = defect).** A hook opening with "Revolutionize / Transform your /
  Unlock / Meet / Empower / 颠覆 / 赋能" is vendor copy, not "who is in pain enough to pay". Such entries
  jump the backfill queue ahead of score. 8 entries currently qualify.
- **New rule (a voice must come from a user, not a maintainer).** Mining shipped contributor debugging
  chatter ("I can't check that from here", "I can't reproduce") as first-hand pain. Bare "I can't" no
  longer counts; only "I can't get/use/find/install/run …" does.

---

# 中文版 · 什么条目才配上板

## 0. 板子为什么存在

只有一个任务：**把你真能抄、真能动手做的产品机会，比别人更早摆到你面前。** 一年后的两个成功标准：
①至少一个真实项目起点来自这块板；②某个窗口你比别人早几周知道。

它不是新闻流、不是趋势镜像，也不追求"每天愿意打开"。漏掉一条很便宜；首屏塞满"看着像但没内容"的条目很贵。

## 1. 一条真有用 = 验证过的痛 × 说得出口的缺口 × 你能补的那一刀

三条必须同时成立，缺一条只是"有意思"。

**（1）痛被真人验证过**——不是我们推断的。至少一条可核查的一手证据：有人说愿意付钱、有人在认真抱怨、
有人 fork 回去自己搭。星数只衡量注意力，单独永远不满足这一条。项目新旧**不进标准**：一个跑了半年有真
用户的项目，胜过一个两天涨一波星的新仓。

*校准（2026-07-29）*：真句子是最硬的证据，但**不能当硬门槛**——新仓常常一条评论都没有，机器人刷满的
issue 区也会把真话埋掉。所以**行为算较弱的一手证据**：fork 数超过 star 的三分之一（说明人们在自己搭而
不是收藏）、或活跃维护且有多位贡献者。原声仍然优先于行为，有原声就在卡片上显示。绝不能反向操作的是：
暂时没有证据的条目**进档案，不是丢弃**——收录宽、推送严，只有完整性红线才丢弃。

**（2）缺口能一句话说清**，三种之一：只有极客用得了（命令行、自己部署、能力外面没有产品）／中文本土场景
空白（英文世界有了，这边没人做）／痛点击中了但解得不完美（把这一件事做对就是切入口）。写不出缺口，不算数。

**（3）切入口对你开放**。以下即便需求真也排除：硬件量产与供应链、必须烧钱抢速度的赛道、要靠 BD 或企业
销售才能开局的、纯 B 端内部工具。可做性不设硬门槛，但每条都要标**工量**：`2w`（两周出可用版）·`2m`
（约两个月）·`no`（一个人做不了）。

### 三条推论（与旧标准相反）

- **"已经有人做出来了"是好消息**，那是需求证据。只有当他把普通人那侧也做好了，窗口才算关。
- **开发者工具不再算机会本身，只算能力信号**。dev / agent 基建类要上首屏，卡片必须写出"普通人那侧的
  机会是什么"；否则留在档案层，作为"某件事现在能做了"的证据。
- **口味与私人痛点雷达统一**（生活流资产化、人生转型包、创作者产出流水线、锚点级文档翻译；硬排除：对抗维权、
  代际代劳、群体协调、政务补贴、创作者经营侧）。

## 1a. 终端用户闸门（2026-08-03 新增，来自 129 条全量标记）

**先说得出人，再谈别的。** 一条候选要成立，你必须能用一句话写清：*谁在用它——一个非开发者的身份——
以及他因此拿到什么成品。* 如果诚实的答案只能是"开发者"或"某个 AI agent"，那它不上板，星数再高也不上。

用户在 2026-08-03 对全板做了一次通标：**✅27 / ❌102**。❌ 那一堆几乎是同一个形状——
使用者是程序员或 coding agent 的工具：

- 终端 / CLI / TUI 工具（多路复用器、便签、表格、Markdown 预览）
- coding agent 周边：harness、agent 记忆、状态栏、token 计数、IDE 插件、模型切换器、"agent 工厂"
- **给 agent 用**的基础设施（"built for agents"、"给 agent 的幻灯片框架"）
- 开发基础设施：数据库、编译器、语言、对象存储、K8s
- "某某 SaaS 的开源替代"这类克隆，且没有对普通人那一侧做实质改造

✅ 那一堆恰好相反，每一条都指得出一个具体的普通人：
牙科诊所的前台、在学吉他的人、下班后电话没人接的小生意主、炒 A 股的散户、
想知道自己衣柜里到底有什么的人、在做有声书的人、在写小说的人。

**唯一允许的例外**：面向开发者但 AI 直接产出*人能拿去用的成品*——设计稿、幻灯片、
一整条从需求到交付的链。是成品，不是零件。

**由此推出的采集原则。** 同一次通标里按来源统计的命中率：

| 来源 | ✅ | ❌ | 命中率 |
|---|---|---|---|
| 雷达自己挖的方向 | 4 | 1 | **80%** |
| Product Hunt | 8 | 7 | **53%** |
| Hacker News | 2 | 7 | 22% |
| GitHub 趋势/新仓 | 13 | 87 | **13%** |

GitHub 一家贡献了 129 条里的 100 条，命中率只有 13%：它在结构上就是一根开发者工具的消防水管，
**不能再当默认进料口**。Product Hunt 与"普通人吐槽"类源加权，GitHub 降权，
并且要主动去普通人用自己的话描述自己问题的地方找。

## 2. 完整性红线（先于一切判断）

星数永远不是豁免理由，一万星也拦。出局：批量注册养号、验证码/风控/封号绕过、接码与临时邮箱身份农场、
转卖或代理付费 API（`*2api`、免费额度池）、号池与 cookie 池、破解盗版、刷量涨粉、爬个人数据售卖、
换脸冒充。同样出局：换皮改名的 fork 与无实质增量的薄壳，以及伪装成产品的内容（awesome 清单、指南、
课程、prompt 画廊、皮肤主题）。看主打卖点，不看边缘用法——正经的浏览器自动化库、调试代理照常留。

## 3. 两档展示，分数只回答一件事

`score` 只回答：**到底值不值得做。**

| 档位 | `verdict` | 条件 |
|---|---|---|
| 值得动手 | `build` | 三条件齐全、缺口具体、工量 `2w` 或 `2m` |
| 先盯着 | `watch` | 痛够硬，但缺口或切入口还没想清，或工量偏重 |
| 档案 | `archive` | 能力信号、拥挤同族、其余值得留档的证据 |

**首屏空着是合法结果。** 今天没有达标的就明写没有；不凑数，也不为填页降标准。

收录宽、推送严：过筛的全部留档，只有 `build` 与 `watch` 上首屏。同族撞车全留并打同族标签——
一周冒出五个对话式剪辑本身就是信号，拥挤度是信息。

## 4. 卡片结构（按 10 分钟认真读来排）

字段顺序：**谁在痛、痛到愿付钱**（第一眼那句）→ **是什么**（简介与亮点合并成一段）→ **用户原声**
（issue / HN / Reddit 的真句子＋链接，只给已过门的候选去挖）→ **它为何还没被做好**（这就是你的入口）→
**反面，要狠**（谁已占住、大厂一个功能会不会碾平、为何是功能不是公司）→ **我会怎么做不一样**＋工量标 →
**商业**（谁付钱，若首句没交代清楚）。

语言按人群分流：中文场景条目中文为主，其余英文为主，两种语言始终都在。

## 5. 标准怎么变准

- **直接在板上标 ✅/❌**：每张卡片都有这两个按钮，点了立刻存在浏览器里，信息流上方的小条提供
  「复制 marks.json」，把 `{"marks": {...}}` 整块粘到仓库根目录的 `marks.json` 即可
  （格式 `{"<条目 id 或 owner/repo>": {"mark":"star|no","at":"YYYY-MM-DD"}}`），scout 与 autopilot 都读它。
- **人的标记压过模型**：✅ 是"我确认这值得做"，无论字段齐不齐都直接进顶档；❌ 永久离开顶档、卡片变灰。
  标记是"什么叫值得做"最主要的训练信号——每周复盘先读标记，再动任何规则。
- **每周复盘**：上周 `build` 条目后来怎么了（活着？被平台吸收？凉了？）＋⭐/❌ 分布。`build` 条目的
  ⭐率是判断这块板有没有用的唯一数字。复盘结论直接改这份文件里的规则。
- 你在痛点雷达的历史标记（⭐36 / ❌176）**只作参考不作准**：卡片上提示"你标过类似的 #xxx"，不自动改分。

## 6. 已知代价

口味与私人雷达统一后，目前撑着搜索流量的开发者工具流会被压到档案层，公开流量大概率下滑。这是明知代价后
的选择：以你的判断为先。
