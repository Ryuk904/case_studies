# EP05 — Roblox, 28–31 October 2021

## Verification of EP04's end-card promise (done first, as instructed)

EP04 speaks: *"a performance optimisation takes Roblox offline for 73 hours, in front of 50
million daily players."*

- **73 hours** — confirmed verbatim, twice: "Starting October 28th and fully resolving on
  October 31st, Roblox experienced a 73-hour outage." and "The outage lasted 73 hours."
- **50 million daily players** — confirmed: "Fifty million players regularly use Roblox
  every day". Note the source's phrasing is *regularly use every day*, not "daily active
  users" and **not concurrent**. Speak it as "fifty million people play Roblox every day".
- **"a performance optimisation"** — confirmed as the framing of the first root cause:
  "Enabling a relatively new streaming feature on Consul under unusually high read and
  write load led to excessive contention and poor performance", and the feature is
  "designed to significantly reduce the CPU and network bandwidth needed to distribute
  updates across large-scale clusters".

**The promise holds. Nothing needs to change in the spoken line.**

**The URL did not move.** `https://about.roblox.com/newsroom/2022/01/roblox-return-to-service-10-28-10-31-2021`
returned HTTP 200 with no redirect on 2026-08-12. Full plain-text copy in
`scratch/roblox_rts.txt`, HTML in `scratch/roblox_rts.html`.

### ⚠ One error in the kickoff brief — the direction of the second cause

The brief says: *"Underneath that, a BoltDB freelist **had grown** to nearly a million free
page IDs"* — which reads as a pre-existing time bomb waiting under the streaming feature.

The source says the opposite direction of causation:

> "Due to a specific usage pattern **created during the incident**, 16kB write operations
> were instead becoming much larger."

So the freelist bloat is presented as a **product of the incident's own conditions**, not a
dormant fault that the streaming feature happened to wake up. The two causes are
**sequential, not stacked**: streaming contention came first, the conditions it created
grew the freelist, and the freelist is why turning streaming off did not end the outage.

This matters for the script's whole spine, so it is flagged rather than quietly corrected.
Roblox does also say "Roblox's workload exposed a pathological performance issue in BoltDB"
— the *susceptibility* was always in BoltDB; the *million free pages* were not.

---

## Core hook & stake

On the afternoon of 28 October 2021, one server in Roblox's Consul cluster was running hot
and Vault was slow. Players were not affected yet. Seventy-three hours later, after four
separately-numbered wrong diagnoses, Roblox came back for all fifty million of its daily
players. Nothing was attacked and nothing was deployed badly. The trigger was a feature
switched on to make the system *cheaper* — Consul's new streaming mode, which cuts the CPU
and bandwidth needed to push updates around a large cluster, and which had been rolling out
successfully for months.

Consul is Roblox's service registry: the directory every one of hundreds of internal
services consults to find every other service, plus health checks, locking and a key-value
store. One cluster served all of it. When the directory is slow, nothing can find anything,
Nomad cannot schedule containers, Vault cannot hand out secrets, and a platform with 18,000
servers stops being a platform.

Underneath the contention sat a second fault that nobody found during the outage at all —
HashiCorp's engineers only worked it out *afterwards*. Consul stores its Raft log in
BoltDB, which never returns disk space: deleted pages are marked free and tracked in a
"freelist". Under the incident's usage pattern that freelist reached nearly a million page
IDs and 7.8 MB, and **the whole freelist was re-written on every single log append** — 7.8
megabytes of bookkeeping to record 16 kilobytes or less of actual data. A 4.2 GB log store
holding 489 MB of real data, 3.8 GB of it empty.

**The channel-level echo:** EP04's GitHub failed because an automated system did exactly
what it was configured to do. Roblox failed because a change that *worked* — measurably,
for months, exactly as designed — met a load shape nobody had benchmarked. And the reason
it took three days rather than three hours is the third thread: **the monitoring that would
have shown the cause was itself built on Consul.** They were debugging blind.

## The hard part, in plain language

Three pictures, and the script should not reach for a fourth.

**1. The one doorway.** The old way: every service walks up to the counter and asks "has
anything changed?", over and over. The new way: one announcer at one doorway calls out
every change as it happens. Fewer questions, less shouting, much cheaper — which is exactly
what it was bought for, and exactly what it delivered for months. Then a day comes when the
crowd is both asking and updating at full volume at the same time, and everything is
funnelled through that one doorway. Now nobody gets through, including the people who just
wanted to ask where something is.

