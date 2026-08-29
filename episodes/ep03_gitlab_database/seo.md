# EP03 — SEO & publishing assets

## Title

**Ship this one:**

> They Deleted the Wrong Database. Then All Five Backups Failed.

62 characters, so the whole thing survives the feed truncation that starts around 60–70,
and the double hook — the mistake *and* the betrayal by the safety nets — is complete by
character 62. "The wrong database" is the click; "all five backups failed" is the promise
the video actually keeps, and it is the sourced number ("out of five backup/replication
techniques deployed none are working reliably").

It also completes the channel's title triptych:

| | EP01 | EP02 | EP03 |
|---|---|---|---|
| Title says | They forgot to delete some code | They did everything right | They deleted the wrong database |
| Failure was | code nobody deleted | code everybody approved | safety nets nobody tested |

EP02's end card promised this episode as "GitLab deleted their own database, then found
all four backups had failed". The count in that promise is wrong (see research.md — the
sourced number is five); this title quietly corrects it rather than repeating it.

Alternatives, kept because they become correct later:

1. **Search:** The GitLab Database Incident: How Five Backup Systems All Failed at Once
   — switch to this once the channel ranks for anything; "GitLab database incident" is the
   query with actual volume.
2. **Punchy (<25 chars):** 5 Backups. 0 Worked.
   — too opaque to carry a click alone; good as a Short's title or a community-post hook.

**Do not use** any title claiming data was "hacked", "stolen", or that "GitLab lost your
code". Nothing was broken into, and repositories survived untouched — both facts are in
the primary sources, and the video says them out loud.

---

## Description

<!-- First two lines are what shows above the fold. Front-load the hook, not the context. -->

At 11pm on 31 January 2017, a GitLab engineer wiped the wrong database server. Around
300 gigabytes of production data, gone in seconds. Then all five backups turned out to be broken.

GitLab.com keeps its code repositories in one kind of storage and everything else — every
project, issue, comment and user account — in one database. That database ran on two
identical machines: the live server, and a spare that copies every change. On the night of
31 January 2017, five hours into fighting a spam attack, the spare broke. The fix is
brutal but standard: wipe the spare, copy everything across fresh. Close to midnight, one
tired engineer — who had tried to sign off an hour earlier — ran the wipe on the wrong
machine. The two hostnames differ by one character. He noticed within a second or two. Of
around 300 gigabytes, about 4.5 were left.

Then the safety nets, one by one. The spare: an empty box he had wiped himself half an
hour before. The daily export: silently producing files a few bytes long, every night, for
nobody knows how long, because the export tool had fallen a major version behind the
database. The warning emails about those failures: rejected by the receiving mail server
for a missing signature, so nobody ever saw one. The cloud storage bucket: empty. The
hosting provider's disk snapshots: never enabled for the database servers. Their own
incident notes, kept in public while it happened, put it in one sentence: "out of five
backup/replication techniques deployed none are working reliably or set up in the first
place."

What saved GitLab was not a backup. Six hours before the deletion, the same engineer had
taken a manual snapshot of production for an unrelated load-balancing experiment. It was
the only copy left. Copying it back took around 18 hours, live on YouTube, in front of
about 5,000 people. The six hours after the snapshot — roughly 5,000 projects, 5,000
comments and 700 new user accounts — never came back.

Every figure in this video is quoted from GitLab's own postmortem and their live incident
notes, linked below.

### Chapters

Measured from the shipping render (all 118 lines voiced), 7 Aug 2026. Runtime 7:30.
Section marks from `out/chapters.txt`; the two mid-breakdown marks are the measured scene
starts of the first cross-off card (238.1s) and the "except" card (309.0s).

```
00:00 The wrong terminal
00:32 Two servers and five safety nets
02:09 Eleven at night
03:58 Crossing off the backups
05:09 The accident that saved them
06:34 Ownership, and a Monday decision
```

The names are deliberately not "Hook / Context / Breakdown / Takeaway". A chapter list is
read as a table of contents by people deciding whether to start the video, so each line
has to be worth clicking on its own.

---

## Tags (10)
<!-- Weighted for a general-audience cut: what a non-specialist actually types, plus two
     engineering terms for the long tail. -->
1. gitlab database incident
2. gitlab deleted database
3. worst software disasters in history
4. they deleted the production database
5. database backup failure
6. rm rf production
7. tech disaster explained
8. postmortem
9. devops horror story
10. computer error explained

---

## Pinned comment

> The detail I can't get over isn't the deletion. It's that the only copy that survived
> wasn't one of the five official backups. It was a snapshot one engineer happened to take
> by hand, six hours earlier, for a completely unrelated experiment. The same engineer who
> later deleted the database.
>
> GitLab's own postmortem asks why the backups were never tested and answers it in one
> word: nobody owned it. Their fix list literally includes "assign an owner for data
> durability."
>
> When did *you* last actually restore one of your backups?

---

## Source links for the description

- **GitLab's own postmortem** (the primary source for every figure in this video):
  https://about.gitlab.com/blog/2017/02/10/postmortem-of-database-outage-of-january-31/
- **GitLab's live incident notes**, published 1 February 2017 while the recovery was still
  running — the source of "out of five backup/replication techniques deployed none are
  working reliably or set up in the first place":
  https://about.gitlab.com/blog/2017/02/01/gitlab-dot-com-database-incident/

---

## When to publish

**Publish Tuesday, Wednesday or Thursday so it goes live around 6:30–9:30pm IST.** That
window is 9am–12pm US Eastern, early evening in Western Europe, and late evening in India.
Mid-week avoids the Friday–Sunday flood of entertainment uploads.

**Do not publish until EP02 has been up for at least a few days.** EP02's end card
promises this exact video and its first minute pays that promise off. (EP02's promise says
"four backups"; this episode says five, which is the sourced number. If EP02 is not yet
public when you read this, consider fixing its end-card line first — see research.md.)

Practical notes, unchanged from EP01/EP02:

- Upload the file **hours early and schedule it** so the HD transcode finishes before
  anyone sees it.
- Set the **thumbnail, title, description, chapters, tags, and end screen before it goes
  live.**
- **Point the EP02 end screen at this video** the day this one goes live — manual step in
  YouTube Studio.
- Category **Science & Technology**. Language English. Not made for kids.
