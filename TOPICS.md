# Episode backlog — source-verified

Every metric below was pulled from a fetched primary source on 2026-07-31, not from recall.
The SOURCES ledger under each topic is the contract: a number may only be spoken in a script
if it appears here with a URL and the verbatim sentence containing it.

**Three numbers I would have gotten wrong from memory alone** — kept here as a standing argument
for never skipping the fetch:
- Cloudflare's traffic drop was **80%**, not the ~50% I'd have said.
- GitLab had **five** backup/replication techniques fail, not four. (This bullet itself
  said "four, not five" until 2026-08-07 — it was counted off the postmortem's four-item
  procedure list without checking the live incident notes, whose verbatim sentence is "out
  of five backup/replication techniques deployed none are working reliably or set up in
  the first place". The wrong count shipped in EP02's end card. A number sourced from one
  primary document can still be contradicted by the other one.)
- Knight's loss is **over $460M** per the SEC order; the widely-repeated "$440M" is Knight's own
  pre-tax figure from its 8-K. Both are real numbers describing different things — that
  discrepancy is itself a good on-screen beat.

Proposed launch order goes broad-and-gripping → deep-and-differentiating.

---

## EP01 — Knight Capital
### `The $460 Million Deploy`

**Core hook & stake.** On 1 Aug 2012 Knight Capital's SMARS order router was updated for the
NYSE's new Retail Liquidity Program. The deploy reached seven of eight servers. The eighth still
carried Power Peg, dead code from 2003, and the team had *repurposed the very flag that
activated it*. In 45 minutes the firm took over $460 million in losses and effectively ceased to
exist as an independent company.

**Why it works as EP1.** Largest money number in the backlog, the mechanism is three moves deep
(partial deploy → repurposed flag → dead code), and every engineer watching has done a deploy
that didn't reach every box.

**Titles**
1. *Search:* `The Knight Capital Deployment Failure: How $460M Vanished in 45 Minutes`
2. *Curiosity:* `They Deployed to 7 of 8 Servers. It Cost $460 Million.`
3. *Punchy:* `The $460M Deploy` (17 chars)

**Thumbnail.** Text `7 OF 8`. Eight server rectangles in sketch outline, seven ink-grey with a
tick, the eighth red with a spark. Palette: off-white paper, ink, one red accent.

