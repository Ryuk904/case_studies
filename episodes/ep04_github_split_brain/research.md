# EP04 — GitHub, 21 October 2018

## Core hook & stake

At 22:52 UTC on Sunday 21 October 2018, routine maintenance to replace a piece of failing
100-gigabit optical equipment cut the connection between GitHub's US East Coast network hub
and its primary US East Coast data centre. The link was back in 43 seconds. That was long
enough. GitHub's automated failover system, Orchestrator, running Raft consensus, saw the
East Coast go silent: the surviving nodes on the West Coast and in the East Coast public
cloud formed a quorum and promoted West Coast databases to be the new primaries. When the
link healed seconds later, the application tier obediently started writing to the West.

But the East Coast servers held a few seconds of writes that had never reached the West —
on the busiest cluster, 954 of them — and the West was now taking new writes of its own.
Two divergent copies, each holding history the other lacked, with no safe way to swap back.
GitHub chose the painful option deliberately: fail forward, protect every write, and eat
the downtime. Restoring multiple terabytes from cloud backups took hours; replication then
had to catch up against the morning traffic of Europe and the US waking up; over five
million webhook events and 80 thousand Pages builds queued behind it. The site went green
at 23:03 UTC on 22 October — 24 hours and 11 minutes of degradation from a 43-second blip,
roughly a 2,000× amplification. No user data was lost, and GitHub says that was the point.

**The channel-level echo:** EP03's GitLab had five backups and none worked. GitHub's
backups worked exactly as designed — tested daily, restore time well understood — and
recovery *still* took a day, because the constraint was physics (terabytes over a wire,
replication against live load), not negligence. The failure here is not a broken net; it
is an automated safety system doing exactly what it was configured to do, across a
boundary its designers never meant it to cross.

## The split-brain picture (the hard part, in plain language)

Two offices keep the same ledger. Only one office is allowed to hold the pen. For 43
seconds the offices cannot hear each other, and the second office, following its emergency
rulebook to the letter, picks up its own pen and starts writing. When the phones come back,
both books contain entries the other has never seen. You cannot photocopy one over the
other without erasing someone's real entries, and there is no honest way to shuffle the two
sets of pages into one book. That is the whole episode: the 43 seconds made the second pen,
and the 24 hours is what it costs to get back to one pen without tearing out anyone's page.

## Verification of EP03's end-card promise (done first, as instructed)

EP03 speaks: *"a 43 second network hiccup splits GitHub's database in two, and putting it
back together takes a full day."*

- **43 seconds** — confirmed verbatim: "Connectivity between these locations was restored
  in 43 seconds".
- **"a full day"** — confirmed: "led to 24 hours and 11 minutes of service degradation";
  timeline runs 22:52 UTC Oct 21 → 23:03 UTC Oct 22, which is 24h11m exactly. "A full day"
  is a fair rounding; the episode itself speaks the precise 24 hours and 11 minutes.
- TOPICS.md's "24 hours 11 minutes" — confirmed, matches the source.

**One description error found (not in a spoken number):** the kickoff brief and TOPICS.md
both say the maintenance "severed the East↔West link". The source says the lost link was
between **the US East Coast network hub and the primary US East Coast data centre** — the
partition isolated the East data centre from the rest of GitHub (which is why the West
plus the East public cloud could form a quorum without it). The *consequence* was an
East/West split, so the thumbnail's severed-coasts image survives as illustration, but the
script must describe the cut correctly. Flagged to the channel owner 2026-08-12.

## Titles (final call at seo.md time; must extend the triptych)

| | EP01 | EP02 | EP03 | EP04 |
|---|---|---|---|---|
| Title says | They forgot to delete some code | They did everything right | They deleted the wrong database | Nobody touched anything — the safety system did it |
| Failure was | code nobody deleted | code everybody approved | safety nets nobody tested | a failover nobody could undo |

1. **Curiosity / CTR:** The Outage Lasted 43 Seconds. Fixing It Took GitHub 24 Hours.
2. **Alternative:** GitHub's Failover Worked Perfectly. That Was the Problem.
3. **Punchy (<25 chars):** 43 Seconds → 24 Hours

## Thumbnail (concept only — one trimmed prompt goes in thumbnail_prompt.md)

