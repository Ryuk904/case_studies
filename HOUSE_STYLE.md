# HOUSE STYLE — locked

The point of this file is that episode 30 sounds exactly like episode 1.
Every rule here is enforced at write time. If a rule fights a specific episode, change this file
deliberately — do not make a one-off exception.

---

## 1. Channel identity

- **Format:** faceless technical case study, 6–10 minutes.
- **Audience: general.** Someone who does not know what a key-value store, a replica or a
  p99 is has to be able to follow the whole episode. Analogy over jargon, every time.

  > **Corrected 2026-08-12.** This line used to read "working software engineers… assume
  > they know what a load balancer, a replica, and a p99 are. Do not explain them." That
  > was wrong from EP01 onward: EP01's first script was rejected outright for writing to
  > engineers, and every kickoff brief since has specified a general audience as
  > non-negotiable. The document contradicted the actual editorial standard for four
  > episodes. The briefs were right; this file was stale.

- **Register:** analytical, sharp, precise — and, from EP05, **dry**. The voice is a very
  good senior engineer walking a colleague through an incident review and being quietly
  funny about it. Short lines. Understatement after a big number. The deadpan restatement
  of something absurd, delivered flat. Not a narrator, not a teacher, and still not a hype
  channel.

  Changed 2026-08-12 at the channel owner's request ("I want a Fireship type lean"). Two
  things did **not** change with it, and they are what keep the register honest:

  - **§7's banned list stands.** Dry is not loud. "insane", "crazy", "game-changer" and
    every cousin of them are still build failures. The humour is in timing and
    understatement, never in adjectives.
  - **The stance below is absolute.** Wit is aimed at the *situation*, never at the people
    in it.

  The delivery prompt (`config.TTS_STYLE`) carries the same instruction, and it must stay
  SHORT — a long one gets performed as content. See the note above it in `config.py`.

- **Stance:** never mock the engineer who made the mistake. The system failed, not the person.
  This is both correct and legally safer. It is also usually the more interesting story:
  on EP05 every one of the four wrong diagnoses was a reasonable decision taken with
  broken instruments, and the joke is on the situation, never on the team.

---

## 2. Word budgets (173 WPM — Polly Ruth, generative)

Derived from `config.MEASURED_WPM`. **Calibrate only against a fully rendered episode**, using
`python -m pipeline.tools.solve_rate <episode>`. Synthetic calibration has now been wrong
three times:

| Method | Said | Actually |
|---|---|---|
| One line, untrimmed | 138.9 WPM | counted TTS container padding as speech |
| Synthetic 8-line passage | 140.2 WPM | passage was far more digit-dense than a real script |
| Synthetic 8-line passage, Polly Ruth | 159.0 WPM | 8.3% slow — same method, third failure |
| **Rendered EP01, edge** | **164.3 WPM at `-4%`** | ground truth: 1125 words, 383.1s speech + 27.8s fixed |
| **Rendered EP01, Gacrux** | **170.0 WPM at tempo `0.97`** | ground truth: 1144 words, 375.1s speech + 28.8s fixed |
| **Rendered EP03, Polly Ruth generative** | **173.3 WPM at `+0%`** | ground truth: 1286 words, 420.8s speech + 24.4s fixed |

A voice change resets this. Gacrux at the tempo solved for edge ran the episode 17% fast, and
nothing but a real render would have shown it: the delivery sounds fine line by line.

**Changed at EP03 (2026-08-07): the channel moved to Amazon Polly, `Ruth`, generative
engine, and the numbers below went up about 20% against the 145-WPM era.** Not a stylistic
choice — generative quantises the SSML rate into roughly three buckets rather than
honouring a percentage, so the only usable speed is its middle bucket, **measured at 173.3
WPM on the rendered EP03** (the pre-render synthetic estimate said 159 and was 8.3% slow).
There is no dial to solve. Since the runtime targets in the timecode column are fixed, a
faster reader needs *more* words to fill the same minutes, not fewer.

