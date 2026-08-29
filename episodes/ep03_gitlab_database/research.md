# EP03 — GitLab, 31 January 2017

## Core hook & stake

At around 11pm UTC on 31 January 2017, an engineer at GitLab — five hours into fighting a
spam attack, an hour after telling the team he was going to sign off for the night — tried
to wipe the data directory of a broken spare database server so it could be rebuilt. He ran
the wipe on `db1.cluster.gitlab.com`, the live production server, instead of
`db2.cluster.gitlab.com`, the spare. He noticed within a second or two; by then around
300 GB of GitLab.com's production database was gone, with about 4.5 GB left.

Then the company went looking for its backups. Their own live notes, written that night,
end the search with one sentence: *"So in other words, out of five backup/replication
techniques deployed none are working reliably or set up in the first place."* The daily
export had been silently producing near-empty files for an unknown time because the backup
tool was one major version older than the database. The warning emails about those failures
were being rejected by the receiving mail server for a missing DMARC signature, so nobody
ever saw one. The cloud storage bucket the exports went to was empty. The hosting
provider's disk snapshots had never been enabled for the database servers. And the spare —
the failover of last resort — had been wiped by the repair attempt an hour earlier.

What saved them was not a backup at all. At 17:20 that afternoon, the same engineer had
taken a manual snapshot of production for an unrelated load-balancing experiment — roughly
six hours before the deletion. Restoring from it took about 18 hours, because staging ran
on the cheapest storage tier, throttled to about 60 Mbps. GitLab.com was down for about
18 hours; roughly 5,000 projects, 5,000 comments and 700 new user accounts — everything
after that snapshot — were lost for good. Git repositories were stored separately and
survived untouched.

They streamed the entire recovery live on YouTube — peak of about 5,000 viewers, the #2
live stream on the platform for several hours — and kept their incident notes in a public
Google Doc while it happened.

## Why this episode works

It completes a triptych. Knight was code nobody deleted; Cloudflare was code everybody
approved; GitLab is the safety net nobody tested. The mistake is thirty seconds of the
story — the other five layers had been broken for weeks or forever, silently, and the
episode's engine is crossing them off one at a time. The twist (the only surviving copy was
an accident, made by the same person who deleted the data, for an unrelated reason) is the
kind of reversal that cannot be invented.

The postmortem's own root-cause answer for "why was the backup procedure not tested?" is
one word long — ownership — which hands the takeaway a Monday decision on a plate.

Two open loops, planted early and paid off late:

1. **Five safety nets.** Planted in the hook, paid off net by net through the back half of
   the breakdown.
2. **The accidental copy.** "The only copy left is one that nobody planned to make" at
   0:40; who made it and why lands at ~6:00, after all five nets have failed.

## Titles

1. **Search-optimised:** The GitLab Database Incident: Five Backups, None of Them Worked
2. **Curiosity / CTR:** They Deleted the Wrong Database. Then All Five Backups Failed.
3. **Punchy (<25 chars):** Five Backups. Zero Worked.

See `seo.md` for the shipping title and why.

⚠ **The count is five, not four.** `TOPICS.md` and EP02's end card both say "all four
backups had failed". The live incident doc's exact sentence is *"out of five
backup/replication techniques deployed"*. See the contradiction section below for where
"four" came from.

## Thumbnail

- **Text overlay:** `0 OF 5` / `BACKUPS WORKED`
- **Visual subject:** five sketch hard-drives in a row, each stamped with a red cross, a
  single glowing terminal cursor beneath. See `thumbnail_prompt.md`.

---

## PRIMARY SOURCES

**1. GitLab, "Postmortem of database outage of January 31",** The GitLab Blog, 10 February
2017. Fetched in full 2026-08-07 and read end to end (plain-text copy in
`scratch/gitlab_postmortem.txt`). URL verified live, no redirect:
https://about.gitlab.com/blog/2017/02/10/postmortem-of-database-outage-of-january-31/

The company's own postmortem, published ten days after the incident, signed off by the CEO
in the first person ("I apologize personally, as GitLab's CEO").

**2. GitLab, "GitLab.com database incident",** The GitLab Blog, 1 February 2017 — the
company's republication of the live incident notes, posted *while the recovery was still
running*. Fetched in full 2026-08-07 (plain-text copy in `scratch/gitlab_incident_blog.txt`):
https://about.gitlab.com/blog/2017/02/01/gitlab-dot-com-database-incident/