Channel page so far: EP01 lit object on a dark wall, EP02 typographic line under a slab,
EP03 row of objects with a count. EP04 needs a fourth kind of image: **a frame torn in
two** — two halves of one database/ledger pulled apart by a red gap down the middle, each
half glowing with its own writes; text "43 SECONDS" / "BROKE GITHUB FOR A DAY". The tear
itself is the subject, which no earlier thumbnail has.

---

## PRIMARY SOURCES

**1. GitHub, "October 21 post-incident analysis",** The GitHub Blog, 30 October 2018,
by GitHub's SVP of Technology. Fetched in full 2026-08-12 and read end to end (plain-text
copy in `scratch/github_postmortem.txt`).

⚠ The URL in TOPICS.md and the kickoff brief
(`https://github.blog/2018-10-30-oct21-post-incident-analysis/`) now 301-redirects.
**Canonical URL (verified live 2026-08-12):**
https://github.blog/news-insights/company-news/oct21-post-incident-analysis/

**2. GitHub, "October 21 Incident Report",** The GitHub Blog, dated 21 October 2018 — the
short day-of statement published while the incident was still running (the postmortem's
07:46 UTC timeline entry, "GitHub published a blog post to provide more context", refers to
this). Fetched in full 2026-08-12 (plain-text copy in `scratch/github_incident_report.txt`).
**Canonical URL (verified live 2026-08-12; the old
`2018-10-22-october21-incident-report` slug redirects here):**
https://github.blog/news-insights/company-news/october21-incident-report/

## SOURCES — the contract

Every number spoken in `script.md` has a row here with the verbatim sentence containing it.
Unmarked rows are from the post-incident analysis; rows marked *day-of* are from the
incident report.

