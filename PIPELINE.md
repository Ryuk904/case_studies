# PIPELINE — how an episode gets built

The design goal is that no step requires a human with an editor. The chain is deterministic:
same `script.md` in, byte-identical `episode.mp4` out.

---

## The one idea that makes it work

**Audio is authored first and measured, then video is built to fit it.**

Every other approach (animate first, then narrate to picture) needs a human in an NLE to fix
drift. Here, each line of `script.md` becomes one TTS clip, the clip's duration is *measured* off
the decoded wav, and the frame schedule is generated from those real numbers. Sync is not
maintained — it is structurally impossible to lose.

```
script.md
   │
   │  pipeline/script.py      parse into beats: spoken lines, [VISUAL:], [PAUSE:], [SFX:]
   ▼
 beats
   │
   │  pipeline/tts.py         synth each line -> wav, MEASURE duration (cached on disk)
   ▼
 clips + durations
   │
   │  pipeline/timeline.py    durations -> per-frame schedule: which visual, what progress
   ▼
 frame schedule
   │
   │  pipeline/render.py      cairo draws each frame via sketch.py / diagram.py
   │  pipeline/sfx.py         synthesised effects mixed onto the VO track at beat timestamps
   ▼
 frames + master wav
   │
   │  imageio_ffmpeg          h264 + aac mux
   ▼
 out/episode.mp4  +  out/thumbnail.png  +  out/chapters.txt
```

---

## Module contracts

| Module | Owns | Must never |
|---|---|---|
| `config.py` | every colour, font, size, voice, rate | contain episode-specific anything |
| `tts.py` | synth, trim, **measured** durations, backend swap | estimate a duration |
| `script.py` | parsing `script.md` into beats | render or synth |
| `sketch.py` | rough-stroke primitives: line, box, arrow, text, wash | know what a "server" is |
| `diagram.py` | node-syntax → laid-out, auto-scaled graph | draw directly; it emits sketch calls |
| `scenes.py` | the `[VISUAL:]` renderers, each self-laying-out | let an episode specify a size or coordinate |
| `schedule.py` | beats + durations → frame schedule + master audio | touch cairo |
| `render.py` | frames → mp4, frame-count verification | decide timing |
| `sfx.py` | synthesised pop/whoosh/thud/riser (numpy, no licensing) | load an audio file |
| `lint.py` | HOUSE_STYLE enforcement, source-ledger check | be skippable in a real build |

Named `schedule.py`, not `timeline.py`: `timeline` is already a scene renderer, and two
different things sharing a name in one codebase is a bug waiting to happen.

---

## Speaking-rate calibration

Word budgets are derived from `config.MEASURED_WPM`, and that number must come from a **fully
rendered episode**:

```bash
python -m pipeline.tools.solve_rate episodes/ep01_knight_capital
```

It solves for whichever dial the active backend actually has: `TTS_RATE` on edge, which takes
a real rate parameter, and `GEMINI_TEMPO` on Gemini, which has none and is time-stretched
afterwards with ffmpeg's `atempo`.

Synthetic calibration was wrong twice, by 17% in opposite directions:

- Measuring one line reports the container length, not the speech. edge-tts pads a 0.7s
  utterance out to 1.78s, so a short line looks three times slower than it is.
- Measuring a hand-written passage over-weights digits. `$460 million` is two words and six
  spoken syllables, so a passage chosen to be "representative" of a metrics channel comes out
  far slower than the real script average.

Only a finished episode has the true mix. `solve_rate.py` splits total runtime into
rate-dependent speech and rate-independent fixed cost (gaps, pauses, head/tail silence) and
solves for the rate that hits a target WPM. Re-run it after any voice change.

---

## Caching

TTS clips are **content-addressed**: a `.fingerprint` sidecar holds a hash of everything that
can change the samples. Editing three lines re-synthesises three lines; changing the voice
re-synthesises everything automatically.

Keying the cache on filename alone — the obvious implementation — means changing the voice
silently reuses the old audio and renders a perfectly valid file in a voice nobody selected.
That failure is invisible until playback, which is exactly the kind that ships.

The cache has **two stages**, because they go stale for different reasons:

```
out/vo/raw/line_007.wav     what the backend was asked for, and on a metered API, paid for
out/vo/line_007.wav         the same clip after tempo and trim — free, local, reproducible
```

Speaking rate is the setting most likely to need several passes, and with one fingerprint
every pass re-synthesised the whole episode. On Gemini's free tier that is a day's quota per
attempt. With the split, a tempo change re-derives from `raw/` with ffmpeg and spends nothing:

```
[gemini] batch 0-11 re-derived from cache, no request
```