**2. The warehouse that never shrinks.** Consul keeps a running diary of every change on
disk. To stop the diary growing forever it periodically takes a snapshot and deletes the
old pages — but the file never gets smaller. The emptied pages are just added to a list of
free shelves kept at the front. Normally that list is a few lines. Here it grew to nearly a
million lines. And the rule of this warehouse is that **before you put anything on a shelf,
you rewrite the entire list of empty shelves.** So delivering one small box means first
copying out a million-line inventory of nothing. The warehouse is 4.2 gigabytes of shelving
holding 489 megabytes of goods, and every delivery has to walk past all the air.

**3. The smoke detector wired into the building's power.** The dashboards and alerts that
would have shown what was wrong ran on the system that was down. Every time the team looked
for evidence, the instrument was part of the fault.

The through-line for the general audience: **the team was not slow or careless. They tried
four sensible things in order, and every one of them was reasonable, and every one of them
was wrong, because the fault was two levels below where anyone was looking and the
instruments were broken.**

## The four wrong answers (the source numbers these itself — this is the spine)

| # | Theory | What they did | Source's words |
|---|---|---|---|
| 1 | Bad hardware | replaced a Consul node | "the team suspected degraded hardware performance as the root cause… This was our first attempt at diagnosing the incident" |
| 2 | Too much traffic | replaced every node with 128-core machines and NVMe | "Perhaps Consul was slow because our system reached a tipping point… This was our second attempt" |
| 3 | Our own services are hammering it | reset from snapshot, blocked traffic with iptables, scaled services to single digits, health checks 60 s → 10 min | "Was the cluster simply getting pushed back into an unhealthy state by the sheer volume of thousands of containers trying to reconnect? This was our third attempt" |
| 4 | The bigger machines made it worse | went **back** to 64-core servers | "the team concluded that it was worth going back to 64 Core servers… This was our fourth attempt" |

Then the pivot that worked: stop looking at Consul from the outside, look at Consul's
insides — perf reports and flame graphs — and the streaming code paths show up as the
contention.

## Titles (final call at seo.md time; must extend the pattern)

| | EP01 | EP02 | EP03 | EP04 | EP05 |
|---|---|---|---|---|---|
| Title says | They forgot to delete some code | They did everything right | They deleted the wrong database | Nobody touched anything — the safety system did it | They made it faster, and it never came back up |
| Failure was | code nobody deleted | code everybody approved | safety nets nobody tested | a failover nobody could undo | an optimisation that worked |

1. **Curiosity / CTR:** Roblox Made One Thing Faster. It Was Offline for 73 Hours.
2. **Alternative:** The Optimisation That Took Roblox Down for Three Days
3. **Punchy (<25 chars):** 73 Hours Offline

## Thumbnail (concept only — one trimmed prompt goes in thumbnail_prompt.md)

Channel page so far: EP01 a lit object on a dark wall, EP02 a typographic line under a
slab, EP03 a row of objects with a count, EP04 a frame torn in two. **EP05 needs a fifth
kind of image, and the one this story owns is SCALE:** one tiny parcel beside a monstrous
tower of paperwork, both under the same loading light — the 16 kilobytes and the 7.8
megabytes that had to be written to deliver it. No earlier thumbnail is a size comparison,
and it is the single image that explains the episode. Text: "THEY MADE IT FASTER" /
"73 HOURS OFFLINE".

---

## PRIMARY SOURCE

**Roblox, "Roblox Return to Service 10/28-10/31 2021",** Roblox Newsroom / Engineering,
published 20 January 2022, by Roblox's SVP of Engineering "in collaboration with… many
others from Roblox and HashiCorp". Fetched in full and read end to end 2026-08-12;
plain-text copy in `scratch/roblox_rts.txt`.

**URL (verified live 2026-08-12, HTTP 200, no redirect):**
https://about.roblox.com/newsroom/2022/01/roblox-return-to-service-10-28-10-31-2021

This is the only primary source for the incident and it is sufficient: it is the company's
own engineering postmortem, written with the vendor whose software failed. No figure below
comes from anywhere else. HashiCorp published no standalone postmortem of this incident.

**All times in the report are Pacific Standard Time** — stated in the report's own footnote:
"Note all dates and time in this blog post are in Pacific Standard Time (PST)."