The trade was taken deliberately: the alternative was time-stretching the audio back down
to 145, and eliminating that stretch is most of why the channel left Gemini. EP01 and EP02
are at 145 and will sound very slightly slower than everything after them.

| Section | Timecode | Words | Hard rule |
|---|---|---|---|
| Hook | 0:00–0:45 | 108–125 | System named + stake + headline metric, all inside 45s |
| Context & Architecture | 0:45–2:30 | 281–305 | How it was built and why that was reasonable |
| Deep Technical Breakdown | 2:30–7:00 | 729–777 | The actual mechanism, step by step |
| Takeaway | 7:00–end | 156–191 | Transferable lesson + soft subscribe |
| **Total** | | **1,285–1,464** | Inside the 1,200–1,550 spec |

Corrected 2026-08-07 from the rendered EP03 (`solve_rate`: 173.3 WPM episode-wide, 183.4
pure speech). EP03 itself was written to the provisional 159-WPM table and shipped at
1,286 words / 7:30 delivered — inside the runtime spec, sections a few percent ahead of
their timecode targets, hook at 0:32. Episodes from EP04 use the numbers above.

Run `python -m pipeline.lint <episode>` to check. It fails the build if a section is out of band.

---

## 3. The 45-second rule

By 0:45 the viewer must have heard, explicitly:
1. The exact system ("Knight Capital's SMARS order router"), not a category ("a trading system").
2. The stake in one number ("$460 million in 45 minutes").
3. The shape of the cause ("a deploy that reached seven of eight servers").

If any of the three is missing at 0:45, the hook is rejected.

---

## 4. Factual integrity

- Every number spoken in the script must have a row in `research.md` → SOURCES ledger, with
  a URL **and** the verbatim sentence from that source containing the number.
- **Primary sources only** for headline metrics: the company's own postmortem, an SEC/FAA/NTSB
  filing, an RFC, or a named engineer's writeup. Not a summary blog, not a search snippet,
  not an AI-generated summary of a source.
- Search-engine result summaries are **not** sources. They frequently echo the numbers in your
  query back at you. Fetch the page.
- If a number cannot be sourced, it gets cut or softened to qualitative ("a large fraction of").
  Never estimate a metric and present it as measured.