⚠ The original public Google Doc ("GitLab.com Database Incident — 2017/01/31",
`docs.google.com/document/d/1GCK53YDcBWQveod9kfzW-VCxIABGiryG7_z_6jHdVik/pub`) now returns
**410 Gone**. The blog post above is the canonical surviving copy of those notes and is
what this ledger cites as "incident notes".

## SOURCES — the contract

Every number spoken in `script.md` has a row here with the verbatim sentence containing it.

| Claim | Source | Verbatim |
|---|---|---|
| **The five backup techniques, none working** | incident notes | "So in other words, out of five backup/replication techniques deployed none are working reliably or set up in the first place. We ended up restoring a six-hour-old backup." |
| **~300 GB removed** | CF-style primary: postmortem | "The engineer terminated the process a second or two after noticing their mistake, but at this point around 300 GB of data had already been removed." |
| **About 4.5 GB left, terminated 11:27pm UTC** | incident notes | "At 2017/01/31 11:27pm UTC, team-member-1 - terminates the removal, but it's too late. Of around 300 GB only about 4.5 GB is left." |
| **Wrong server: primary, not secondary** | postmortem | "Trying to restore the replication process, an engineer proceeds to wipe the PostgreSQL database directory, errantly thinking they were doing so on the secondary. Unfortunately this process was executed on the primary instead." |
| Noticed after a second or two | incident notes | "After a second or two he notices he ran it on db1.cluster.gitlab.com, instead of db2.cluster.gitlab.com." |
| **The two hostnames, one character apart** | postmortem | "The primary's hostname is db1.cluster.gitlab.com, while the secondary's hostname is db2.cluster.gitlab.com." |
| The deleted directory's path | incident notes | "db2.cluster refuses to replicate, /var/opt/gitlab/postgresql/data is wiped to ensure a clean replication" |
| One primary, one spare, spare only for failover | postmortem | "GitLab.com currently uses a single primary and a single secondary in hot-standby mode. The standby is only used for failover purposes." |
| **Spam attack detected at 6pm UTC** | incident notes | "At 2017/01/31 6pm UTC, we detected that spammers were hammering the database by creating snippets, making it unstable." |
| Escalation at 9pm, write lockup | incident notes | "At 2017/01/31 9pm UTC, this escalated, causing a lockup on writes on the database, which caused some downtime." |
| **47,000 addresses signing in as one account** | incident notes | "We removed a user for using a repository as some form of CDN, resulting in 47 000 IPs signing in using the same account (causing high DB load)" |
| A background job was deleting one of their own employees | postmortem | "We would later find out that part of the load was caused by a background job trying to remove a GitLab employee and their associated data. This was the result of their account being flagged for abuse and accidentally scheduled for removal." |
| …because a troll reported them | postmortem (5 Whys) | "The employee was reported for abuse by a troll." |
| **Paged at 10pm: replication stopped** | incident notes | "At 2017/01/31 10pm UTC, we got paged because DB Replication lagged too far behind, effectively stopping." |
| Why replication broke | postmortem | "The replication failed as WAL segments needed by the secondary were already removed from the primary." |
| Fixing the spare requires wiping it first | postmortem | "This involves removing the existing data directory on the secondary, and running pg_basebackup to copy over the database from the primary to the secondary." |
| He wiped the spare and started the copy | postmortem | "One of the engineers went to the secondary and wiped the data directory, then ran pg_basebackup." |
| The copy tool hung, silently | postmortem | "Unfortunately pg_basebackup would hang, producing no meaningful output, despite the --verbose option being set." |
| **It waits silently, up to 10 minutes** | incident notes | "pg_basebackup will silently wait for a master to initiate the replication progress, according to another production engineer this can take up to 10 minutes." |
| …and that behaviour was not documented | postmortem | "Unfortunately this was not clearly documented in our engineering runbooks nor in the official pg_basebackup document." |
| **He had meant to sign off around 11pm local** | incident notes | "Earlier this night team-member-1 explicitly mentioned he was going to sign off as it was getting late (23:00 or so local time), but didn't due to the replication problems popping up all of a sudden." |
| The deletion happened around 11pm UTC | incident notes | "At 2017/01/31 11pm-ish UTC, team-member-1 thinks that perhaps pg_basebackup is refusing to work due to the PostgreSQL data directory being present (despite being empty), decides to remove the directory." |
| **Net 1 — daily export produced near-empty files** | incident notes | "According to team-member-2 these don't appear to be working, producing files only a few bytes in size." |
| …because of a version mismatch, failing silently | postmortem | "Upon closer inspection we found out that the backup procedure was using pg_dump 9.2, while our database is running PostgreSQL 9.6 (for Postgres, 9.x releases are considered major). A difference in major versions results in pg_dump producing an error, terminating the backup procedure." |
| **Net 1a — the warning emails were thrown away** | postmortem | "Unfortunately DMARC was not enabled for the cronjob emails, resulting in them being rejected by the receiver. This means we were never aware of the backups failing, until it was too late." |
| **Net 2 — the cloud bucket was empty** | postmortem | "When we went to look for the pg_dump backups we found out they were not there. The S3 bucket was empty, and there was no recent backup to be found anywhere." |
| **Net 3 — provider disk snapshots never enabled for the databases** | postmortem | "While enabled for the NFS servers, these snapshots were not enabled for any of the database servers as we assumed that our other backup procedures were sufficient enough." |
| **Net 4 — the staging sync strips data as it copies** | incident notes | "The synchronisation process removes webhooks once it has synchronised data to staging." |
| **Net 5 — replication itself** | postmortem (5 Whys) | "Why could we not fail over to the secondary database host? - The secondary database's data was wiped as part of restoring database replication. As such it could not be used for disaster recovery." |
| …and it was fragile anyway | incident notes | "The replication procedure is super fragile, prone to error, relies on a handful of random shell scripts, and is badly documented" |
| Backups only every 24 hours | postmortem | "Every 24 hours a backup is generated using pg_dump, this backup is uploaded to Amazon S3." |
| Snapshots only every 24 hours | postmortem | "This procedure normally happens automatically once every 24 hours (at 01:00 UTC), but they wanted a more up to date copy of the database." |
| **The saving snapshot: manual, ~6 hours old** | postmortem | "A snapshot created manually by one of the engineers roughly 6 hours before the outage." |
| …taken by the same engineer, for load balancing | incident notes | "LVM snapshots are by default only taken once every 24 hours. Team-member-1 happened to run one manually about six hours prior to the outage because he was working in load balancing for the database." |
| …at 17:20 UTC, loaded into staging | postmortem | "± 17:20 UTC: prior to starting this work, our engineer took an LVM snapshot of the production database and loaded this into the staging environment." |
| The alternative was losing almost 24 hours | postmortem | "To recover GitLab.com we decided to use the LVM snapshot created 6 hours before the outage, as it was our only option to reduce data loss as much as possible (the alternative was to lose almost 24 hours of data)." |
| **The copy back took ~18 hours** | postmortem | "Copying the data from the staging to the production host took around 18 hours." |
| …because staging ran on slow throttled disks | postmortem | "These disks are network disks and are throttled to a really low number (around 60Mbps), there is no way to move from cheap storage to premium, so this was the performance we would get out of it." |
| …chosen to save money | postmortem | "For our staging environment we were using Azure classic, without Premium Storage. This is primarily done to save costs as premium storage is quite expensive." |
| **GitLab.com was down about 18 hours** | postmortem (5 Whys) | "Problem 1: GitLab.com was down for about 18 hours." |
| **Lost: ~5,000 projects, ~5,000 comments, ~700 accounts** | postmortem | "Our best estimate is that it affected roughly 5,000 projects, 5,000 comments and 700 new user accounts." |
| Git repositories survived | postmortem | "Code repositories or wikis hosted on GitLab.com were unavailable during the outage, but were not affected by the data loss." |
| **They streamed the recovery: ~5,000 peak viewers, #2 on YouTube** | postmortem | "We also streamed the recovery procedure on YouTube, with a peak viewer count of around 5000 (resulting in the stream being the #2 live stream on YouTube for several hours)." |
| The notes were public while it happened | postmortem | "In the spirit of transparency we kept track of progress and notes in a publicly visible Google document." |
| Database restored 17:00 UTC Feb 1, done ~18:00 | postmortem | "On February 1st at 17:00 UTC we managed to restore the GitLab.com database without webhooks." / "Around 18:00 UTC we finished the final restoration procedures such as restoring the webhooks and confirming everything was operating as expected." |
| **Root cause of untested backups: no ownership** | postmortem (5 Whys) | "Why was the backup procedure not tested on a regular basis? - Because there was no ownership, as a result nobody was responsible for testing this procedure." |
| The fix list includes an owner | postmortem | "Assign an owner for data durability" |
| Snapshots moved to hourly afterwards | postmortem | "Fear not however, as LVM snapshots are now taken every hour instead of once per 24 hours." |
| The CEO's apology | postmortem | "To the GitLab.com users whose data we lost and to the people affected by the outage: we're sorry. I apologize personally, as GitLab's CEO, and on behalf of everyone at GitLab." |
| "Losing production data is unacceptable" | postmortem | "Losing production data is unacceptable. To ensure this does not happen again we're working on multiple improvements to our operations & recovery procedures for GitLab.com." |

