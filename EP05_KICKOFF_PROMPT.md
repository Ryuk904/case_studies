# EP05 kickoff — paste the block below into a new chat

Everything between the rules is the prompt. Nothing above or below it needs to go.

---

Build episode 5 of the POSTMORTEM channel, in `C:\Users\abhis\OneDrive\Desktop\case_studies`.

Pure-Python pipeline: cairo draws every frame, ffmpeg muxes, no video editor is ever
opened. EP01 (Knight Capital), EP02 (Cloudflare), EP03 (GitLab) and EP04 (GitHub) are done
and rendered.

READ FIRST, in this order:
  1. `HOUSE_STYLE.md` — all 13 sections. Section 2's word budgets are ground truth from
     rendered episodes. **Section 13 is the newest and the most important: it is the
     staging law, written after EP04 was rejected TWICE for looking recycled.** Read its
     second-pass note before you design a single frame.
  2. `PIPELINE.md` — the numbered build order, the voice gate, and the render gotcha.
     Its "TTS backend: Amazon Polly" section is now HISTORY: see the TTS block below.
  3. `episodes/ep04_github_split_brain/` — the most current worked example. Read
     `research.md` for how a source ledger is built, including its "derived, not quoted",
     "contradictions", "photography" and "do not use" sections.

EPISODE: Roblox's outage of 28–31 October 2021. Roblox switched on a new Consul streaming
feature intended to *reduce* CPU and bandwidth. Under simultaneous heavy read and write
load it produced contention instead. Underneath that, a BoltDB freelist had grown to
nearly a million free page IDs, so a 4.2 GB log store held only 489 MB of real data and
every write amplified. The site was down for 73 hours, with 50 million daily players
locked out.

EP04's end card promises this episode. The exact spoken line is in ep04's `script.md`:
"a performance optimisation takes Roblox offline for 73 hours, in front of 50 million
daily players." **VERIFY BOTH NUMBERS against the source before anything else.** They were
re-checked verbatim on 2026-08-12 and held, but check again — EP02 shipped an end card
saying "four backups" when the source said five, and EP04's kickoff brief described the
severed link incorrectly. If the promise and the source disagree, speak the true number
and tell me.

PRIMARY SOURCE: Roblox's own return-to-service report,
https://about.roblox.com/newsroom/2022/01/roblox-return-to-service-10-28-10-31-2021
Verify that URL resolves and use the canonical one if it has moved. **Expect the path to
have changed** — `blog.roblox.com` and `corp.roblox.com` both redirect here today, and
github.blog silently reshuffled EP04's primary source out from under its own kickoff
brief. Read the report in full. Do not source figures from summaries, news articles or
search snippets. Every spoken number needs a row in `research.md` with a URL and the
verbatim sentence containing it. Where sources disagree, say so and do not speak the
contested figure.

NON-NEGOTIABLE:
- General audience, not engineers. Someone who does not know what a key-value store, a
  write amplification or a p50 latency is has to follow the whole episode. Analogy over
  jargon. This is the single most important editorial rule and EP01's first script was
  rejected outright for breaking it. The hard part of this episode is that there are TWO
  interacting causes, and the second one (a bookkeeping list that grew until every write
  had to walk it) is genuinely subtle. Find the plain-language picture before you write.
- Thumbnails are mine. Deliver `thumbnail_prompt.md` for me to paste into ChatGPT. Do not
  generate the image or offer to. Put it next to EP01–EP04's thumbnails on the channel
  page before committing to a concept — four dark images already sit there.
- All motion lands on whole pixels. See PIPELINE.md, "Motion must land on the pixel grid".
- Pictures over text. Measure the rendered ink in SECONDS of screen time, never eyeball it.
- Look at the contact sheet before rendering (`python -m pipeline.tools.sheet --episode <ep>`).
- Never name an individual engineer. The system failed, not the person.
- No fabricated artefacts: no invented command lines, no fake dashboards or status pages.
  A shown command must be printed by the source or be visibly generic (HOUSE_STYLE §12).

**THE VISUAL BAR — read this twice. EP04 was rendered three times before it was accepted.**

The two rejections were, verbatim: *"it feels like you haven't put any effort in making
the video and just used the previous components. The video needs life. There should be
humans, buildings, images, animation, and other props. The background needs to be
better."* Then, after a first fix that did not work: *"the background is still all black.
You have reused the same setup you used in previous episode."*

Both were mechanically checkable, and checking them is now part of the build:

