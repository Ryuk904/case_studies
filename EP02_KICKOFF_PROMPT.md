# EP02 kickoff — paste the block below into a new chat

Everything between the rules is the prompt. Nothing above or below it needs to go.

---

I'm building a faceless YouTube channel of engineering-failure case studies at
`C:\Users\abhis\OneDrive\Desktop\case_studies`. It is a pure-Python pipeline — cairo draws
every frame, ffmpeg muxes, no video editor is ever opened. Episode 1 (Knight Capital) is
finished and about to be uploaded. You are building **episode 2**.

**Read these before you touch anything.** They are the accumulated rules of the channel and
most of them were learned by getting something wrong first:

- `HOUSE_STYLE.md` — voice, word budgets, the 45-second rule, factual integrity, visual
  grammar, the motif system, banned phrases.
- `PIPELINE.md` — how a build works, the two-stage TTS cache, speaking-rate calibration,
  the pixel-grid rule, and the numbered build order. Follow that build order.
- `episodes/ep01_knight_capital/` — a complete worked example. `script.md` is the format,
  `research.md` is the sourcing standard, `seo.md` is the publishing package.

## The episode

**Cloudflare's outage of 2 July 2019.** A single Web Application Firewall rule went out
globally; the regular expression inside it backtracked catastrophically, CPU pinned across
the network, and roughly 80% of Cloudflare's traffic went to 502 for about 27 minutes.

Episode 1 ends by promising exactly this, so the hook has to pay off "one line of text took
80 percent of Cloudflare's traffic offline."

Why it earns an episode: Cloudflare published an unusually honest postmortem, so the
mechanism is properly sourceable; the cause is one line a competent engineer wrote and
reviewed; and it rhymes with EP01 without repeating it — Knight was code nobody deleted,
Cloudflare was code everybody approved.

**Primary source:** https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/
Fetch it and read it in full. Their own writeup is the authority; do not source figures from
summaries, news articles, or search snippets. Every number that gets spoken needs a row in
`research.md` with a URL and the verbatim sentence containing it.

## The one thing I want more of: animation

EP01 is good but the pictures mostly *appear* and then hold. I want EP02 to move. Concretely:

1. **The stick figures are frozen and shouldn't be.** `pipeline/stickman.py` is a real
   skeletal rig — `WALK`, `RUN` and `IDLE_BREATH` are keyframed cycles, `cycle()` interpolates
   them, and `blend()` moves between any two poses. EP01 used four *static* poses and never
   called a cycle once. Use them. Add cycles if the beat needs one the rig doesn't have.
2. **Animate the state change, not just the end state.** A switch should flip, a counter
   should roll, servers should go red one at a time in sequence, a queue should back up.
   EP01 mostly draws the finished picture with a reveal wipe over it.
3. **Give some scenes a second beat.** The strongest EP01 frames are the ones where something
   is still happening ten seconds in — the alarm's pulsing arcs, the dashboard's moving bars.
   The weakest are static after two seconds. A scene held for 15 seconds needs a reason to
   still be on screen at second 14.
4. **Motion between scenes is already there** (accent-led wipe, `config.TRANSITION`) — vary
   it if a beat wants a harder or softer cut.

**The hard constraint on all of it:** any motion must land on whole pixels. Sub-pixel
translation re-antialiases every glyph edge 30 times a second, which reads on screen as the
text vibrating and wastes the h264 bitrate on noise. This already shipped once and had to be
found by diffing consecutive frames. `scenes._drift()` shows the pattern — round the
translate. Diagnose any suspected shimmer by decoding consecutive frames of a scene that
should be still and diffing them; anything over a few hundred changed pixels at a delta
above ~20 is a bug, not encoder noise.

## Constraints that are not negotiable

- **General audience, not engineers.** Someone who does not know what a regular expression
  is has to follow the whole episode. Analogy over jargon. This is the single most important
  rule and the v1 script of EP01 was rejected outright for breaking it.
- **No paid API.** Gemini free tier only. `GEMINI_BATCH` stays at **4** — larger batches make
  the model perform the lines as a script with speaker turns and swing pitch by up to an
  octave, which sounds like a second narrator. 4 costs ~35 requests of ~90/day.
- **Re-solve the speaking rate** with `python -m pipeline.tools.solve_rate <ep>` after any
  voice, tempo or batch-size change, and update `GEMINI_TEMPO`. Batch size changes the pace
  as well as the timbre.
- **Pictures over text.** Every text-only frame takes a `motif` — see the motif section of
  `HOUSE_STYLE.md`, including how to size one (measure the rendered ink, never eyeball it)
  and why a motif must not repeat the primitive of an adjacent scene.
- **Thumbnails are mine to generate, not yours.** Deliver `thumbnail_prompt.md`, a prompt I
  paste into ChatGPT. Do not generate or offer to generate the image. Match the dark palette.
- **Look at the contact sheet before rendering.** `python -m pipeline.tools.sheet --episode <ep>`
  costs seconds; a render costs eight minutes. One pass over the sheets caught four layout
  collisions on EP01 that were invisible in the script.
- Retention is the goal — open loops early, pay them off late.

## Done means

`out/episode.mp4` verified frame-for-frame, `research.md` with a complete source ledger,
`script.md`, `seo.md` with title/description/chapters/tags/pinned comment, and
`thumbnail_prompt.md`. Then tell me what you are least confident about.

Start by reading the three docs and the EP01 example, then fetch the Cloudflare postmortem
and build `research.md`. Show me the hook and the source ledger before writing the script.

---