## SOURCES — the contract

Every number spoken in `script.md` has a row here with the verbatim sentence containing it.

| Claim | Verbatim |
|---|---|
| **73-hour outage, 28–31 October** | "Starting October 28th and fully resolving on October 31st, Roblox experienced a 73-hour outage." |
| **73 hours, again** | "The outage lasted 73 hours." |
| **50 million players a day** | "Fifty million players regularly use Roblox every day and, to create the experience our players expect, our scale involves hundreds of internal online services." |
| **The two root causes, in Roblox's own summary** | "The root cause was due to two issues. Enabling a relatively new streaming feature on Consul under unusually high read and write load led to excessive contention and poor performance. In addition, our particular load conditions triggered a pathological performance issue in BoltDB." |
| What BoltDB is doing in there | "The open source BoltDB system is used within Consul to manage write-ahead-logs for leader election and data replication." |
| **One cluster for everything made it worse** | "A single Consul cluster supporting multiple workloads exacerbated the impact of these issues." |
| **Why it took three days: diagnosis, not repair** | "Challenges in diagnosing these two primarily unrelated issues buried deep in the Consul implementation were largely responsible for the extended downtime." |
| **The monitoring depended on the broken thing** | "Critical monitoring systems that would have provided better visibility into the cause of the outage relied on affected systems, such as Consul. This combination severely hampered the triage process." |
| Bringing it back up was itself slow and deliberate | "We were thoughtful and careful in our approach to bringing Roblox up from an extended fully-down state, which also took notable time." |
| No data loss, no intrusion | "We would like to reiterate there was no user data loss or access by unauthorized parties of any information during the incident." |
| **The scale of the estate** | "The scale of our deployment is significant, with over 18,000 servers and 170,000 containers." |
| Roblox runs its own metal | "Roblox's core infrastructure runs in Roblox data centers. We deploy and manage our own hardware, as well as our own compute, storage, and networking systems on top of that hardware." |
| **What Consul is for** | "We use Consul for service discovery, health checks, session locking (for HA systems built on-top), and as a KV store." |
| What service discovery means | "Roblox services use the Service Registry to find one another so they can communicate. This process is called 'service discovery.'" |
| **5 voters, 5 non-voters** | "Consul is deployed as a cluster of machines in two roles. 'Voters' (5 machines) authoritatively hold the state of the cluster; 'Non-voters' (5 additional machines) are read-only replicas that assist with scaling read requests." |
| Leaders change often, and that is normal | "It is not uncommon for the leader to change via leader election several times throughout a given day." |
| **Healthy KV Apply time is under 300 ms** | "KV Apply time for instance is considered normal at less than 300ms and is 30.6ms in this moment." |
| **The upgrade, and what streaming was bought for** | "In the months leading up to the October incident, Roblox upgraded from Consul 1.9 to Consul 1.10 to take advantage of a new streaming feature. This streaming feature is designed to significantly reduce the CPU and network bandwidth needed to distribute updates across large-scale clusters like the one at Roblox." |
| **First symptom, 13:37 on 28 October — players fine** | "On the afternoon of October 28th, Vault performance was degraded and a single Consul server had high CPU load. Roblox engineers began to investigate. At this point players were not impacted." (section heading: Initial Detection (10/28 13:37)) |
| **Write latency: normally under 300 ms, now 2 seconds** | "The 50th percentile latency on these operations was typically under 300ms but was now 2 seconds." |
| **Wrong answer #1: bad hardware** | "In this case, the team suspected degraded hardware performance as the root cause and began the process of replacing one of the Consul cluster nodes. This was our first attempt at diagnosing the incident." |
| HashiCorp joins | "Around this time, staff from HashiCorp joined Roblox engineers to help with diagnosis and remediation." |
| **16:35 — half the players gone** | "Even with new hardware, Consul cluster performance continued to suffer. At 16:35, the number of online players dropped to 50% of normal." |
| **Why a slow directory is a dead platform** | "When a Roblox service wants to talk to another service, it relies on Consul to have up-to-date knowledge of the location of the service it wants to talk to. However, if Consul is unhealthy, servers struggle to connect." |
| Nomad and Vault fall with it | "Furthermore, Nomad and Vault rely on Consul, so when Consul is unhealthy, the system cannot schedule new containers or retrieve production secrets used for authentication." |
| **The single point of failure, named** | "In short, the system failed because Consul was a single point of failure, and Consul was not healthy." |
| **Wrong answer #2: not enough machine** | "Perhaps Consul was slow because our system reached a tipping point, and the servers on which Consul was running could no longer handle the load? This was our second attempt at diagnosing the root cause of the incident." |
| **Doubling the cores did not help** | "These new machines had 128 cores (a 2x increase) and newer, faster NVME SSD disks. By 19:00, the team migrated most of the cluster to the new machines but the cluster was still not healthy." |
| Still 2 seconds | "The cluster was reporting that a majority of nodes were not able to keep up with writes, and the 50th percentile latency on KV writes was still around 2 seconds rather than the typical 300ms or less." |
| The inexplicable symptom | "We could still see elevated KV write latency as well as a new inexplicable symptom that we could not explain: the Consul leader was regularly out of sync with the other voters." |
| **Wiping the cluster's state** | "The team decided to shut down the entire Consul cluster and reset its state using a snapshot from a few hours before – the beginning of the outage." |
| What they knowingly risked | "We understood that this would potentially incur a small amount of system config data loss (not user data loss)." |
| Even with no players, the system talks to itself | "Even though Roblox did not have any user-generated traffic flowing through the system at this point, internal Roblox services were still live and dutifully reaching out to Consul to learn the location of their dependencies and to update their health information. These reads and writes were generating a significant load on the cluster." |
| They walled it off to find out | "To address this concern, we configured iptables on the cluster to block access." |
| **The reset worked, then unwound** | "The reset went smoothly, and initially, the metrics looked good… However, Consul performance began to degrade again, and eventually we were back to where we started: 50th percentile on KV write operations was back at 2 seconds." |
| **14 hours in, still nothing** | "It was now 04:00. There was clearly something about our load on Consul that was causing problems, and over 14 hours into the incident, we still didn't know what it was." |
| **Wrong answer #3: our own services** | "Was the cluster simply getting pushed back into an unhealthy state by the sheer volume of thousands of containers trying to reconnect? This was our third attempt at diagnosing the root cause of the incident." |
| **Turning Roblox down to almost nothing** | "Roblox services that typically had hundreds of instances running were scaled down to single digits. Health check frequency was decreased from 60 seconds to 10 minutes to give the cluster additional breathing room." |
| **24 hours in, second attempt to come back — and it fails too** | "At 16:00 on Oct 29th, over 24 hours after the start of the outage, the team began its second attempt to bring Roblox back online. Once again, the initial phase of this restart attempt looked good, but by 02:00 on Oct 30th, Consul was again in an unhealthy state, this time with significantly less load from the Roblox services that depend on it." |
| **The pivot: stop looking from outside** | "Instead of looking at Consul from the perspective of the Roblox services that depend on it, the team started looking at Consul internals for clues." |
| **What they found: contention** | "This data showed Consul KV writes getting blocked for long periods of time. In other words, 'contention.'" |
| **Wrong answer #4: undo the big machines** | "The team then transitioned the Consul cluster back to 64 CPU Core servers, but this change did not help. This was our fourth attempt at diagnosing the root cause of the incident." |
| Where the CPU was actually going | "The majority of time was spent in kernel spin locks via the Streaming subscription code path." |
| **The rollout that preceded it: 27 October, 14:00** | "On October 27th at 14:00, one day before the outage, we enabled this feature on a backend service that is responsible for traffic routing. As part of this rollout, in order to prepare for the increased traffic we typically see at the end of the year, we also increased the number of nodes supporting traffic routing by 50%." |
| **It had worked fine for a whole day** | "The system had worked well with streaming at this level for a day before the incident started, so it wasn't initially clear why it's performance had changed." |
| **The breakthrough: 15:51 on 30 October** | "We disabled the streaming feature for all Consul systems, including the traffic routing nodes. The config change finished propagating at 15:51, at which time the 50th percentile for Consul KV writes lowered to 300ms. We finally had a breakthrough." |
| **Why streaming was the problem** | "HashiCorp explained that, while streaming was overall more efficient, it used fewer concurrency control elements (Go channels) in its implementation than long polling. Under very high load – specifically, both a very high read load and a very high write load – the design of streaming exacerbates the amount of contention on a single Go channel, which causes blocking during writes, making it significantly less efficient." |
| **Why the faster machines made it worse** | "This behavior also explained the effect of higher core-count servers: those servers were dual socket architectures with a NUMA memory model. The additional contention on shared resources thus got worse under this architecture." |
| **The breakthrough was not the end** | "Despite the breakthrough, we were not yet out of the woods. We saw Consul intermittently electing new cluster leaders, which was normal, but we also saw some leaders exhibiting the same latency problems we saw before we disabled streaming, which was not normal." |
| **The workaround they shipped instead of a fix** | "the team made the pragmatic decision to work around the problem by preventing the problematic leaders from staying elected." |
| **Nobody solved cause two during the outage** | "But what was going on with the slow leaders? We did not figure this out during the incident, but HashiCorp engineers determined the root cause in the days after the outage." |
| What BoltDB stores | "Consul uses a popular open-source persistence library named BoltDB to store Raft logs. It is not used to store the current state within Consul, but rather a rolling log of the operations being applied." |
| Snapshots keep the log bounded | "To prevent BoltDB from growing indefinitely, Consul regularly performs snapshots. The snapshot operation writes the current state of Consul to disk and then deletes the oldest log entries from BoltDB." |
| **The file never shrinks** | "However, due to the design of BoltDB, even when the oldest log entries are deleted, the space BoltDB uses on disk never shrinks. Instead, all the pages (4kb segments within the file) that were used to store deleted data are instead marked as 'free' and re-used for subsequent writes. BoltDB tracks these free pages in a structure called its 'freelist.'" |
| **Normally free, here fatal** | "Typically, write latency is not meaningfully impacted by the time it takes to update the freelist, but Roblox's workload exposed a pathological performance issue in BoltDB that made freelist maintenance extremely expensive." |
| **Caused during the incident, not before it** | "Due to a specific usage pattern created during the incident, 16kB write operations were instead becoming much larger." |
| **4.2 GB holding 489 MB** | "This 4.2GB log store is only storing 489MB of actual data (including all the index internals)." |
| **3.8 GB of nothing** | "3.8GB is 'empty' space." |
| **7.8 MB, nearly a million free pages** | "The freelist is 7.8MB since it contains nearly a million free page ids." |
| **THE SENTENCE — 7.8 MB written to store 16 kB** | "That means, for every log append (each Raft write after some batching), a new 7.8MB freelist was also being written out to disk even though the actual raw data being appended was 16kB or less." |
| Back pressure, 2–3 second writes | "Back pressure on these operations also created full TCP buffers and contributed to 2-3s write times on unhealthy leaders." |
| The eventual repair | "HashiCorp and Roblox have developed and deployed a process using existing BoltDB tooling to 'compact' the database, which resolved the performance issues." |
| **54 hours in, Consul is finally stable** | "It had been 54 hours since the start of the outage. With streaming disabled and a process in place to prevent slow leaders from staying elected, Consul was now consistently stable." |
| The caching layer's scale | "the caching system, which regularly handles 1B requests-per-second across its multiple layers during regular system operation, was unhealthy." |
| The databases were never the problem | "These databases were unaffected by the outage, but the caching system… was unhealthy." |
| The snapshot reset came back to bite | "Likely due to the Consul cluster snapshot reset that had been performed earlier on, internal scheduling data that the cache system stores in the Consul KV were incorrect." |
| One sick node ate the deployments | "It turned out that there was an unhealthy node that the job scheduler saw as completely open rather than unhealthy. This resulted in the job scheduler attempting to aggressively schedule cache jobs on this node, which failed because the node was unhealthy." |
| **The tool was built for a running system, not a dead one** | "The caching system's automated deployment tool was built to support incremental adjustments to large scale deployments that were already handling traffic at scale, not iterative attempts to bootstrap a large cluster from scratch." |
| **61 hours in, ready to bring Roblox back** | "At 05:00 on October 31, 61 hours since the start of the outage, we had a healthy Consul cluster and a healthy caching system. We were ready to bring up the rest of Roblox." |
| **Letting players back a slice at a time** | "To avoid a flood, we used DNS steering to manage the number of players who could access Roblox. This allowed us to let in a certain percentage of randomly selected players while others continued to be redirected to our static maintenance page." |
| Ratcheting up in 10% steps | "Every time we increased the percentage, we checked database load, cache performance, and overall system stability. Work continued throughout the day, ratcheting up access in roughly 10% increments." |
| The players who cracked the scheme | "We enjoyed seeing some of our most dedicated players figure out our DNS steering scheme and start exchanging this information on Twitter so that they could get 'early' access as we brought the service back up." |
| **The end: 16:45, Sunday 31 October** | "At 16:45 Sunday, 73 hours after the start of the outage, 100% of players were given access and Roblox was fully operational." |
| **Why HashiCorp had never seen it** | "While HashiCorp had benchmarked streaming at similar scale to Roblox usage, they had not observed this specific behavior before due to it manifesting from a combination of both a large number of streams and a high churn rate." |
| **THE FIX THAT IS THE TAKEAWAY** | "There was a circular dependency between our telemetry systems and Consul, which meant that when Consul was unhealthy, we lacked the telemetry data that would have made it easier for us to figure out what was wrong. We have removed this circular dependency. Our telemetry systems no longer depend on the systems that they are configured to monitor." |
| One cluster for everything, named as the exposure | "Running all Roblox backend services on one Consul cluster left us exposed to an outage of this nature." |
| They replaced BoltDB | "We are working closely with HashiCorp to deploy a new version of Consul that replaces BoltDB with a successor called bbolt that does not have the same issue with unbounded freelist growth." |
| They chose to postpone the upgrade | "We intentionally postponed this effort into the new year to avoid a complex upgrade during our peak end-of-year traffic." |
| **They intend to switch streaming back on** | "We originally deployed streaming to lower the CPU usage and network bandwidth of the Consul cluster. Once a new implementation has been tested at our scale with our workload, we expect to carefully reintroduce it to our systems." |
| Why the postmortem took 2.5 months | "It has been 2.5 months since the outage… while we could have issued a post sooner to explain what happened, we felt we owed it to you, our community, to make significant progress on improving the reliability of our systems before publishing." |
| The December surge held | "Roblox did not have a single significant production incident during the December surge, and that the performance and stability of both Consul and Nomad during this surge were excellent." |
| Taking responsibility | "Another one of our Roblox values is Take Responsibility, and we take full responsibility for what happened here." |
| **Nobody turned on each other** | "At some point during a 73-hour outage, with the clock ticking and the stress building, it wouldn't be surprising to see someone lose their cool, say something disrespectful, or wonder aloud whose fault this all was. But that's not what happened." |

