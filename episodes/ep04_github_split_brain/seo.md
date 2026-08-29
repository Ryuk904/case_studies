# EP04 — SEO & publishing assets (trimmed format, HOUSE_STYLE §12)

## Title

**Ship this one:**

> The Outage Lasted 43 Seconds. Fixing It Took GitHub 24 Hours.

61 characters, so it survives feed truncation around 60–70. Both numbers are the sourced
pair ("restored in 43 seconds" / "24 hours and 11 minutes of service degradation"), and
the gap between them is the click. It extends the channel's title pattern:

| | EP01 | EP02 | EP03 | EP04 |
|---|---|---|---|---|
| Title says | They forgot to delete some code | They did everything right | They deleted the wrong database | Nobody touched anything, and it broke anyway |
| Failure was | code nobody deleted | code everybody approved | safety nets nobody tested | a failover nobody could undo |

Alternative kept in case the channel ever ranks: `GitHub's 2018 Outage: How a 43-Second
Network Partition Became a 24-Hour Split Brain`.

**Do not use** any title claiming data was lost or GitHub was "hacked". No user data was
lost and nothing was broken into — the video says both out loud.

---

## Description

At 10:52 pm on a Sunday, routine maintenance cut one link inside GitHub's network for 43
seconds. GitHub's own emergency system noticed before any human could, and made everything
worse.

The automated failover moved the master copy of GitHub's databases to the opposite coast.
When the link healed 43 seconds later, both coasts held writes the other had never seen —
two diverged copies of the same ledger, with no honest way to merge them. This is the
story of split brain, told for people who have never run a database: why GitHub chose a
full day of degraded service over deleting anyone's work, why backups that were tested
every single day still took all night to restore, and why the scariest sentence in the
postmortem is "Orchestrator's actions behaved as configured."

### Chapters

```
00:00 43 seconds on a Sunday night
00:38 Two coasts, one pen
02:19 22:52: the machines hold a vote
04:10 The choice: nobody's work gets deleted
04:56 Every backup worked, it still took all night
06:59 Behaved as configured, and a Monday decision
```

Section marks from `out/chapters.txt` (measured render, 12 Aug 2026, runtime 7:57); the
two mid-breakdown marks are the measured scene starts of the choice card (250.8s) and the
rebuild clock (296.4s).

### Sources

- **GitHub, "October 21 post-incident analysis"** (30 Oct 2018) — the primary source for
  every figure in this video:
  https://github.blog/news-insights/company-news/oct21-post-incident-analysis/
- **GitHub, "October 21 Incident Report"** — the short statement published while the
  incident was still running:
  https://github.blog/news-insights/company-news/october21-incident-report/

### Image credits

Background photography is free-licence stock, used as generic illustration and never as
a depiction of GitHub's own facilities. The two CC BY plates below **must** stay in the
published description — that is the licence condition, not a courtesy:

- Control room — NASA Goddard Photo and Video, CC BY 2.0:
  https://www.flickr.com/photos/24662369@N07/8665952824
- Magnetic tape reel — Government & Heritage Library, State Library of North Carolina,
  CC BY 2.0: https://commons.wikimedia.org/w/index.php?curid=152404652

Remaining plates (night skyline, offices at night, server room, sunrise) are CC0 /
public domain and carry no attribution requirement.

---

## Tags

github outage 2018, split brain database, github down, network partition, database failover, orchestrator mysql, raft consensus explained, tech disaster explained, postmortem, devops horror story

---

## Pinned comment

> The detail that stays with me: the failover finished before any human had even read the
> first alert. 43 seconds was an eternity for the machines and nothing at all for the
> people. And GitHub's verdict on the system that caused a 24-hour outage was that it
> "behaved as configured" — nobody had imagined it being allowed to take that decision
> across a continent.
>
> When did you last write down the biggest decision your automation can take without you?

---

## When to publish

Same practical notes as EP01–EP03: publish Tue–Thu around 6:30–9:30 pm IST, upload hours
early and schedule, set thumbnail/title/description/chapters/end screen before it goes
live, point EP03's end screen at this video the day it goes live (manual step in YouTube
Studio), category Science & Technology, not made for kids.

**Do not publish until EP03 has been up at least a few days.** EP03's end card promises
this exact video ("a 43 second network hiccup splits GitHub's database in two, and putting
it back together takes a full day") — both numbers verified against the source in this
episode's research.md.