Clips synthesised before `raw/` existed are recovered rather than re-bought — inverting the
tempo reconstructs a usable raw clip. Do it **before** changing the tempo, while the
deliverable clips are still valid:

```bash
python -m pipeline.tts --backfill episodes/ep01_knight_capital
```

The `final` field order in `_fingerprint()` is load-bearing. It must stay byte-identical to
the original single-stage hash, or introducing the split would itself invalidate every clip
on disk — the exact cost the split exists to avoid.

Frames are not cached; the 1080p render is the expensive step (~20 fps, so ~13 minutes for an
8-minute episode). `--smoke` gives every visual a fixed short span for a ~20 second dry run that
still exercises every scene. Always smoke before a full render.

### The dry runs must not spend quota — this cost a day of it

`--smoke` used to call `synth_lines()` before building the schedule. It never needed to:
smoke mode gives every visual a fixed 0.6s span and lays a silent track under it, so the
measured durations are read exactly nowhere. On EP02 that turned a fifteen-second silent
visual check into 33 Gemini requests, which exhausted all four keys across all three models
and blocked the real render for ten hours until Pacific midnight.

The shape of the mistake is worth remembering beyond this one bug: **smoke is by definition
the run you make before you are confident, so it is the run you make most often, and it was
the most expensive one in the pipeline.** Cost should fall as confidence falls, not rise.

There are now three modes, and only the last one can spend anything:

| | Audio | Cost | Use it for |
|---|---|---|---|
| `--smoke` | none, zero-length placeholders | free | does every scene render at all |
| `--dry` | cached clips only, estimated silence for the rest | free | full length at real pace: composition, shimmer, frame sampling |
| *(none)* | synthesised | API quota | the deliverable |

`--dry` writes `episode_dry.mp4` and `episode_dry_chapters.txt`, deliberately not the
canonical names. Its timings for any unvoiced line are *estimated*, and letting it overwrite
`chapters.txt` would put guessed timecodes into a published description with nothing marking
them as guesses. It is a proof, never a deliverable.

---

## TTS backend: Amazon Polly (from EP03)

Moved off Gemini on 2026-08-07 for two structural reasons, not preference.

**Determinism.** Gemini swings register between sentences inside one batched request. EP02
shipped with 51 of 130 clips beyond 2.5 semitones and a viewer heard it as the narrator
changing sex mid-video. Polly returns the same audio for the same input, so the defect
cannot occur. `voice_qc` stays in the build anyway — a check you remove because it should
not fire is a check that will not fire when it should.

**No time-stretching.** Gemini exposes no rate parameter, so every clip was stretched ~19%
by `atempo`. Polly has a real `<prosody rate>`, so `_tempo()` returns 1.0 and the waveform
is never resampled.

Two consequences fall out for free. Cost is per character, not per request, so there is no
reason to batch: `synth_lines()` already routes any non-Gemini backend to one request per
line, which means clip boundaries are *exact* rather than estimated by `_split_by_words()`.
And the entire quota apparatus — key rotation, model fallback, the 18-second throttle, the
shared daily pool across all three channels — stops applying. An episode is ~6,700
characters against a 100,000/month free allowance.

### The generative engine quantises the speaking rate

Measured 2026-08-07, same sentence, same voice, durations in seconds:

| engine | 70% | 85% | 95% | 100% | 105% | 115% | 130% |
|---|---|---|---|---|---|---|---|
| generative | 12.82 | 12.82 | 9.70 | 9.70 | 9.70 | 7.68 | 7.68 |
| long-form | 15.74 | 12.96 | 11.59 | 11.04 | 10.49 | 9.60 | 8.50 |
| neural | 13.30 | 11.09 | 10.01 | 9.55 | 9.14 | 8.42 | 7.56 |

Generative collapses the percentage onto about three buckets — roughly 117, 159 and 195
WPM. This is what the AWS docs mean by `<prosody>` having "partial availability" for
generative voices, and it is not stated anywhere more plainly than that.

So on generative there is nothing to solve: you take 159 WPM or you time-stretch, and
stretching is what we came here to stop. The word budgets in HOUSE_STYLE were re-derived
upward instead. If fine rate control is ever needed back, long-form and neural both honour
the percentage smoothly.

Two traps this created, both now closed:
- `POLLY_ENGINE` is in the clip fingerprint. Without it, switching engine would serve
  generative audio from a neural cache and look like a working cache — the exact failure
  `GEMINI_BATCH` caused before it was added.
- `MEASURED_WPM` is no longer a target that gets solved for; it is a measurement of a voice
  that cannot be tuned. `lint.py` therefore scales the total-words spec from it rather than
  hard-coding 1,000-1,300, which at 159 WPM would have quietly demanded a 7m50s episode.