- If sources disagree, say so on screen. ("Knight's own 8-K said $440M pre-tax; the SEC order
  says over $460M.") Disagreement is content, not a problem.
- Attribute contested causes: "the postmortem attributes this to…", not "this was caused by…".

---

## 5. Writing for TTS (non-negotiable — this is what makes the render work)

The script is not prose. It is the **timing source** for the whole video. Each line becomes one
audio clip, and the frame schedule is built from that clip's measured duration.

- **One sentence per line.** No exceptions. A blank line separates beats.
- **No em-dashes.** TTS swallows them. Use a period or a comma.
- **No parentheses** in spoken lines. Rewrite as a separate sentence.
- **Spell out anything the voice would mangle:**
  | Write this | Not this |
  |---|---|
  | `300 milliseconds` | `300ms` |
  | `the p99` → `the p ninety-nine` | `p99` |
  | `Consul's key-value store` | `Consul KV` |
  | `four million orders` or `4 million orders` | `4,000,000 orders` |
  | `B-olt-D-B` only if tested; else `Bolt D B` | `BoltDB` |
- **Numbers stay in digits when the voice reads them correctly** (`$460 million`, `45 minutes`,
  `73 hours` all read fine on edge-tts). Verify with `python -m pipeline.tts --probe "<line>"`.
- **Pauses are explicit:** `[PAUSE:0.8]` on its own line inserts 0.8s of silence and holds the
  current frame. Use before a reveal, after a number, never more than one per beat.
- **Emphasis:** wrap in `*asterisks*`. The TTS layer converts to SSML prosody. Max one per sentence.

---

## 6. Script file format (machine-readable — `script.md` is the single source of truth)

Phase 2, 3, and 4 all live in this one file so they cannot drift apart.
`visuals.md` is **generated** from it, never hand-edited.

```
## SECTION: hook

[VISUAL: title_card text="$460,000,000" sub="45 minutes" ]
On August 1st, 2012, Knight Capital lost $460 million in 45 minutes.
[PAUSE:0.8]

[VISUAL: diagram nodes="[NYSE Open] --(orders)--> [SMARS] --(routes)--> [8 Servers]" highlight="8 Servers"]
The cause was a deployment that reached seven of its eight servers.
[SFX: thud]
```

A param value is delimited by double quotes and therefore **cannot contain one**, which
rules out most real code and any regular expression. `code` takes `file="snippet.txt"`
instead, resolved next to `script.md`. Put the literal text in the episode folder, never in
`pipeline/`.

Directives:
- `[VISUAL: <renderer> <k="v">…]` — switches the frame content. Holds until the next `[VISUAL:]`.
- `[PAUSE: <seconds>]` — silence, frame holds.
- `[SFX: <name>]` — mixes a synthesized effect at that timestamp. Names in `pipeline/sfx.py`.
- `## SECTION: <hook|context|breakdown|takeaway>` — used for chapter timestamps and lint.

---

## 7. Banned

Phrases that mark generic tech content. The linter greps for these and fails the build.

- "In today's video" / "Let's dive in" / "Buckle up"
- "And that's why observability matters" and every cousin of it
- "Little did they know"
- "Simply put" / "Basically" / "Essentially"
- "It's important to note that"
- "game-changer", "revolutionary", "insane", "crazy"
- Rhetorical questions in the hook ("But what if I told you…")
- Any sentence that could open any other episode

**Endings specifically:** the takeaway must name a decision a viewer could make differently on
Monday. "Monitor your systems" is not a takeaway. "Delete dead code on the day you retire it,
because a dormant flag is a loaded gun with a nine-year fuse" is.

---

## 8. Visual grammar

**Art direction (set 2026-08-04).** Dark documentary base — near-black ground, off-white
type, amber for the thread the eye follows, red only for the failure path — with full-bleed
saturated colour fields at section breaks and hero beats. Chosen from a four-way look test
after the warm-paper scheme was rejected: cream, grey and one red is near-zero contrast on a
phone and reads as a beige PDF.

Three things carry it, and none of them is the palette:

1. **Composition varies.** `layout="left|right|hero"`, derived from the content when the
   script does not say. The first cut used headline-top-centre / subject-centre /
   caption-bottom fifty-four times, and that monotony was doing more damage than any single
   frame's contents.
2. **Type fills its measure.** Headlines run 130–180pt. Use `sketch.fit_block()`, never
   `fit_size()`, for anything that wraps — `fit_size` sizes an unwrapped string, so on a
   sentence it forces one line and shrinks the whole thing to a caption. This is worth
   grepping for after any type change: it was fixed in `title_card` and left in `end_card`,
   where a fourteen-word next-episode title rendered at caption size on the one frame whose
   entire job is selling the next watch.
3. **Subjects are big.** An illustration should own 50–70% of the frame. Floating a small
   object in the middle of a dark frame is the same failure as floating it in a white one.
4. **Labels on a drawing are `SZ_ANNOT`, not `SZ_BODY`.** An annotation pinned to an
   illustration carries as much meaning as the drawing — "written in 2003, never removed" is
   the punchline of its frame. At `SZ_BODY` it is 2.8% of frame height and gone on a phone.
   `SZ_BODY` is for running text read close up; nothing in a 1080p frame should use it as a
   caption.
5. **Alignment alternates.** `_headline()` picks left or centre from the content hash. The
   illustration scenes are the bulk of the episode, and one fixed headline slot made them
   all open identically however different the drawing beneath was — the same monotony the
   layouts fixed for the text cards, just hidden somewhere less obvious.

Numbers get a **rule under them**, never a highlighter wash: amber at half alpha over
near-black turns olive and muddies the glyphs it is meant to lift.

- Palette and fonts live in `pipeline/config.py`. Never hardcode a colour in an episode.
- Precise, confident geometry — `STROKE` 5.0, one pass. The loose double-pass sketch look
  belonged to the paper direction; on a dark ground it reads as timid hairlines.
- A diagram earns screen time only if it changes. Static diagram held over 12+ seconds = cut it
  into a build-up sequence instead.
- Max 7 nodes on screen at once. Beyond that, split the diagram.
- Code on screen: max 12 lines, monospace, one highlighted line. Never a full file.
- Numbers get their own full-frame card when they are the point.

### Renderers

Everything registered in `pipeline/scenes.py`. See them all at once with
`python -m pipeline.tools.sheet`.

| Renderer | Use it for |
|---|---|
| `title_card` | a line of text that needs to land on its own |
| `metric_card` | one number that *is* the point; counts up |
| `quote` | a verbatim sentence from the primary source, attributed |
| `diagram` | how something is wired; `[a] --(label)--> [b]; ...` |
| `timeline` | events in order across a span of years |
| `code` | the rare case where the literal text matters; `body="…"` or `file="snippet.txt"` |
| `end_card` | the next-episode hook |

Pictorial. Reach for one of these *before* reaching for `title_card`:

| Renderer | Use it for |
|---|---|
| `switch` | a thing turned on or off — `state="on"\|"off"` |
| `servers` | a fleet of machines — `n="8" bad="8"` (1-based) |
| `mail` | a pile of warnings nobody read |
| `alarm` | something sounding that nobody is listening to |
| `counter` | a running tally — `blank="on"` shows empty windows |
| `calendar` | a span of years — `years="2003\|…\|2012" mark="0"` |
| `checklist` | steps taken and not taken — `marks="tick\|cross\|"` (blank = empty box) |
| `dashboard` | everything reporting healthy |
| `loop` | a cycle with no way out |
| `link` | two things that are no longer connected |
| `lock` | nothing was broken into |
| `scale` | two quantities whose *ratio* is the point |
| `clock` | a time, or elapsed time as a fraction |
| `people` | "one in ten", as figures rather than a percentage |
| `stick` | a person *doing* something — `pose="carry\|shrug\|type\|walk\|panic\|slump…"` |

**Moving pictures (added for EP02).** These animate a state *changing* rather than showing a
state that is true, and every one of them still has something happening after the reveal has
landed. Prefer them for any beat where the change is the point.

| Renderer | Use it for |
|---|---|
| `gauge` | something pinned against its limit — `value="0.99"`; the needle trembles at the stop |
| `world` | a change propagating everywhere — `secs="2.29"` is how long the wave takes, then it pulses |
| `windows` | a wall of sites falling over one at a time — `bad="1.0" secs="2.2" code="502"` |
| `barrier` | a protection with a hole in it, and the thing it should have stopped going through; `gap="off"` for the intact bookend |
| `backtrack` | work exploding with input size — `text="x=xxx" target="555"`; the counter paces itself off the beat's length |
| `door` | someone locked out, badging and being refused, on a loop |

Four existing renderers gained a moving form. Use them instead of two static frames:

- `switch state="flip" at="2.4"` — throws the rocker on screen instead of cutting between OFF and ON.
- `servers fall="2.2"` — the listed machines go over in sequence rather than arriving already red.
- `counter roll="40"` — digits keep turning, for a count with no stop condition.
- `stick pose="walk" travel="480" then="panic" at="3.2"` — cycles (`walk run idle type panic
  wave look badge`), travel that lands on whole pixels, and a blend into a second pose.

**Cuts vary now.** `cut="hard"` snaps in 0.07s for a beat that should land like a slap;
`cut="soft"` cross-dissolves over 0.62s for a change of subject. Omit it for the standard
accent-led wipe. One wipe for a whole episode is its own kind of monotony.

### No frame is text alone

`title_card`, `quote` and `end_card` take a **`motif`** — a supporting illustration drawn in
the column the type is not using. It is not decoration; it names the thing the sentence is
about, and the viewer reads it before the sentence finishes.

```
[VISUAL: title_card text="remember the tally" motif="counter"]
[VISUAL: quote text="In 2005, Knight moved…" motif="calendar:2005|2006|2007|2008"]
```

Spec is `name` or `name:arg`. Everything in the pictorial table works, plus `stick:<pose>`.
Three rules learned the hard way:

- **Solve the scale from measured ink, never by eye.** Guessing was wrong by 3–5× in *both*
  directions on the first pass — `people` rendered 409×75, a thin strip beside 180pt type,
  while `dashboard` rendered 881 wide, wider than the column it had to fit in. Render the
  primitive to a surface, take the alpha bounding box, solve for the target.
- **Pick the column before the centre.** With type at 0.56 of the content width, a motif
  centred at 0.745 of the frame has ~300px of clearance on its left, not the ~430 the
  fraction implies. `_motif_spot()` centres in the actual gap.
- **Never repeat the primitive of an adjacent scene.** Four of the first twelve motifs sat
  directly beside a full-frame scene of the same object and read as a stutter. Either change
  the motif or make it a *build*: the single-envelope `mail:1` running into the pile of 97
  works precisely because the scale changes the meaning.

### Nothing holds still for fifteen seconds

The note back on EP01 was that the pictures mostly *appear* and then hold. The frames that
survived it were the two with an ongoing motion in them — the alarm's pulsing arcs and the
dashboard's moving bars. The rule that came out of it:

**A scene held for fifteen seconds needs a reason to still be on screen at second fourteen.**
Draw-on is not that reason; draw-on is over in two and a half seconds. Either the beat gets
a renderer from the moving-pictures table, or it gets split into two visuals.

Two ways to get it wrong, both found on EP02's contact sheets before they cost a render:

- **A counter that finishes early.** The backtracking counter reached its target ten seconds
  into a forty-second beat and then froze for thirty. Counters now pace themselves off the
  beat's measured length, which is a number that only exists after the audio is measured —
  so it cannot be hand-set at authoring time and be right.
- **A settled frame that contradicts its own caption.** The same scene froze on a green
  matched cell under the words "it has not found an answer yet". If a scene has an end
  state, the end state's label has to be written for the end state.

**Ration `title_card`.** It is the easy answer and it is flat: text on paper is what the
narration is already doing. The first cut of EP01 was **48% of its screen time** on title
cards, and the note back was "all I see is mostly text written on the screen, there are no
illustrations". Rewiring twenty directives — no change to a single spoken word — took
text-only scenes from 58% of the runtime to 28%.

Measure it. Do not eyeball it: counting *types* said the episode had eleven kinds of visual
and looked fine, while counting *seconds* showed half the video was one of them.

If a beat is about a quantity, a ratio, a duration, a mechanism, or a thing that did or did
not happen, a picture says it better. A picture the viewer *reads* before the sentence
finishes buys attention; a caption spends it.

---

## 9. Subscribe ask

One sentence, at the end, factual and low-key. No mid-roll ask, no "smash".
Template: "If you want the next one, it's about *<next topic>*. Subscribe and it'll show up."

---

## 10. Delivery — from the EP02 viewer notes (2026-08-07)

Four notes came back on the finished EP02. All four are binding from EP03.

**One voice, and it is now a build gate.** The note was that the narrator switches from a
female to a male voice around 02:54 and back later. Measured: **51 of 130 clips beyond 2.5
semitones from the episode median, 95th percentile 5.72 semitones.** Gemini swings register
between sentences *inside a single batched request* — it is not the fallback model, and it
happens at `GEMINI_BATCH = 4`, so the batch size is not a defence.

`pipeline/tools/voice_qc.py` has existed since EP01, was written for this exact defect, and
was not run on EP02. It is now called from `build.py` after synthesis and **halts before the
render** when more than 10% of clips are out of tolerance. The audio is already cached at
that point, so stopping costs nothing but the render. Override with `--ignore-voice` only
when you have listened and decided it is fine.

Re-synthesising a flagged line is a re-roll, not a repair: the register is random per
request, so the fix is to synthesise the batch again and re-measure, not to edit anything.

**Narration should need less stretching.** The voice reads as processed partly because it
is: Gemini speaks at roughly 173 WPM and every clip is time-stretched to 145 by
`atempo=0.8379` — about a 19% stretch applied to 100% of the audio. Prompt-steering the
pace tops out near 128 WPM and varies line to line (see `_to_wav`), so this is a real
trade, not an oversight. Before EP03, test whether a slower style prompt plus a tempo nearer
1.0 sounds cleaner than the current split, and keep whichever wins on a listen.

**A counter that climbs must accelerate.** The regex count-up (23 → 555 → 4,067) held the
screen for nearly two minutes at a near-constant rate. Measured on the shipping file, the
first `backtrack` scene advances one step per second for 38.8 seconds. The point of the
scene is that the cost *explodes*, and a linear counter says the opposite of that. Pace the
step rate off the value, not the clock: slow and readable while the numbers are small,
racing once they pass a few hundred.

**Breathing room at the borders.** Text sits too close to the vertical divider and the
bottom edge on some cards. `SAFE = 96` governs the frame margin, but the gutter between a
type block and an internal divider has no rule at all. Give it one, and check it on the
contact sheet the same way everything else here gets checked — by measuring the rendered
ink, not by looking at it and deciding it seems fine.

---

## 11. Motion notes (same review pass, 2026-08-07)

### Already fixed

**Chrome contrast on colour fields.** `_chrome()` drew the channel mark in `MUTED`
regardless of ground. Measured **1.28:1** on the takeaway teal and **1.32:1** on the hook
red, against a 4.5:1 floor — invisible. Field scenes now draw it in `FIELD_INK` at 0.8
alpha: **3.53:1** and **3.54:1**, with the near-black path unchanged at 5.55:1.

### Already built — use it

**Sound effects.** `pipeline/sfx.py` has `pop`, `tick`, `thud`, `whoosh` and `riser`, mixed
into the audio track by `schedule.py` at `SFX_GAIN = 0.35`. EP02 used **one cue in nine
minutes**. Checkbox ticks, sliding boxes and the alarm beat all had a matching effect
sitting unused. This is the cheapest polish available and it costs no quota and no render
time. Add a `ping` for alarms.

**Count-up on big numbers.** `sketch.count_up()` already spins metrics up from zero and is
on by default (`count="off"` disables). It ran on all four EP02 metric cards. If it does not
land hard enough, lengthen it — the mechanism is there.

### Real gaps

**Easing is written but barely wired.** `_ease()` is a cubic ease-out and is applied to
exactly **3 of 24** reveal call sites — the full-bleed field wipes. Every text reveal and
the `_drift` pan run on raw `_phase`, which is linear. That is the uniform-speed feel.
Default reveals to eased and keep linear as the exception.

**The counter must accelerate.** Covered in section 10; the motion note adds the right
treatment — play the first few steps at readable speed to teach the mechanism, then blur and
fast-forward as the count runs away. The scene's subject is that cost explodes; a constant
rate argues against its own point.

**Syntax colour on the regex.** The rule renders as monochrome text in a plain border.
Bracket, operator and literal in three colours makes a 132-character line scannable. No
conflict with anything — worth doing.

### Costed against existing constraints — decide before building

**A slow push (102%→105%) fights the whole-pixel rule.** That rule is not stylistic: a
continuous scale re-antialiases every glyph edge every frame, which is the exact shimmer
that shipped once and had to be found by diffing frames. Cairo re-renders vector type at the
new scale each frame, so it cannot be snapped to the grid the way a translation can. A real
push needs supersampled rendering downsampled to 1080p, roughly **4x the render cost** —
EP02's 15 minutes becomes about an hour. Worth it or not is a call to make deliberately, not
by adding a zoom and discovering the cost later.

**Moving grain has the same problem plus a second one.** Per-frame noise makes every frame
pair differ, which destroys `tools/shimmer.py`'s ability to tell a real still from a bug —
the check that has caught two shipped defects. It also spends h264 bitrate on noise. A
*static* grain or dot-matrix texture gives the same depth with neither cost; take that
unless the moving version is worth losing the check.

**Bloom is feasible.** Blurred copies under the bright elements, per frame, in cairo. Costs
render time proportional to how many elements glow. No constraint conflict.

**The saturated fields — DECIDED at EP03 (2026-08-07).** `FIELD_INK` measured 4.74:1 on
the hook red and 4.59:1 on the takeaway teal, against 16.71:1 for `INK` on the near-black
ground — every card on those two fields was inherently the weakest text in the episode, and
no ink colour could fix it because the *field* was too light. Both fields were darkened by
a straight 0.7 multiply, which keeps the hue: hook `#D0323E` → `#92232B` (8.01:1),
takeaway `#018073` → `#04574E` (8.04:1). The navy context field was already at 14.63:1 and
is unchanged. EP01/EP02 predate the change and keep the lighter fields in their shipped
renders.

**The push zoom — also decided at EP03: not taken.** The 4x render cost buys motion the
eased reveals and the (now actually working) drift pan already provide. Revisit only if a
finished episode still reads static on a full watch.

---

## 12. EP03 viewer notes (2026-08-08) — standing guidance from EP04

Two notes came back on the finished EP03. Neither warrants a re-render; both apply to
every episode after it.

**Audio texture, not just audio punctuation.** The cue set exists (pop, tick, thud,
whoosh, riser, ping) and EP03 used eight cues — but the note asks for *atmosphere*:
low-frequency sound design under the tense stretches, soft UI clicks, and a quiet impact
each time a red ✕ lands. Two concrete moves for EP04:

- **A red cross should land with a sound, every time.** Cross reveal times exist only at
  schedule time (beat start + the checklist's `reveal` pacing), so hand-placed `[SFX:]`
  lines can only hit beat boundaries. The right build is renderer-emitted cues — a scene
  declares its own sub-beat events ("cross at +2.1s, +4.3s, …") and `schedule.py` mixes
  them. That also fixes ticks drifting off their checkboxes whenever the audio re-paces.
- **The ambient bed should react to tension.** `music.py` already synthesises a
  per-chapter drone at `MUSIC_GAIN = 0.05`; give it a darker, sparser variant that a
  section (or a beat range) can opt into for a midnight-sequence feel, rather than
  raising the global gain — texture sits *under* the voice and must never announce itself.

**Stylised terminal for command beats.** The note asks for authentic terminal texture
(e.g. an `rm -rf` prompt snippet), and it can coexist with §4's sourcing rules, which is
why EP03 showed hostnames and a path but no command: **the literal command line appears in
neither primary source** (see ep03 research.md, "Unverified — do not use"). The rule going
forward:

- The *dressing* is always fair game: dark prompt block, chevron, monospace, blinking
  cursor. Worth adding a `prompt="on"` mode to the `code` renderer (composes with
  `syntax="on"` / `hot=`).
- A command may appear inside it only when (a) the source prints it — then it is a quote —
  or (b) it is visibly generic (`rm -rf <data directory>` with a placeholder), staged as
  illustration, never a fabricated literal presented as the incident's real command line.
  The channel's proposition is that its artefacts are the ones the company actually
  published; a plausible invented terminal is the exact thing that would break it.

**Publishing assets, trimmed (2026-08-08).** Measured traffic sources: Direct/unknown
60%, External 20%, Playlists 20%, **YouTube search 0%**. Nobody arrives by query, so
search-optimised copy is dead weight and the assets shrink to what a viewer who already
clicked actually reads:

- **Description: short.** Two hook lines above the fold, one compact paragraph at most
  beneath, then chapters and the primary-source links. No multi-paragraph retelling of
  the episode — EP03's ~350-word version is the last of its kind.
- **Tags: one comma-separated line.** Not a numbered list; they carry ~0% of traffic and
  get one line of effort.
- **`thumbnail_prompt.md`: ONE prompt, the with-text version, plus only the binding
  rules** (palette hexes, crop note, no logos / no fabricated artefacts / check at
  168×94). No concept B/C, no art-only variant, no iterate section.
- Chapters stay full-quality — playlist and direct viewers are the audience that uses
  them. The title keeps optimising for the cold click, which was always its job.

---

## 13. Staging (2026-08-12) — from the EP04 first watch

The note back on EP04's first cut: *"repetitiveness from previous video... just used the
previous components. The video needs life. There should be humans, buildings, images,
animation (not just animating the charts and graphs), and other props. The background
needs to be better."* A sister channel died of exactly this — the viewer sees the same
icons on the same flat void and reads it as recycled, however new the story is.

Binding from EP04 on:

1. **No subject floats in a void.** Every frame starts from the graded, grained backdrop
   (`sketch._backdrop()`), and pictorial subjects stand somewhere: `scenes._stage()`
   draws a night exterior (stars, horizon lift, ground plane) or a room (floor, warm
   wall pool), and `scenes._shadow()` puts a contact shadow under anything with a base.
   An icon may only float when the frame is deliberately abstract (a metric, a quote).
2. **Humans appear wherever the story has humans.** Maintenance crews, responders,
   engineers at desks — the stick rig with props (`ladder`, `toolbox`, `desk`), at human
   scale against buildings (a person is small next to a data centre; the first pass drew
   a giant and it read instantly as wrong).
3. **Each episode must add staging, not just icons.** Reusing a renderer is fine only
   when its frame is re-staged into this story's world (EP04: the smoke alarm gained a
   `figure=` being paged under it; the ledgers gained writing desks and lamp pools).
   An episode assembled purely from the existing library is the failure mode.
4. Shipped renders of EP01–EP03 keep their flat background; this is a forward direction
   change, the same policy as the EP03 field darkening.

### Staging, second pass (2026-08-12) — after the note came back a second time

The first staging pass did not work, and the reason is worth keeping: it was *measured*
as insufficient only after the fact. The note was "the background is still all black" and
"you have reused the same setup", with four timestamps attached. Both were checkable:

- The backdrop spanned **11 levels of 255** top to bottom. A gradient that measures 11
  levels is not a gradient. It now spans ~45 and `BG` was lifted out of near-black
  (`#0E1013` → `#151921`). **Measure the backdrop, do not look at it in a bright room.**
- All four flagged timestamps were EP01/EP02 icons dropped in unchanged — a smoke alarm,
  a CPU dial *twice*, a status board. So: **count renderer reuse per episode.** Any
  renderer appearing twice needs a reason, and a renderer inherited from an older episode
  needs to be doing this story's job, not just filling a slot.

The fix that worked: **photographic plates** (`pipeline/photo.py`, free-licence, treated
into the palette, defocused under the line art) so every pictorial beat is set in a real
place, plus **story-specific scenes replacing generic icons** — a pager waking someone at
a desk, a write physically crossing a continent, a wall of clocks that disagree, a crowd
arriving at sunrise, a fork with one road barricaded, crates being dragged, copies landing
on a shelf.

**The checklist is retired as a default.** Three of them ran 42.6s (8.9%) of EP04 and a
tick-box list is the most chart-like thing the channel can draw. A decision is a fork in a
road; a schedule is objects landing on a shelf; a sequence of steps is weight being moved.
Reach for `checklist` only when the *list itself* is the subject.

A repeat is allowed when it is a **callback that changes state** — EP04 reuses the clock
wall once, with every clock now agreeing, as the payoff of the earlier frame where none
of them did. That reads as resolution. A repeat with no state change reads as reuse.