### Derived, not quoted — and flagged as such

| Spoken as | Arithmetic |
|---|---|
| "nearly five hundred times more bookkeeping than data" | 7.8 MB ÷ 16 kB ≈ 487. The source says the appended data was "16kB **or less**", so the true ratio is *at least* this. Speak "nearly five hundred times", never a precise multiple. |
| "almost nine tenths of that file was empty" | 3.8 GB of 4.2 GB is 90.5%; the source states both figures and states "3.8GB is 'empty' space". Prefer speaking the two figures over the fraction. |
| "three days" | 73 hours = 3 days 1 hour. "Three days" is a fair rounding; the episode speaks the exact 73 hours at least once. |
| "a day and a half before they even looked inside Consul" | 13:37 on the 28th → the internals pivot at 02:00 on the 30th ≈ 36 hours. Keep qualitative unless the timeline is on screen. |
| "four wrong answers" | The source itself numbers first/second/third/fourth attempt at diagnosis. Not our count. |
| "the write got seven times slower" | "typically under 300ms but was now 2 seconds" — 2000 ÷ 300 ≈ 6.7, but "under 300ms" is a ceiling, so the real multiple is larger and unknown. **Speak the two numbers, never the ratio.** |
| "half the players were gone within three hours" | 13:37 detection → 16:35 CCU at 50% is 2h58m. Both are stated; the subtraction is ours. Safe, but say "within three hours", not "in 178 minutes". |