### Derived, not quoted — and flagged as such

| Spoken as | Arithmetic |
|---|---|
| "five hours into fighting a spam attack" | 6pm UTC spam detected → ~11pm UTC deletion |
| "an hour or so after he meant to log off" | "sign off … (23:00 or so local time)" → deletion at "11pm-ish UTC"; his local clock was ahead of UTC, so the deletion came at least an hour after the intended sign-off. Kept vague ("he had already stayed past the point he meant to stop") — no timezone is stated in either source. |
| "one character apart" | `db1.cluster.gitlab.com` vs `db2.cluster.gitlab.com` — string comparison of the two quoted hostnames |
| "about six hours of everyone's work" | 17:20 UTC snapshot → ~23:27 UTC termination ≈ 6h; both sources also state "six-hour-old backup" outright |
| "the snapshot was about 20 hours old" (if spoken of the scheduled one) | scheduled daily at 01:00 UTC → outage at ~23:27 UTC ≈ 22.5h; the postmortem says only "almost 24 hours of data", which is what the script uses instead |

## ⚠ Contradictions inside the primary sources — handled, not hidden

**Four procedures vs five techniques.** The postmortem's "Broken recovery procedures"
section enumerates **four** mechanisms (pg_dump→S3, LVM snapshots, Azure disk snapshots,
replication). The incident notes, written the night of, count **five**: "out of five
backup/replication techniques deployed" — they count the staging synchronisation as its own
technique; the postmortem folds it into the LVM snapshot procedure. The episode speaks
**five**, explicitly attributed to the live notes ("their own notes, written that night,
count five"), because that is the number GitLab itself put in a sentence; the postmortem
never states a count as a number. **This is also where EP02's shipped "all four backups"
end card and TOPICS.md's "four, not five" bullet came from — both counted the postmortem's
list and neither checked the incident notes. Flagged to the channel owner 2026-08-07.**

**When the data loss window ends.** The postmortem's intro says changes "between 17:20 and
00:00 UTC" were lost; its Data-loss-impact section says "between January 31st 17:20 UTC and
23:30 UTC"; the incident notes say "between 5:20pm UTC and 11:25pm UTC". Three end times
(00:00 / 23:30 / 23:25). The episode speaks only "about six hours", which all three
support, and never gives the window's endpoints.

**"roughly 5,000" vs "at least 5000".** The postmortem's intro says "roughly 5,000
projects"; its impact section says "at least 5000 projects". The episode says "about five
thousand", which both support.

## Next-episode tease (spoken on the end card)

| Claim | Source | Verbatim |
|---|---|---|
| GitHub 2018: 43 seconds → 24 hours 11 minutes | GitHub post-incident analysis, https://github.blog/2018-10-30-oct21-post-incident-analysis/ (fetched for TOPICS.md 2026-07-31) | "Connectivity between these locations was restored in 43 seconds, but this brief outage triggered a chain of events that led to 24 hours and 11 minutes of service degradation." |

## ⚠ Unverified — do not use

- **The literal command `rm -rf`.** Neither source prints the command line the engineer
  ran; both say only that the directory was "wiped" / "removed". The episode shows the two
  hostnames and the directory path — both verbatim from the sources — and never fabricates
  a command prompt. (TOPICS.md's thumbnail note "terminal cursor blinking on rm -rf" should
  not survive into the artwork as literal text for the same reason.)
- **The engineer's name.** It became public (he added it to the doc himself, and GitLab
  says "we will redact names in future cases"). HOUSE_STYLE §1: the system failed, not the
  person. He is "an engineer" throughout, singular and unnamed.
- **"They almost went out of business" / any revenue or cost figure.** No dollar figure
  exists in either source. No cost number is spoken.
- **"X hours of video" / "1.5 million watched the stream".** Only the peak-viewer figure
  (~5,000) and "#2 live stream" are sourced.
- **"The spare was seconds behind."** Replication lag is described but never quantified as
  a healthy-state number (only "about 4 GB" behind during the failure). Not spoken.
- **"They lost customer code."** False — repositories were stored separately and survived.
  The script says so explicitly, because getting this wrong is the single likeliest
  correction-magnet in the comments.