**SOURCES**
| Claim | Source | Verbatim |
|---|---|---|
| Loss over $460M | [WilmerHale on SEC settlement](https://www.wilmerhale.com/en/insights/client-alerts/knight-capital-settles-rule-15c3-5-violations-with-sec-agrees-to-pay-12-million) | "suffering a trading loss of over $460 million" |
| 45 minutes | ibid. | "during the first 45 minutes of trading on August 1, 2012" |
| 4M+ orders, 397M shares | ibid. | "sent over 4 million orders to the market"; "trading more than 397 million shares" |
| To fill 212 retail orders | ibid. | "in an effort to fill 212 small retail orders" |
| $12M SEC penalty | ibid. | "agreed to pay $12 million to settle charges" |
| 1 of 8 servers missed | [Varma, quoting SEC order 34-70694](https://www.jrvarma.in/blog/Y2013/Knight-Capital.html) | "One of Knight's technicians did not copy the new code to one of the eight SMARS computer servers" |
| Cumulative-quantity check moved in 2005 | ibid. | "In 2005, Knight moved the tracking of cumulative shares function in the Power Peg code to an earlier point in the SMARS code sequence" |
| 4M executions, 154 stocks | ibid. | "obtained over 4 million executions in 154 stocks for more than 397 million shares" |

⚠ **Unverified — do not use:** the frequently-repeated "97 email alerts before market open".
Could not confirm against the order. Cut unless a primary source turns up.

---

## EP02 — Cloudflare, 2 July 2019
### `The Regex That Took Down 80% of the Internet's Front Door`

**Core hook & stake.** A single WAF rule containing `.*.*=.*` was pushed globally. Catastrophic
backtracking drove CPU to ~100% across every machine in Cloudflare's network. 80% of traffic
gone, 27 minutes, ended by a global kill switch.

**Why it works.** Pure algorithmic complexity — the audience can *feel* the O(n²) blowup, and the
step counts make it visual. Also the cleanest deployment-policy lesson in the backlog: the SOP
explicitly permitted WAF rules to skip the staged rollout that everything else went through.

**Titles**
1. *Search:* `Cloudflare's 2019 Outage: How One Regular Expression Caused Global Failure`
2. *Curiosity:* `This Regex Took Down 80% of Cloudflare's Traffic in 27 Minutes`
3. *Punchy:* `.*.*=.* — 27 Minutes` (20 chars)

**Thumbnail.** Text `ONE REGEX`. The literal pattern `.*.*=.*` huge in mono, a CPU gauge pegged at
100% behind it. Red accent on the gauge needle only.

**SOURCES** — all from [Cloudflare's own postmortem](https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/)
| Claim | Verbatim |
|---|---|
| CPU near 100% globally | "CPUs dedicated to serving HTTP/HTTPS traffic spiking to nearly 100% usage across the servers in our network" |
| 27 minutes | "The outage was 27 minutes" |
| 80% traffic lost | "we had lost 80% of our traffic" |
| Backtracking blowup | "With 20 `x`'s after the `=` the engine takes 555 steps to match!"; variant `.*.*=.*;` needed "5,353 steps" |
| WAF skipped staged rollout | "The SOP for a rule change specifically allows it to be pushed globally" (vs DOG → PIG → Canary → global) |
| Kill switch | "'global terminate', a mechanism built into Cloudflare to disable a single component worldwide" |
| Timeline | 13:31 merged · 13:42 deploy began · 14:00 WAF identified · 14:07 global terminate · 14:09 restored · 14:52 re-enabled |

---

## EP03 — GitLab, 31 January 2017
### `Five Backups. All Five Failed.`

**Core hook & stake.** A tired engineer ran a directory wipe against `db1.cluster.gitlab.com` —
the primary, not the secondary. ~300 GB gone. Then GitLab discovered that all five of its
backup/replication techniques had silently failed ("out of five backup/replication techniques
deployed none are working reliably or set up in the first place" — the live incident notes).
Recovery came from a staging-server copy and took 18 hours to transfer.

**Why it works.** The mistake is not the story — the five independent, silently-broken safety nets
are. Best "go check your own backups tonight" episode in the set, and GitLab's radical
transparency means the sourcing is unusually rich.

**Titles**
1. *Search:* `The GitLab 2017 Database Incident: Five Backup Systems, Zero Recovery`
2. *Curiosity:* `GitLab Deleted Their Production Database. Then Found All 5 Backups Were Broken.`
3. *Punchy:* `5 Backups. 0 Worked.` (20 chars)

**Thumbnail.** Text `0 OF 5`. Five sketch hard-drive icons, each stamped with a red ✕. A bare
blinking terminal cursor in the corner — not the literal `rm -rf`, which appears in neither
primary source (see ep03 research.md, "Unverified — do not use").

**SOURCES** — all from [GitLab's postmortem](https://about.gitlab.com/blog/2017/02/10/postmortem-of-database-outage-of-january-31/)
| Claim | Verbatim |
|---|---|
| Wrong server | "an engineer proceeds to wipe the PostgreSQL database directory, errantly thinking they were doing so on the secondary. Unfortunately this process was executed on the primary instead." |
| ~300 GB deleted | ~300 GB removed before the process was halted |
| Data loss scope | "at least 5000 projects, 5000 comments, and roughly 700 users"; window 17:20–23:30 UTC |
| pg_dump failure | "the backup procedure was using pg_dump 9.2, while our database is running PostgreSQL 9.6" |
| Alerting failure | "DMARC was not enabled for the cronjob emails, resulting in them being rejected by the receiver" |
| Azure snapshots | not enabled for DB servers — "we assumed that our other backup procedures were sufficient" |
| LVM snapshot age | most recent was "roughly 6 hours before the outage" |
| Replication | "a spike in database load caused the database replication process to stop" |
| Recovery | restored from a staging copy; "Copying the data from the staging to the production host took around 18 hours" |

---

## EP04 — GitHub, 21 October 2018
### `43 Seconds That Cost 24 Hours`

**Core hook & stake.** A routine optical-equipment replacement severed the US East Coast ↔ West
Coast link for 43 seconds. Orchestrator, following Raft, failed the MySQL primaries westward.
When the link returned, both coasts held writes the other had never seen. Total degradation:
24 hours 11 minutes.

**Why it works.** Best ratio hook on the channel — 43 seconds to 24 hours is a 2,000× amplification
and it fits in a thumbnail. It also teaches the single most under-appreciated distributed-systems
lesson: automated failover across a WAN can convert a blip into a split brain you cannot safely
undo.

**Titles**
1. *Search:* `GitHub's 2018 Outage: How a 43-Second Network Partition Caused 24 Hours of Downtime`
2. *Curiosity:* `The Network Blip Lasted 43 Seconds. GitHub Was Broken for 24 Hours.`
3. *Punchy:* `43 Seconds → 24 Hours` (21 chars)

**Thumbnail.** Text `43 SECONDS`. US map in sketch outline, east and west data centres joined by a
severed red line, a small `24h` counter ticking on the right.

**SOURCES** — all from [GitHub's post-incident analysis](https://github.blog/2018-10-30-oct21-post-incident-analysis/)
| Claim | Verbatim |
|---|---|
| 43s → 24h11m | "Connectivity between these locations was restored in 43 seconds, but this brief outage triggered a chain of events that led to 24 hours and 11 minutes of service degradation." |
| Orchestrator failover | "Orchestrator… began a process of leadership deselection, according to Raft consensus. The US West Coast data center and US East Coast public cloud Orchestrator nodes were able to establish a quorum and start failing over clusters" |
| Why it couldn't fail back | "Because the database clusters in both data centers now contained writes that were not present in the other data center, we were unable to fail the primary back over to the US East Coast data center safely." |
| Divergent writes | "one of our busiest clusters had 954 writes in the affected window" |
| Timeline | 22:52 UTC 21 Oct → 23:03 UTC 22 Oct |

---

## EP05 — Roblox, 28–31 October 2021
### `73 Hours Down: The Cost of One Optimisation`

**Core hook & stake.** Roblox enabled a new Consul streaming feature designed to *reduce* CPU and
bandwidth. Under simultaneous high read and high write load it produced contention instead. p50
Consul KV writes went from under 300 milliseconds to 2 seconds. Underneath, a BoltDB freelist had
grown to nearly a million free page IDs, so a 4.2 GB log store held just 489 MB of real data and
every write amplified. 73 hours down, 50 million daily players.

**Why it works.** The differentiator. Knight and Cloudflare are well-trodden; this one is deep,
recent, superbly documented, and barely covered on YouTube. Two interacting root causes is exactly
the shape senior engineers find satisfying, and it's the strongest argument in the backlog for the
"a performance optimisation is a change in failure modes" thesis.

**Titles**
1. *Search:* `The Roblox 73-Hour Outage: Consul, BoltDB Write Amplification, and Cascading Failure`
2. *Curiosity:* `A Performance Optimisation Took Roblox Down for 73 Hours`
3. *Punchy:* `73 Hours Offline` (16 chars)

**Thumbnail.** Text `73 HOURS`. A latency graph in sketch style climbing off the top of the frame,
`300ms` marked small at the bottom, `2s` marked large at the ceiling.

**SOURCES** — all from [Roblox's return-to-service report](https://about.roblox.com/newsroom/2022/01/roblox-return-to-service-10-28-10-31-2021/)
| Claim | Verbatim |
|---|---|
| 73 hours | "Starting October 28th and fully resolving on October 31st, Roblox experienced a 73-hour outage." |
| 50M daily players | "Fifty million players regularly use Roblox every day." |
| Infra scale | "over 18,000 servers and 170,000 containers" |
| Latency blowup | "The 50th percentile latency on these operations was typically under 300ms but was now 2 seconds." |
| Streaming contention | new streaming feature caused contention "under very high load—specifically, both a very high read load and a very high write load" |
| BoltDB freelist | "This 4.2GB log store is only storing 489MB of actual data…3.8GB is 'empty' space"; freelist "7.8MB since it contained nearly a million free page ids" |
| Fix | streaming disabled; "the 50th percentile for Consul KV writes lowered to 300ms" |

---

## Deeper bench (researched but not yet source-verified — do not script until fetched)

Failures: AWS S3 us-east-1 2017 · Meta BGP withdrawal 2021 · Fastly 2021 · CrowdStrike channel
file 291, 2024 · Slack 2021 Transit Gateway · Ariane 5 Flight 501 · Therac-25 · Mars Climate
Orbiter · Postgres XID wraparound at Sentry · Log4Shell.

Scaling wins (needed for tonal variety — an all-disaster channel gets exhausting around ep 8):
Discord Cassandra → ScyllaDB · Segment microservices → monolith · Figma Postgres sharding ·
Notion's block-table shard · Shopify Black Friday flash-sale architecture · Dropbox off S3.

**Backlog depth note.** Incidents with hard, publicly-sourced numbers realistically run 60–120.
That is roughly one to two years weekly before the well thins, and the scaling-wins category is
what doubles it. Worth deciding around ep 10 whether the channel is "failures" or the broader
"engineering decisions with numbers attached" — the second has far more runway.