## ⚠ Contradictions and tensions inside the primary source — handled, not hidden

- **The 73-hour clock has three different start times inside the same document.** The
  elapsed-time markers do not reconcile: "54 hours" at 10/30 20:00 implies a start of
  14:00; "61 hours" at 10/31 05:00 implies 16:00; "73 hours" at 10/31 16:45 implies 15:45.
  Detection is stated as 13:37. **Handling: speak "73 hours" as Roblox's own headline
  figure and speak the timestamps as timestamps. Never perform the subtraction on screen,
  and never state a clock time for "the start of the outage".**
- **"The outage lasted 73 hours" vs "at this point players were not impacted."** The
  73-hour clock evidently starts somewhere in the mid-afternoon of the 28th, but the
  first players only lost service at 16:35. Handling: the episode says the first symptom
  appeared on the afternoon of the 28th and half the players were gone within three hours.
- **The trigger is not "they flipped a switch".** Streaming had been rolling out for
  months and had run on the traffic-routing service for a full day before anything broke:
  "The system had worked well with streaming at this level for a day before the incident
  started." Roblox never states what tipped it on the 28th. **The script must not say the
  rollout caused it immediately** — that is the most tempting simplification available and
  it is not what the source says.
- **Cause two: created during the incident, or exposed by it?** Both framings appear.
  "a specific usage pattern created during the incident" (created) versus "Roblox's
  workload exposed a pathological performance issue in BoltDB" (exposed). These reconcile
  as susceptibility-versus-trigger, and the script should say it that way: BoltDB was
  always built to behave like this; the incident's conditions are what made it matter.