1. **Measure the background, do not look at it.** The rejected backdrop spanned 11 levels
   of 255 top to bottom. Under ~20 levels it reads as flat black no matter what the code
   says. Decode a frame and measure top vs bottom mean luminance.
2. **Count renderer reuse before you render.** Tally `[scene] … @ …s` from the build log
   into seconds AND repeat counts. In the rejected cut, all four timestamps the viewer
   flagged were EP01/EP02 icons dropped in unchanged, and one CPU dial appeared twice.
   Any renderer used twice needs a reason. A renderer inherited from an older episode
   needs to be doing *this* story's job, not filling a slot.
3. **A repeat is only allowed as a callback that changes state.** EP04 reuses its clock
   wall once, with every clock finally agreeing, as the payoff of the frame where none of
   them did. A repeat with no state change reads as reuse.
4. **Every pictorial beat is set in a real place.** `pipeline/photo.py` fetches
   free-licence stock (Openverse; CC0/PD/**CC BY only** — never share-alike, which would
   reach the finished video, and never non-commercial), caches it under `assets/photo/`
   with a `.json` licence sidecar, and `sketch.photo_backdrop()` composites it dark,
   defocused and palette-tinted under the line art. Add the plates this story needs to
   `photo.MANIFEST` and fetch once. **If you use a CC BY plate, its credit must go in
   `seo.md`'s description block — that is the licence condition, not a courtesy.** Photos
   are generic illustration; never present one as Roblox's own facility, and never as a
   screenshot or document.
5. **Humans, props and depth.** Figures appear wherever the story has people, at human
   scale, with contact shadows (`scenes._shadow`) and a ground to stand on
   (`scenes._stage`). Props exist: `illustrate.ladder`, `toolbox`, `desk`, `box`.
6. **The checklist is retired as a default.** Three of them ate 8.9% of EP04 and a
   tick-box list is the most chart-like thing this channel can draw. A decision is a fork
   in a road; a schedule is objects landing on a shelf; a sequence of steps is weight
   being dragged. Reach for `checklist` only when the *list itself* is the subject.

**Build this episode's own scenes.** EP04 shipped seven (`nightdesk`, `crossing`,
`clockwall`, `sunrise`, `fork`, `haul`, `vault`) plus `coasts` and `ledgers`. Use them
only where they genuinely fit; this story needs its own. It is about a system throttling
itself under its own bookkeeping, so the obvious candidates are a queue that will not
drain, a ledger of free space that grows until walking it is the whole job, and a room
full of players locked out for three days. Build them in `pipeline/illustrate.py` /
`scenes.py` following the existing self-laying-out contract. Max 7 nodes on screen;
subjects own 50–70% of the frame.

Also use what EP03/EP04 added: eased reveals are the default; `code` takes `syntax="on"`,
`hot=` and `prompt="on"` (terminal dressing with a blinking cursor); renderer-emitted
sub-beat SFX via `cue="on"` land sounds at their true schedule-time moments; `mood="dark"`
opts a beat range into the sparse tension bed; climbing counters accelerate. And repeat
the hold-rule audit after the first full render: grep the `[scene] … @ …s` lines and check
every scene on screen 15 seconds or longer still has something moving at second fourteen.
That audit caught two violations on EP04 that the contact sheet cannot show.

TTS — **CHANGED FOR THIS EPISODE, and it is the riskiest part of the build.**

The channel is moving back to **Gemini** from EP05. The owner's verdict on Amazon Polly
was *"the amazon voice doesn't have emotions"*. `config.py` is already switched:
backend `gemini`, `GEMINI_BATCH = 1`, `GEMINI_TEMPO = 0.972`, and a rewritten `TTS_STYLE`
that asks for emotional colour while pinning vocal identity.

**Voice is chosen: `Iapetus`**, already set in `config.VOICE_BY_BACKEND`. I ruled out
Orus and Achernar by ear and left the rest to measurement. On the bake-off passage
Iapetus had the widest dynamic range by a clear margin (18.4 dB against 12.3-16.1) and
near-widest intonation (14.0 semitones) — it leans on words and backs off them, which is
exactly what "doesn't have emotions" was asking for. Two other things settled it: Gacrux,
the old incumbent, measured among the flattest (11.4 st / 14.7 dB) AND is the narrator of
the tiny_rules channel, and two live channels should not share a voice. Samples remain in
`scratch/voice_bakeoff/` if I want to revisit.

Why this is safe now, when Gemini was abandoned at EP03 for two reasons:
- **The time-stretch reason is basically gone.** Gemini's raw rate is ~188.7 WPM of
  speech and the channel now targets 183.4, so the stretch is **2.8%**, not the 19.4%
  that made EP02 sound processed. That objection was mostly an artefact of the old
  145-WPM target.
- **The register-swing reason has a known cure: solo synthesis.** Batching is the cause
  (the model performs a batch as a *set* and drops register for short punchy lines).
  Measured 95th-percentile deviation: batch 12 → 5.89 st, batch 4 → 3.73, solo → ~1–4.

What that costs, and how to run it:
- Solo means ~one request per line, about 120 for an episode, against a free-tier
  ceiling of roughly **40/day on the preferred model** (4 keys × 10). So **the synth run
  will span about three days.** That is fine and expected: clips are content-addressed,
  so re-running `build.py` the next day resumes from cache and only buys what is missing.
  Quota resets at Pacific midnight = 12:30 IST.
- **Never "fix" a quota stall by raising `GEMINI_BATCH`.** That trades the defect the
  owner personally reported on EP02 straight back in.
- The key×model rotation was fixed on 2026-08-12 to walk **model-major**, so all four
  keys are spent on the preferred model before any fallback model is touched. Do not
  reorder it: the old key-major order changed models every ~10 requests, which at solo
  synthesis would narrate one episode in up to three different model voices.
- The pool of ~120 requests/day is **shared with the other channels**, so claim it
  deliberately before anyone else draws on it.

Gates and calibration, none of which are optional here:
- `build.py` runs `voice_qc` automatically and halts before the render if more than 10%
  of clips sit beyond 2.5 semitones of the episode median. **If it fires, tell me — do
  not pass `--ignore-voice`.** Re-synthesising a flagged line is a re-roll, not an edit.
- **A voice change RESETS the speaking-rate calibration.** `MEASURED_WPM = 173.3` and
  `SPEECH_WPM = 183.4` are Polly ground truth, and `GEMINI_TEMPO = 0.972` is solved from
  EP01's old Gacrux render, not from this voice. Both are estimates until this episode is
  rendered. Run `python -m pipeline.tools.solve_rate <ep>` after the first full render,
  report the drift, and re-derive HOUSE_STYLE §2 if it moved more than ~2%. Word budgets
  may need re-deriving before EP06.
- Editing `TTS_STYLE` re-buys the whole episode — it is part of the clip fingerprint.
  Do not tune it casually at ~40 requests/day. And never ask this model for "quietly" or
  "softly": it whispers.
- **EP01–EP04 are frozen.** Their audio is cached under the old backend. Do not rebuild
  them under the new voice — the config switch is global, so a rebuild would re-synthesise
  a shipped episode in a different narrator.

**Finish the script before the first real synth, and get the visuals right before the
first FULL render.** A 1080p render is ~13–17 minutes. `--smoke` (free, ~60s) proves every
scene renders; the contact sheet proves composition; only then spend the render. EP04
burned three full renders because that order was not respected.

DELIVERABLES:
  `research.md`, `script.md`, `seo.md`, `thumbnail_prompt.md`, and `out/episode.mp4`
  verified frame-for-frame. Copy `episodes/_template/build.py` into the new episode folder
  first — EP02's first launch failed because it was missing.

  `seo.md` and `thumbnail_prompt.md` stay TRIMMED (HOUSE_STYLE §12): description is two
  hook lines plus at most one short paragraph, then chapters (from the real timeline) and
  source links, plus any CC BY image credits; tags are ONE comma-separated line;
  thumbnail_prompt.md is ONE with-text prompt plus only the binding rules. The title still
  extends the channel's title pattern (see ep04 seo.md's four-column table).

  **End card teases EP06 — you choose it and I will confirm.** The deeper bench in
  `TOPICS.md` is researched but NOT source-verified, so whichever you pick, fetch its
  primary source and put the teased numbers in this episode's ledger so lint passes. My
  suggestion is Meta's BGP withdrawal of October 2021 — it rhymes with EP04 (automation
  doing exactly what it was configured to do) and the detail that staff could not badge
  into their own buildings is a gift, and there is already a `door` renderer built for
  exactly that image. Say if you would rather take CrowdStrike 2024 or AWS S3 2017.

CHECKPOINT: show me the hook and the source ledger before you write the script.
Then show me the contact sheet before the full render.

Then tell me what you are least confident about.

---