| Claim | Verbatim |
|---|---|
| **24 hours 11 minutes of degradation** | "Last week, GitHub experienced an incident that resulted in degraded service for 24 hours and 11 minutes." |
| **43 seconds; the chain of events** | "Connectivity between these locations was restored in 43 seconds, but this brief outage triggered a chain of events that led to 24 hours and 11 minutes of service degradation." |
| **Routine maintenance, failing 100G optical equipment, 22:52 UTC, what was cut** | "At 22:52 UTC on October 21, routine maintenance work to replace failing 100G optical equipment resulted in the loss of connectivity between our US East Coast network hub and our primary US East Coast data center." |
| It was a Sunday night | *day-of:* "At 10:52 pm Sunday UTC, multiple services on GitHub.com were affected by a network partition and subsequent database failure resulting in inconsistent information being presented on our website." |
| **No user data lost; a few seconds still being reconciled** | "Ultimately, no user data was lost; however manual reconciliation for a few seconds of database writes is still in progress." |
| Webhooks and Pages down for most of the incident | "For the majority of the incident, GitHub was also unable to serve webhook events or build and publish GitHub Pages sites." |
| The apology | "With this incident, we failed you, and we are deeply sorry." |
| Partitions were a known possibility | "Despite the layers of redundancy built into the physical and logical components in this design, it is still possible that sites will be unable to communicate with each other for some amount of time." |
| **What the database holds (metadata, not Git)** | "GitHub operates multiple MySQL clusters varying in size from hundreds of gigabytes to nearly five terabytes, each with up to dozens of read replicas per cluster to store non-Git metadata, so our applications can provide pull requests and issues, manage authentication, coordinate background processing, and serve additional functionality beyond raw Git object storage." |
| Writes go to one primary per cluster, reads to replicas | "To improve performance at scale, our applications will direct writes to the relevant primary for each cluster, but delegate read requests to a subset of replica servers in the vast majority of cases." |
| **Orchestrator, automated failover, Raft** | "We use Orchestrator to manage our MySQL cluster topologies and handle automated failover. Orchestrator considers a number of variables during this process and is built on top of Raft for consensus." |
| The foreshadow sentence | "It's possible for Orchestrator to implement topologies that applications are unable to support, therefore care must be taken to align Orchestrator's configuration with application-level expectations." |
| **The failover itself, 22:52 UTC** | "During the network partition described above, Orchestrator, which had been active in our primary data center, began a process of leadership deselection, according to Raft consensus. The US West Coast data center and US East Coast public cloud Orchestrator nodes were able to establish a quorum and start failing over clusters to direct writes to the US West Coast data center." |
| The link heals, writes go west | "When connectivity was restored, our application tier immediately began directing write traffic to the new primaries in the West Coast site." |
| **The split: why they could not switch back** | "Because the database clusters in both data centers now contained writes that were not present in the other data center, we were unable to fail the primary back over to the US East Coast data center safely." |
| The stranded East writes | "The database servers in the US East Coast data center contained a brief period of writes that had not been replicated to the US West Coast facility." |
| **First alerts at 22:54, two minutes in** | "Our internal monitoring systems began generating alerts indicating that our systems were experiencing numerous faults." (section heading: 2018 October 21 22:54 UTC) |
| 23:02: engineers see the wrong shape | "By 23:02 UTC, engineers in our first responder team had determined that topologies for numerous database clusters were in an unexpected state." |
| Orchestrator showed a West-only world | "Querying the Orchestrator API displayed a database replication topology that only included servers from our US West Coast data center." |
| 23:07 deploys frozen; 23:09 yellow; 23:13 red | "By this point the responding team decided to manually lock our internal deployment tooling to prevent any additional changes from being introduced. At 23:09 UTC, the responding team placed the site into yellow status." / "At 23:11 UTC the incident coordinator joined and two minutes later made the decision change to status red." |
| **By 23:13 the West held ~40 minutes of new writes** | "This effort was challenging because by this point the West Coast database cluster had ingested writes from our application tier for nearly 40 minutes." |
| The seconds of East writes blocked the way back | "Additionally, there were the several seconds of writes that existed in the East Coast cluster that had not been replicated to the West Coast and prevented replication of new writes back to the East Coast." |
| **The deliberate choice: fail forward to protect data** | "In an effort to preserve this data, we decided that the 30+ minutes of data written to the US West Coast data center prevented us from considering options other than failing-forward in order to keep user data safe." |
| Why the site then crawled: cross-country latency | "However, applications running in the East Coast that depend on writing information to a West Coast MySQL cluster are currently unable to cope with the additional latency introduced by a cross-country round trip for the majority of their database calls." |
| They knew what the choice cost | "This decision would result in our service being unusable for many users. We believe that the extended degradation of service was worth ensuring the consistency of our users' data." |
| **The strategy in one sentence** | "In other words, our strategy was to prioritize data integrity over site usability and time to recovery." |
| Webhooks/Pages paused deliberately at 23:19 | "We made an explicit choice to partially degrade site usability by pausing webhook delivery and GitHub Pages builds instead of jeopardizing data we had already received from users." |
| 00:05: the recovery plan | "Our plan was to restore from backups, synchronize the replicas in both sites, fall back to a stable serving topology, and then resume processing queued jobs." |
| **Backups every four hours, in remote cloud storage** | "While MySQL data backups occur every four hours and are retained for many years, the backups are stored remotely in a public cloud blob storage service." |
| Terabytes over the wire took hours | "The time required to restore multiple terabytes of backup data caused the process to take hours." |
| **The backups were tested daily — and still** | "This procedure is tested daily at minimum, so the recovery time frame was well understood, however until this incident we have never needed to fully rebuild an entire cluster from backup and had instead been able to rely on other strategies such as delayed replicas." |
| 06:51: first clusters restored | "Several clusters had completed restoration from backups in our US East Coast data center and begun replicating new data from the West Coast." |
| **The two-hour estimate, and why it was wrong** | "This estimate was linearly interpolated from the replication telemetry we had available and the status page was updated to set an expectation of two hours as our estimated time of recovery." / "In reality, the time required for replication to catch up had adhered to a power decay function instead of a linear trajectory." |
| The morning rush made it worse | "Due to increased write load on our database clusters as users woke up and began their workday in Europe and the US, the recovery process took longer than originally estimated." |
| 11:12: primaries back East, replicas hours behind | "All database primaries established in US East Coast again." / "While this improved performance substantially, there were still dozens of database read replicas that were multiple hours delayed behind the primary." |
| Users saw time-travel | "These delayed replicas resulted in users seeing inconsistent data as they interacted with our services." |
| 13:15: replication delays growing, not shrinking | "It was clear that replication delays were increasing instead of decreasing towards a consistent state." |
| The fix that worked: more replicas, less load each | "Once these became available it became easier to spread read request volume across more servers. Reducing the utilization in aggregate across the read replicas allowed replication to catch up." |
| 16:24: back to the original topology | "Once the replicas were in sync, we conducted a failover to the original topology, addressing the immediate latency/availability concerns." |
| **The backlog: 5 million+ webhooks, 80k Pages builds** | "There were over five million hook events and 80 thousand Pages builds queued." |
| ~200,000 webhook payloads expired and were dropped | "As we re-enabled processing of this data, we processed ~200,000 webhook payloads that had outlived an internal TTL and were dropped." |
| They stayed red on purpose until the backlog cleared | "To avoid further eroding the reliability of our status updates, we remained in degraded status until we had completed processing the entire backlog of data and ensured that our services had clearly settled back into normal performance levels." |
| **Green at 23:03 UTC, 22 October** | "All pending webhooks and Pages builds had been processed and the integrity and proper operation of all systems had been confirmed. The site status was updated to green." (section heading: 2018 October 22 23:03 UTC) |
| **954 writes on one of the busiest clusters** | "The total number of writes that were not replicated to the West Coast was relatively small. For example, one of our busiest clusters had 954 writes in the affected window." |
| Some writes users had already redone | "our analysis has already determined a category of writes that have since been repeated by the user and successfully persisted." |
| **The verdict: it behaved as configured** | "Orchestrator's actions behaved as configured, despite our application tier being unable to support this topology change." |
| **The fix: keep failover inside a region** | "Adjust the configuration of Orchestrator to prevent the promotion of database primaries across regional boundaries." |
| In-region failover is safe; cross-country was the poison | "Leader-election within a region is generally safe, but the sudden introduction of cross-country latency was a major contributing factor during this incident." |
| Emergent behaviour, never seen at this magnitude | "This was emergent behavior of the system given that we hadn't previously seen an internal network partition of this magnitude." |
| The takeaway initiative: test your assumptions | "We will take a more proactive stance in testing our assumptions." / "we will also begin a systemic practice of validating failure scenarios before they have a chance to affect you. This work will involve future investment in fault injection and chaos engineering tooling at GitHub." |
| **Git repositories were fine throughout** | *day-of:* "Further, this incident only impacted website metadata stored in our MySQL databases, such as issues and pull requests. Git repository data remains unaffected and has been available throughout the incident." |