- **"Faster hardware… potentially hurt stability."** Hedged in the source ("as we learned
  later, potentially hurt"), then explained mechanically later ("dual socket architectures
  with a NUMA memory model. The additional contention on shared resources thus got worse").
  Attribute it: the report says the bigger machines likely made it worse.
- **Two different "second attempts".** The document has "our second attempt at diagnosing
  the root cause" (the hardware-capacity theory) and, separately, "the team began its
  second attempt to bring Roblox back online" (16:00 on the 29th). Diagnosis attempts and
  return-to-service attempts are numbered on separate clocks. Do not merge them.

## Next-episode tease (spoken on the end card) — EP06

**Recommendation: CrowdStrike, 19 July 2024 — not Meta's BGP withdrawal.** The reason is
purely the sourcing rule, and it is decisive.

**Meta, checked first because it was the suggestion.** Both of Meta's own posts were
fetched in full and read (`scratch/meta_outage.txt`, `scratch/meta_outage_details.txt`;
both URLs live 2026-08-12, HTTP 200):

- https://engineering.fb.com/2021/10/04/networking-traffic/outage/
- https://engineering.fb.com/2021/10/05/networking-traffic/outage-details/

They contain **no duration, no user count, and no dollar figure** — there is not a single
number in either post that an end card could speak. Worse, the detail the kickoff calls "a
gift", staff unable to badge into their own buildings, **does not appear in either source.**
The nearest sentence is "these facilities are designed with high levels of physical and
system security in mind. They're hard to get into" — which is about the difficulty of
working on hardened routers, not about badge readers failing. The badge story is press
reporting, and §4 forbids sourcing it that way. Meta stays on the bench; if it is ever
taken, its stake has to be built from a third party's *observations* (Cloudflare's own
1.1.1.1 write-up), which is a different and weaker kind of episode.