## Batch size changes the performance, so it is part of the cache key

Gemini renders a batched request as one performance. Hand it a dozen sentences and it treats
them as a script with speaker turns and swings register by up to an octave; hand it four and
it stays close. Measured on EP01, pitch deviation from the episode median:

| | max | 95th pct |
|---|---|---|
| batch 12, newline-joined | 6.43 st | 5.89 st |
| batch 12, paragraph-joined | 6.12 st | 5.01 st |
| **batch 4** | **3.84 st** | **3.73 st** |
| solo | ~1–4 st, but 137 requests — over a day's quota |

"The eighth did not." came back 11.96 semitones under the median inside a batch of twelve and
1.00 under it alone. Listeners hear that as a second narrator.

`GEMINI_BATCH` therefore belongs in the raw fingerprint, and leaving it out was a live bug:
changing the batch size re-used the old audio and printed `0 requests`, which looks exactly
like a working cache. Check the result with:

```bash
python -m pipeline.tools.voice_qc episodes/ep01_knight_capital
```

Read it comparatively, not as an absolute gate — a short sentence-final line genuinely does
fall several semitones, so some spread is prosody rather than a fault. Compare the same lines
before and after a change.

**Batching also has a degenerate case.** 137 lines at 4 per request leaves a final batch of
one, which has no interior boundary for the splitter to solve. It never fired at 12 because
137 divided differently. Any change to `GEMINI_BATCH` should be smoke-tested against a line
count that leaves a remainder of one.

**Batch size is also a rate change.** The same 1,144 words came back 5% longer at batch 4
than at batch 12 — a short batch is performed with more space around each sentence. So
`GEMINI_TEMPO` has to be re-solved after a batch change exactly as after a voice change;
0.8183 delivered 141.8 WPM against a 145 target until it was re-solved to 0.8379. Cheap to
miss, because 3 WPM is not audible in any single line.

---

## Motion must land on the pixel grid

`scenes._drift()` pans the frame slowly so a long card does not read as a stalled video.
It **rounds the translation to whole pixels**, and that is not a detail.

The first cut translated by `-12 * t` — 0.4px per frame at 30fps. Every glyph edge got
re-antialiased with a different subpixel phase thirty times a second. On screen that reads
as the type vibrating, and the report back was "some of the visual text feels like they are
glitching". It also wastes the h264 bitrate: the encoder re-encodes edges that are not
actually moving.

Measured on a static title card, consecutive-frame differences:

| | changed pixels/frame | max delta |
|---|---|---|
| sub-pixel drift | 15,947 | 141 |
| integer drift | **0** | **0** |

Travel is also a fixed total across the scene, not a rate per second. As a rate, 12px/s slid
a 20-second card 240px off its own layout while a 4-second card barely moved.

To check a suspected shimmer, decode consecutive frames and diff them:

```bash
python -m pipeline.tools.shimmer episodes/ep02_cloudflare_regex --at 20 95 300
```

Pick timestamps inside scenes that are meant to be **still** — a title card mid-hold, a
metric card after its count has landed. It reports changed pixels per frame above a delta of
20, with a budget of 400; h264 at CRF 16 is not lossless so a handful of pixels always
differ by 1 or 2 in flat areas, while a shimmer bug is thousands of pixels differing by 20+,
all of them on a glyph or stroke edge.

A scene with deliberate motion in it — the gauge needle, the backtracking counter, the
dashboard bars — will report MOVING, and that is the feature working. Only a scene that is
supposed to be held still and is not is a bug.

**Moving things must land on the grid too.** The rule is not only about `_drift`. Anything
that translates a whole drawn object across the frame rounds its position: `stick`'s
`travel`, and the wipe edge in `render.run`, which used to slide on fractional pixels for
the length of every transition. Small elements whose *entire job* is to move — an orbiting
dot, a needle, a ripple — are left smooth, because rounding those makes them stutter and
they are never carrying type.

### The pan had been dead, and fixing it exposed a seam

`_drift` computed `k = amount * t / dur`. But `t` is *already* progress 0..1 and `dur` is the
scene length in seconds, so dividing by it cancelled the behaviour the function exists for
and inverted it:

| scene length | total travel delivered | whole-pixel steps |
|---|---|---|
| 3.4s | 3.53px | 4 |
| 15.3s | 0.78px | 1 |
| 25.2s | 0.48px | **0** |
| 38.8s | 0.31px | **0** |

The long cards — the ones the docstring is explicitly about, the ones that read as a stalled
video — were the ones getting no pan at all. It is invisible on a contact sheet, because a
sheet renders a single moment.

