# EP02 — SEO & publishing assets

## Title

**Ship this one:**

> They Did Everything Right. One Line of Text Still Took Cloudflare Down.

70 characters, so the whole thing survives the feed truncation that starts around 60–70, and
the hook — "they did everything right" — is inside the first 26.

It wins for the same reason EP01's did: **a channel with no search authority gets its views
from browse and suggested**, where the job of the title is to make someone who has never
heard of the company want to know what happened. But it also does a second job EP01's
didn't have to. This is episode two, and two episodes both titled "somebody made a mistake"
would set the channel up as a blooper reel. "They did everything right" says the opposite,
and it is the actual thesis of the video.

It is also the deliberate counterpart to EP01's title:

| | EP01 | EP02 |
|---|---|---|
| Title says | They forgot to delete some code | They did everything right |
| Failure was | code nobody deleted | code everybody approved |

Alternatives, kept because they become correct later:

1. **Search:** How One Regular Expression Took 80% of Cloudflare's Traffic Offline
   — switch to this once the channel ranks for anything. It is the better query match and
   the worse cold-open, and "regular expression" is a word most of the audience does not
   know, which is precisely what the video is written around not needing.
2. **Punchy (<20 chars):** 132 Characters
   — too opaque to carry a click alone; good as a Short's title or a pinned-comment hook.

**Do not use** any title of the form "took down the internet" or "broke 20% of the web".
Cloudflare lost 80% of *its own* traffic. Neither primary source supports a claim about a
share of the internet, and the channel's whole proposition is that its numbers are the ones
the company actually published. See research.md, "Unverified — do not use".

---

## Description

<!-- First two lines are what shows above the fold. Front-load the hook, not the context. -->

On 2 July 2019, one line of text took 80% of Cloudflare's traffic offline for 27 minutes.
It had been written, reviewed, approved and tested. It was never even switched on.

More than 20 million websites and apps sit behind Cloudflare. When you open one of them you
reach Cloudflare first, and their firewall checks your request against a long list of rules
describing what an attack looks like. On 2 July 2019 an engineer made a routine change to
those rules. Six minutes later the tests passed. Five minutes after that it was live on
every machine they own, in more than 180 cities, in about two seconds — because firewall
rules deliberately skip the staged rollout that every other change at Cloudflare goes
through, so that a new attack can be blocked in minutes rather than days.

Inside that change was a pattern 132 characters long, and the seven characters that mattered
asked the machine to find "anything, then anything, then an equals sign, then anything".
There is no single way to do that, so the machine tries every way. Three characters cost 23
attempts. Twenty characters cost 555. Twenty characters with no equals sign at all cost
4,067 — just to work out that the answer is no. Running on every request arriving worldwide,
that took every processor to 100% and Cloudflare's traffic to a wall of error pages.

Three things then had to be true at once. The protection that would have stopped a rule
eating a machine had been removed weeks earlier, by mistake, during a refactor whose purpose
was to make the firewall use less CPU. The test suite checked whether rules caught attacks
and whether they over-blocked, but never how long one took to answer. And the rule was in
simulate mode: real traffic through it, nothing blocked. A rule on a trial run still has to
run.

Then they could not press the kill switch, because logging in to their own internal system
meant going through Cloudflare.

Every figure in this video is quoted from Cloudflare's own postmortem, linked below.

### Chapters

Measured from the shipping render (all 130 lines voiced), 7 Aug 2026. Runtime 8:38.

```
00:00 132 characters
00:42 What Cloudflare does, and why rules get a fast lane
02:30 Anything, followed by anything
07:34 Four ordinary decisions, and your own fast lane
```

The names are deliberately not "Hook / Context / Breakdown / Takeaway". A chapter list is
read as a table of contents by people deciding whether to start the video, so each line has
to be worth clicking on its own.

---

## Tags (10)
<!-- Weighted for a general-audience cut: what a non-specialist actually types, plus two
     engineering terms for the long tail. -->
1. cloudflare outage
2. how one line of code broke the internet
3. cloudflare 2019 outage explained
4. worst software bugs in history
5. regex catastrophic backtracking
6. tech disaster explained
7. why websites go down
8. software engineering disaster
9. postmortem
10. computer error explained

---

## Pinned comment

> The part I keep coming back to isn't the pattern. It's the protection that would have
> caught it, which had been taken out a few weeks earlier by mistake — during a refactor
> whose entire purpose was to make the firewall use less CPU.
>
> Also worth knowing: the way to make this specific problem impossible has been understood
> since 1968, when Ken Thompson published an algorithm that matches in time proportional to
> the length of the input, with no backtracking at all. Cloudflare's own fix list ends with
> switching to an engine built that way.
>
> What's the safety check in your system that somebody removed for a good reason?

---

## Source links for the description

- **Cloudflare's own postmortem** (the primary source for every figure in this video):
  https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/
- **Cloudflare's Form S-1**, 15 August 2019 — the source for "over 20 million Internet
  properties" and the 44 billion threats a day:
  https://www.sec.gov/Archives/edgar/data/1477333/000119312519222176/d735023ds1.htm
- Ken Thompson, "Programming Techniques: Regular expression search algorithm", CACM 1968 —
  the linear-time approach Cloudflare moved to:
  https://dl.acm.org/doi/10.1145/363347.363387

---

## When to publish

**Publish Tuesday, Wednesday or Thursday so it goes live around 6:30–9:30pm IST.** That
window is 9am–12pm US Eastern, early evening in Western Europe, and late evening in India.
Mid-week avoids the Friday–Sunday flood of entertainment uploads that engineering content
loses to.

One thing that is different from EP01, and it is the only scheduling decision that actually
matters at this stage: **do not publish this until EP01 has been up for at least a few
days.** EP01's end card promises this exact video, and EP02's hook pays that promise off in
its first fifteen seconds. That pairing is the single best retention asset the channel has
right now, and it only works if there is an EP01 audience to inherit. Publishing both at
once spends the setup and the payoff on the same empty room.

Practical notes, unchanged from EP01:

- Upload the file **hours early and schedule it**. A video that goes public before YouTube's
  HD transcode finishes serves 360p to its most important first viewers.
- Set the **thumbnail, title, description, chapters, tags, and end screen before it goes
  live.** Changing a title after publication resets some of the algorithm's early learning.
- **Point the EP01 end screen at this video** the day this one goes live. That is a manual
  step in YouTube Studio and it is the whole reason the end card exists.
- Category **Science & Technology**. Language English. Not made for kids.