**CrowdStrike, verified live 2026-08-12, two primary sources, both with hard numbers:**

| Claim | Source | Verbatim |
|---|---|---|
| The update went out at 04:09 UTC and was pulled at 05:27 UTC — 78 minutes | CrowdStrike, "Technical Details: Falcon Content Update for Windows Hosts", https://www.crowdstrike.com/en-us/blog/falcon-update-for-windows-hosts-technical-details/ | "On July 19, 2024 at 04:09 UTC, as part of ongoing operations, CrowdStrike released a sensor configuration update to Windows systems." / "The sensor configuration update that caused the system crash was remediated on Friday, July 19, 2024 05:27 UTC." |
| 8.5 million Windows devices | Microsoft, "Helping our customers through the CrowdStrike outage", https://blogs.microsoft.com/blog/2024/07/20/helping-our-customers-through-the-crowdstrike-outage/ | "We currently estimate that CrowdStrike's update affected 8.5 million Windows devices, or less than one percent of all Windows machines." |

Proposed end-card line: *"a security update that was live for 78 minutes crashes 8.5
million computers, and most of them cannot be fixed remotely."* The 78 minutes is our
subtraction of two stated timestamps and is flagged as derived; both timestamps are
spoken-safe on their own. The final clause needs one more verbatim row from CrowdStrike's
remediation guidance before it is spoken — **flagged as outstanding.**

It also rhymes with this episode better than Meta does: a change that was routine,
well-tested and working, distributed to everyone at once.

**If you would rather have Meta or AWS S3 2017, say so and the tease is rewritten** — but
Meta's end card cannot carry a number, which no episode's end card has had to do yet.

## Photography — free-licence, generic, never evidence

