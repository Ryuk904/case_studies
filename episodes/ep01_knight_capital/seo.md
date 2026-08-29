# EP01 — SEO & publishing assets

## Title

**Ship this one:**

> They Forgot to Delete Some Code. It Cost $460 Million in 45 Minutes.

It is a merge of the two candidates below, and it wins for one specific reason: **a channel
with no history has no search authority**, so nobody is going to find this by typing "Knight
Capital". Every view for the first few months comes from browse and suggested, where the job
of the title is to make someone who has never heard of the company want to know what happened.
"They forgot to delete some code" does that with no prior knowledge required, and the number
supplies the stake the curiosity needs.

Alternatives, kept because they become correct later:

1. **Search:** How Knight Capital Lost $460 Million in 45 Minutes
   — switch to this once the channel ranks for anything; it is the better query match and
   the worse cold-open.
2. **Punchy:** The Switch Nobody Removed
   — too vague to carry a click on its own; good as a Short's title or a pinned-comment hook.

Titles are written for the general-audience cut. An earlier set led with "deployment failure"
and "7 of 8 servers", which is a great click for engineers and means nothing to anyone else.

---

## Description

In 45 minutes on 1 August 2012, one of the largest trading firms in America destroyed itself.
Nobody hacked them. It happened because of some old code nobody had deleted in nine years, and
a switch somebody decided to reuse.

Knight Capital handled roughly one in every ten trades in American stocks. Their system chopped
big orders into small pieces and kept a tally so it knew when to stop. In 2005 that tally was
moved. An old switched-off feature called Power Peg was never reconnected to it, and never
deleted either. In 2012 a new release reused the exact switch that woke Power Peg up, and the
new code reached seven of eight machines.

212 customer orders became over 4 million trades across 154 companies. Knight's own systems sent
97 warning emails that morning before the market opened, and nobody read them. Then the attempted
fix spread the fault from one machine to all eight.

Every figure in this video is quoted from SEC Administrative Proceeding 34-70694, linked below.

### Chapters
<!-- Timings from out/chapters.txt of the SHIPPING render (Gacrux, tempo 0.8379, 8:01).
     Re-copy after any re-render — a speaking-rate change moves every one of these, and the
     tempo re-solve after the batch-size change moved all four by 4-8 seconds. -->
```
00:00 45 minutes
00:31 Who Knight was, and what the machine did
01:47 The switch, the missing tally, and the eighth machine
06:49 What it cost, and the four ordinary decisions
```

---

## Tags (10)
<!-- Rebalanced for the general-audience cut: fewer engineering terms, more of what a
     non-specialist actually types. -->
1. knight capital
2. how knight capital lost 460 million
3. biggest trading mistake in history
4. wall street disaster
5. stock market glitch
6. worst software bugs in history
7. computer error cost millions
8. software engineering disaster
9. dead code
10. tech failure explained

---

## Pinned comment

> The detail that stayed with me: the system did try to warn them. 97 emails went out from
> 8:01am saying "Power Peg disabled", ninety minutes before the market opened. They weren't
> meant to be alarms, so nobody was watching that inbox.
>
> Everybody has one of these. A folder, a notification, a light on a dashboard that stopped
> meaning anything a long time ago. What's yours?

---

## Source links for the description

- **SEC Administrative Proceeding 34-70694** (the primary source for every figure in this video):
  https://www.sec.gov/litigation/admin/2013/34-70694.pdf
- Aftermath, rescue financing and the Getco merger:
  https://en.wikipedia.org/wiki/Knight_Capital_Group
- Cloudflare's own postmortem of the 2 July 2019 outage (next episode):
  https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/

**Note for upload:** the sec.gov link above opens fine in a browser; it only returns 403 to
automated fetches. Put that canonical link in the description, not a mirror.

---

## When to publish

**Be straight about this: for episode one, the hour barely matters.** Upload timing is a
lever for channels with subscribers, because a notification going out when people are awake
produces the early click-through that decides how wide the video travels. With no subscribers
there is no notification and no launch spike — YouTube will feed this into browse and
suggested over days and weeks, and a video that works will find its audience on day nine as
easily as on day one. The thumbnail and the title are doing ~90% of the work here. Do not
spend a second agonising over the clock.

That said, pick a slot rather than uploading at random:

**Publish Tuesday, Wednesday or Thursday so it goes live around 6:30–9:30pm IST.**

That window is 9am–12pm US Eastern, early evening in Western Europe, and late evening in
India — it is the only time all three of the likely audiences are plausibly awake. Mid-week
avoids the Friday–Sunday flood of entertainment uploads that engineering content loses to.

Practical notes:

- Upload the file **hours early and schedule it**, do not publish on arrival. A 16MB file is
  quick, but YouTube's HD transcode is not instant, and a video that goes public before the
  high-resolution version is ready serves 360p to its most important first viewers.
- Set the **thumbnail, title, description, chapters, tags, and end screen before it goes
  live.** Changing a title after publication resets some of the algorithm's early learning.
- Category **Science & Technology**. Language English. Not made for kids.
- Once 20–30 videos of data exist, replace all of the above with what YouTube Studio's
  "when your viewers are on YouTube" report actually says. That report is real evidence about
  your audience; everything in this section is a prior.
