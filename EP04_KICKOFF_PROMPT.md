# EP04 kickoff — paste the block below into a new chat

Everything between the rules is the prompt. Nothing above or below it needs to go.

---

Build episode 4 of the POSTMORTEM channel, in `C:\Users\abhis\OneDrive\Desktop\case_studies`.

Pure-Python pipeline: cairo draws every frame, ffmpeg muxes, no video editor is ever
opened. EP01 (Knight Capital), EP02 (Cloudflare) and EP03 (GitLab) are done and rendered.

READ FIRST, in this order:
  1. `HOUSE_STYLE.md` — all 12 sections. Section 2's word budgets were corrected against
     the rendered EP03 (173.3 WPM, budgets 1,285–1,464 words) and are no longer
     provisional. Sections 10–11 are EP02's viewer notes; **section 12 is EP03's viewer
     notes and contains pipeline work you are expected to BUILD this episode** — see below.
  2. `PIPELINE.md` — especially "TTS backend: Amazon Polly", the numbered build order, and
     the voice gate.
  3. `episodes/ep03_gitlab_database/` — the most current worked example. Read
     `research.md` for how a source ledger is built, including its "derived, not quoted",
     "contradictions", and "do not use" sections. That episode also caught a shipped
     factual error in an *earlier* episode's end card by checking the promise against the
     source — which brings us to:

EPISODE: GitHub's outage of 21 October 2018. Routine maintenance severed the link between
their East and West Coast data centres for 43 seconds. Automated failover (Orchestrator,
following Raft consensus) moved the database primaries west. When the link came back, both
coasts held writes the other had never seen, so they could not simply switch back — and
unwinding it took about a day.

EP03's end card promises this episode. The exact spoken line is in ep03's `script.md`:
"a 43 second network hiccup splits GitHub's database in two, and putting it back together
takes a full day." **VERIFY BOTH NUMBERS against the source before anything else.**
TOPICS.md records the degradation as 24 hours 11 minutes; EP02 shipped an end card saying
"four backups" when the source said five, and that mismatch is exactly the kind of thing
this check exists to catch. If the promise and the source disagree, speak the true number
and tell me.

PRIMARY SOURCE: GitHub's own post-incident analysis,
https://github.blog/2018-10-30-oct21-post-incident-analysis/
Verify that URL resolves and use the canonical one if it has moved (github.blog has
reshuffled paths before; EP03's incident doc had gone 410 and had to be traced to a
republication). If the analysis references GitHub's earlier day-of incident report, fetch
that too as a second primary source. Read both in full. Do not source figures from
summaries, news articles or search snippets. Every spoken number needs a row in
`research.md` with a URL and the verbatim sentence containing it. Where sources disagree,
say so in research.md and do not speak the contested figure.

NON-NEGOTIABLE:
- General audience, not engineers. Someone who does not know what a database primary or a
  failover is has to follow the whole episode. Analogy over jargon. This is the single
  most important rule and EP01's first script was rejected outright for breaking it. The
  hard part of this episode is split brain: find the plain-language picture (two copies of
  the ledger both written in during those 43 seconds, and no honest way to merge them) and
  build the episode on it.
- Thumbnails are mine. Deliver `thumbnail_prompt.md` for me to paste into ChatGPT. Do not
  generate the image or offer to. Put it next to EP01–EP03's thumbnails on the channel
  page before committing to a concept — three dark images already sit there.
- All motion lands on whole pixels. See PIPELINE.md, "Motion must land on the pixel grid".
- Pictures over text. Measure the rendered ink in SECONDS of screen time, never eyeball it.
- Look at the contact sheet before rendering (`python -m pipeline.tools.sheet --episode <ep>`).
- Never name an individual engineer. The system failed, not the person.
- No fabricated artefacts: no invented command lines, no fake dashboards or status pages.
  A shown command must be printed by the source or be visibly generic (HOUSE_STYLE §12).

TTS — settled, no surprises expected:
Amazon Polly, voice Ruth, generative engine, keys in `.env`. Billing is per character
(~6,700/episode against a 100,000/month free allowance), so synthesis is effectively free:
no quota, no rationing, no batching, one request per line. `--smoke` and `--dry` never
call the backend. `MEASURED_WPM = 173.3` and `SPEECH_WPM = 183.4` are ground truth solved
from the rendered EP03 — write to the §2 table as it now stands. Still run
`python -m pipeline.tools.solve_rate <ep>` after the render to confirm (it is free); a
drift of more than ~2% means something changed and I want to know. build.py runs voice_qc
automatically and halts the render if the narration is not in one voice; EP03 passed with
only one-word dramatic beats flagged, which is prosody. If the gate fires, tell me — do
not pass `--ignore-voice`.

WHAT TO BUILD THIS EPISODE — the three §12 features, specced from EP03's viewer notes:
1. **Renderer-emitted sub-beat SFX.** A red cross (or any marked reveal) should land with
   its own quiet thud/tick at its actual reveal moment. Those moments only exist at
   schedule time, so scenes must declare their cue times and `schedule.py` must mix them —
   hand-placed `[SFX:]` lines can only hit beat boundaries. Design it so EP01–EP03 render
   byte-identically unless a scene opts in.
2. **Tension-aware ambient bed.** `music.py` already synthesises a per-chapter drone at
   `MUSIC_GAIN = 0.05`. Add a darker, sparser variant a section or beat range can opt
   into. Texture sits under the voice; it must never announce itself.
3. **`prompt="on"` dressing for the `code` renderer** — dark prompt block, chevron,
   monospace, blinking cursor; composes with `syntax="on"` and `hot=`. Command content
   rules are in §12.

Also use what EP03 added: eased reveals are the default, `checklist` takes `reveal=` so a
narrated list lands row by row, `code` takes `syntax="on"`/`hot=`, `ping` exists for
alarms, climbing counters accelerate. And repeat EP03's hold-rule audit: after the first
full render, grep the `[scene] ... @ ...s` lines from the build log and check every scene
on screen 15 seconds or longer still has something moving at second fourteen — that audit
caught two violations on EP03 that the contact sheet cannot show.

This story will likely want one or two new pictorial renderers (two data centres, a link
that cuts and heals, writes landing on both sides of a divide). Build them in
`pipeline/illustrate.py`/`scenes.py` following the existing self-laying-out contract
rather than forcing the story through `diagram`. Max 7 nodes on screen; subjects own
50–70% of the frame.

DELIVERABLES:
  `research.md`, `script.md`, `seo.md`, `thumbnail_prompt.md`, and `out/episode.mp4`
  verified frame-for-frame. Copy `episodes/_template/build.py` into the new episode folder
  first — EP02's first launch failed because it was missing. End card teases EP05 (Roblox,
  73 hours — see TOPICS.md), with its numbers added to the ledger so lint passes.

  **seo.md and thumbnail_prompt.md are TRIMMED from this episode on** (HOUSE_STYLE §12,
  "Publishing assets, trimmed" — search traffic is 0%, so write for the viewer who
  already clicked): description is two hook lines plus at most one short paragraph, then
  chapters (from the real timeline, full quality) and source links; tags are ONE
  comma-separated line; thumbnail_prompt.md is ONE with-text prompt plus only the binding
  rules — no alternate concepts, no art-only variant. The title still extends the
  channel's title pattern (see ep03 seo.md's triptych table) and still optimises the cold
  click.

CHECKPOINT: show me the hook and the source ledger before you write the script.

Then tell me what you are least confident about.

---