**Fixing it immediately broke every hero card.** `sketch.field()` and `sketch.vignette()`
fill "the frame" with a `0, 0, W, H` rectangle, and they are called *inside* the drift
translation — so once the pan actually moved, they landed short of two edges and left a strip
of bare near-black down the red. Measured on a hero metric card: **71% of the rightmost 14px
column was background**. Both now paint in device space, so the colour field is the paper and
the content moves over it. Any future full-bleed primitive has to do the same.

**How to tell a real still from encoder noise.** Diffing the *encoded* file reports a few
hundred changed pixels on scenes that are genuinely frozen — that is h264 ringing around a
keyframe, not motion. Diff raw cairo surfaces instead when you need certainty:

```python
surf, ctx = sketch.new_surface(); scenes.render(ctx, visual, t, dur)
```

The signature to look for is *proportion of frame pairs*, not pixel count. A whole-pixel pan
step changes tens of thousands of pixels on 2–4 pairs out of 90. Sub-pixel drift changes
~16,000 pixels on **every** pair.

---

## Render gotcha (inherited from `tiny_rules`, cost hours there)

Do **not** launch a long render with PowerShell `Start-Process -RedirectStandardOutput/-RedirectStandardError`.
That redirection corrupts the child ffmpeg encoder's stdin pipe: imageio counts every frame it
sends, but ffmpeg only decodes about half, and the file silently loses its front half with no error.

Launch through the Bash tool with a plain shell redirect instead:

```bash
python episodes/ep01_knight_capital/build.py > scratch/ep01.log 2>&1
```

Then always verify — the frame count here must equal the render's own reported count:

```bash
ffmpeg -i episodes/ep01_knight_capital/out/episode.mp4 -map 0:v -f null -
```

---

## Build order for a new episode

1. `research.md` — hook, titles, **SOURCES ledger fetched from primary sources**
2. `python -m pipeline.lint <ep> --sources` — every number in the ledger has a URL + verbatim quote
3. `script.md` — verbatim VO with inline `[VISUAL:]` / `[PAUSE:]` / `[SFX:]`
4. `python -m pipeline.lint <ep>` — banned phrases, word budgets, 45-second rule, layout, TTS-safety
5. `python -m pipeline.tools.sheet --episode <ep>` — look at every visual while changes are cheap
6. `build.py --smoke` (free) → `build.py --dry` (free, full length) → `build.py` full

**Finish the script before the first real synth.** Clips are content-addressed, so editing a
line after synthesis re-buys that line's whole batch, and *inserting* one re-buys every batch
after it — the indices shift, so the fingerprints at those filenames no longer match. On
EP02, four small edits made after the run started turned into seven stale batches. Steps 4
and 5 are cheap and exist precisely so that step 6 happens once.

Step 5 is where layout bugs are supposed to die, and it earns its place every time: one pass
over the six sheets caught a padlock whose shackle ran through the headline and whose label
fell off the bottom edge, a clock caption reading through its own dial, a timeline with no
headline at all, and an end card at caption size. All four would have cost an eight-minute
render each to find in the video, and none of them is visible in the script.

Sample the *finished* file at scene ends, not on a fixed interval. `tools.frames` steps
evenly through the runtime, so it lands mid-reveal and mid-transition and reports clipped
text that is simply a wipe caught halfway. Judge composition at ~85% through a scene, when
every animation has settled.
7. `python -m pipeline.tools.solve_rate <ep>` — confirm the delivered pace; re-derive if it drifted
8. `python -m pipeline.tools.frames <ep>` — sample the finished video
9. `python -m pipeline.tools.voice_qc <ep>` — one voice throughout

**Step 9 is now automatic, because relying on someone to run it did not work.** `build.py`
calls `voice_qc.gate()` after synthesis and raises before the render when more than 10% of
clips sit beyond 2.5 semitones of the episode median. EP02 shipped with **51 of 130 clips**
out of tolerance and a viewer heard it as the narrator changing sex mid-video; every other
check in this list passed that episode clean, because none of them listens.

The gate fires after the audio is cached, so a stop costs no quota — only the fifteen
minutes of rendering something that would need re-rendering anyway. `--ignore-voice`
overrides it.
9. `seo.md` — description, chapters generated from the real timeline, tags, pinned comment
10. Thumbnail, **last**: generate art from `<ep>/thumbnail_prompt.md`, then
    `python -m pipeline.thumbnail --compose art.png --top "..." --bottom "..."`
11. Human: spot-check 2–3 numbers, watch once, upload

Step 7 is not optional after a voice change. Gacrux delivered EP01 at 170 WPM using the tempo
solved for edge — 17% fast, and audible only as "this feels rushed", which is easy to talk
yourself out of. The measurement is not.