Same three rules as EP04: illustration and never evidence, CC0/PD/CC BY only (no
share-alike, no non-commercial), and **any CC BY plate used must be credited in `seo.md`'s
description block, which is the licence condition and not a courtesy.** No photo is
presented as a Roblox facility, and nothing is staged as a screenshot, dashboard or
document.

Five plates added to `photo.MANIFEST` and fetched 2026-08-12. **Every one came back CC BY
2.0, so all five must be credited in `seo.md`** — this episode has a longer credit block
than EP04's two-line one, and removing it breaks the licence.

| Plate | For | Licence | Creator | Source |
|---|---|---|---|---|
| `warehouse` | the warehouse that never shrinks — the freelist scene | CC BY 2.0 | nSeika | https://www.flickr.com/photos/33542052@N07/8096899965 |
| `archive_papers` | the million-line inventory of empty shelves | CC BY 2.0 | FeatheredTar | https://www.flickr.com/photos/55915190@N00/2302651444 |
| `crowd_queue` | fifty million players outside a closed door | CC BY 2.0 | Mark Hodson Photos | https://www.flickr.com/photos/20538653@N00/3388029136 |
| `turnstile` | the one doorway everything is funnelled through | CC BY 2.0 | ell brown | https://www.flickr.com/photos/39415781@N06/4388675372 |
| `arcade` | a lit play space at night — the platform with nobody in it | CC BY 2.0 | Dominic's pics | https://www.flickr.com/photos/64097751@N00/1128788988 |

Two were re-queried after the first fetch returned unusable subjects: `archive_papers`
first came back as an **architectural blueprint**, which is both wrong for the beat and
close enough to "a document on screen" to be a §4 risk, and `warehouse` first came back as
an office stationery cupboard. Both were re-fetched and checked on a contact strip
(`scratch/ep05_plates2.png`) rather than accepted from the search result's title.

Existing plates that genuinely fit: `server_room` (the cluster and the hardware swaps),
`office_night` and `control_room` (the three nights of triage), `sunrise_city` (the 31st,
letting players back in).

**Fixed while here:** `photo.MANIFEST` had `"server_aisle"` as a duplicate key, so the
first query was silently discarded by the dict literal and the plate had never fetched.
De-duplicated; it still returns no usable result and no scene depends on it.

## ⚠ Unverified — do not use

- **Any dollar cost, revenue figure, share-price move or refund total.** None appears in
  the source. Press coverage has numbers; they are not usable here.
- **Concurrent player counts.** "Fifty million players regularly use Roblox every day" is a
  daily figure. The CCU chart is referenced as an image ("2. CCU during the 16:35 PST
  Player Drop") and its axis values are not in the text. Never say "50 million players were
  online".
- **The location of any Roblox data centre.** The source says only "Roblox data centers"
  and "multiple sites". No city, no state.
- **Any individual's name or role in the failure.** The post is bylined, and it names
  colleagues in thanks. Nobody is named as having done anything wrong, and per HOUSE_STYLE
  §1 nobody gets named at all. "The team" throughout.
- **The literal command output in the BoltDB screenshots.** The report shows images
  ("6. Detailed BoldDB statistics used in analysis") whose text is not in the page's
  markup. The *figures* are stated in prose and are usable; the *command line* that
  produced them is not, so **no terminal frame may show a command here** — the `code`
  renderer's prompt dressing is fine, an invented `bolt stats` line is not (HOUSE_STYLE
  §12).
- **Which service the traffic-routing backend actually is.** Only "a backend service that
  is responsible for traffic routing".
- **How many services, clusters or Consul instances Roblox runs.** "Hundreds of internal
  online services" and "a single Consul cluster" are the only counts. No total.
- **Attributing blame to HashiCorp or calling BoltDB "buggy".** The source's framing is
  that streaming was "overall more efficient" and that HashiCorp had benchmarked it at
  similar scale without seeing this. Use the source's framing.
- **"Split brain", "thundering herd", "write amplification" and similar labels.** None
  appears in the source, and all three are jargon this audience does not have. If any is
  spoken it is our word, and the plain-language picture carries the episode without them.
- **What tipped the system on 28 October.** The source does not say. Do not invent a
  trigger, and do not imply the 27 October rollout caused it the same day — it explicitly
  ran fine for a day.
- **The 73-hour clock's start time.** See the contradictions section: three different
  values are implied. Never speak one.