### Derived, not quoted — and flagged as such

| Spoken as | Arithmetic |
|---|---|
| "roughly two thousand times longer than the glitch" | 24h11m = 87,060 s; 87,060 ÷ 43 ≈ 2,025. Speak "roughly two thousand", never a precise figure. |
| "a full day" (EP03's promise line, echoed in the hook) | 24h11m, and 22:52 Oct 21 → 23:03 Oct 22. The episode speaks the exact 24 hours and 11 minutes at least once. |
| "before anyone could even reach a keyboard" | link restored in 43 s; first monitoring alerts at 22:54, two minutes after the cut — every human action in the timeline comes after the failover was already done. |
| "seconds of writes on one side, forty minutes on the other" | "several seconds of writes" (East) vs "nearly 40 minutes" of ingestion (West, by 23:13). The asymmetry is the reason failing forward won. |
| "the estimate said two hours; it took another twelve" | two-hour estimate posted at 06:51; primaries East at 11:12 but replicas still hours behind; catch-up achieved between 13:15 and 16:24; green at 23:03. Keep it qualitative ("far longer") unless spoken with the timeline on screen. |

## ⚠ Contradictions and tensions inside the primary sources — handled, not hidden

- **"No data was lost" vs the dropped webhooks.** The day-of report says flatly "no data
  was lost". The postmortem says "Ultimately, no user data was lost; however manual
  reconciliation for a few seconds of database writes is still in progress" — and,
  separately, that ~200,000 webhook *payloads* expired and were dropped. These reconcile
  (webhook payloads are notifications to other services, not stored user data), but the
  script must not say "nothing was lost" unqualified. Speak the postmortem's version:
  no user data lost, some writes manually reconciled, and the dropped payloads named as
  what they are.
- **"Nearly 40 minutes" vs "30+ minutes" of West writes.** Same document, two figures —
  the 23:13 timeline entry says the West had ingested writes "for nearly 40 minutes"; the
  decision paragraph says "the 30+ minutes of data". Not strictly contradictory (different
  moments of an ongoing window), but the script picks one framing: "over half an hour", or
  "nearly forty minutes" tied explicitly to 23:13.
- **Where the cut was.** Not a source contradiction — the source is consistent — but both
  TOPICS.md and the kickoff brief paraphrase it as "the East↔West link". The severed link
  was **East Coast network hub ↔ primary East Coast data centre**. The East↔West split was
  the consequence, not the cut. Script describes it correctly; thumbnail may still show the
  coasts splitting because that is the consequence being illustrated.

## Next-episode tease (spoken on the end card) — EP05, Roblox

| Claim | Source | Verbatim |
|---|---|---|
| Roblox down 73 hours | Roblox, "Roblox Return to Service 10/28-10/31 2021", https://about.roblox.com/newsroom/2022/01/roblox-return-to-service-10-28-10-31-2021 (URL verified live and verbatim re-checked 2026-08-12) | "Starting October 28th and fully resolving on October 31st, Roblox experienced a 73-hour outage." |
| 50 million daily players | ibid. | "Fifty million players regularly use Roblox every day" |

## Photography — free-licence, generic, never evidence

Added on the rebuild (2026-08-12). Every pictorial scene sits on a treated photographic
plate so the episode is set in real places rather than on an empty ground. Three rules,
which keep this compatible with §4's sourcing standard:

- **Illustration, not evidence.** These depict *a* server room, *a* night skyline. None is
  presented as GitHub's own facility, and no photo of GitHub, its offices or its staff is
  used. Nothing is a screenshot, dashboard or document, real or fabricated.
- **Licence-clean.** CC0 / public domain / CC BY only. No share-alike (it would reach the
  finished video) and no non-commercial. Every file carries a `.json` sidecar with its
  source, creator and licence; `python -m pipeline.photo --list` prints the ledger.
- **CC BY plates must be credited in the published description.** Two are used, and the
  credit block is in `seo.md`; removing it breaks the licence.

| Plate | Used for | Licence | Creator |
|---|---|---|---|
| `night_city` | the two-coasts stage, the crossing, the fork | CC0 1.0 | pixellaphoto |
| `office_night` | the ledger desks, the war room, the night desk | CC0 1.0 | Wonderlane |
| `server_room` | the database racks, the haul | CC0 1.0 | — (rawpixel PD) |
| `sunrise_city` | the morning rush | CC0 1.0 | — (rawpixel PD) |
| `control_room` | the wall of disagreeing clocks | **CC BY 2.0** | NASA Goddard Photo and Video |
| `tape_backup` | the shelf of copies | **CC BY 2.0** | Government & Heritage Library, State Library of NC |

## ⚠ Unverified — do not use

- **Facility locations beyond "US East Coast" / "US West Coast".** Neither source names a
  city, state, or provider for either data centre. No "Virginia", no "Seattle".
- **Who performed the maintenance.** "Routine maintenance work to replace failing 100G
  optical equipment" is passive; no person, team, or vendor is named. Do not say "an
  engineer unplugged…" — nobody's hands are in the sourced story, which is also the point.
- **The number of MySQL clusters.** Only "multiple". Sizes: "hundreds of gigabytes to
  nearly five terabytes"; replicas: "up to dozens" per cluster. No total server count.
- **954 as a site-wide total.** It is one cluster's figure, introduced with "For example".
  Speak it only as "on one of their busiest clusters".
- **"954 writes in 43 seconds."** The source says the 954 fell in "the affected window"
  and describes the stranded East writes as "a brief period" / "several seconds" — it
  never equates the window to exactly 43 seconds. Keep the two numbers in separate
  sentences.
- **Any dollar cost, revenue impact, or user count.** None appears in either source.
- **"Split brain."** Useful shorthand, but the term appears in neither source. If spoken,
  it is our label for the situation, not GitHub's — attribute accordingly or skip it. The
  plain-language ledger picture carries the episode either way.
- **Raft mechanics beyond the quoted sentences.** "Leadership deselection" and quorum are
  quoted; anything more detailed about how Raft votes is textbook material, not incident
  material, and the general audience does not need it.
