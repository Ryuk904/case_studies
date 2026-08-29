"""Channel-wide constants. Episodes import from here and never hardcode a colour,
font, size, or voice. Changing the channel's look means changing this file only."""

from pathlib import Path

# ---------------------------------------------------------------- identity
CHANNEL = "POSTMORTEM"          # working name — change once the YT channel exists
TAGLINE = "real systems, real numbers, real failures"

# ---------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parent.parent
EPISODES = ROOT / "episodes"
ASSETS = ROOT / "assets"
FONTS = ASSETS / "fonts"
SCRATCH = ROOT / "scratch"

# ---------------------------------------------------------------- video
W, H = 1920, 1080
FPS = 30
SAFE = 96                        # margin; nothing important outside this

# Seconds of wipe when the scene changes. Long enough to register as a cut rather than a
# jump, short enough that it never eats a beat. Costs a second frame render only while a
# transition is running — about 4% of an episode.
TRANSITION = 0.32

# ---------------------------------------------------------------- palette
# Direction, chosen 2026-08-04 from a four-way look test: a dark documentary base for
# authority and contrast, with full-bleed saturated colour fields for section breaks and
# hero beats. The previous warm-paper scheme was replaced outright — the note on it was
# "I don't find it appealing", and the honest diagnosis was that cream + grey + one red is
# near-zero contrast on a phone and reads as a beige PDF.
BG          = (0.082, 0.098, 0.129)   # #151921 dark blue-grey ground
# Lifted from #0E1013 on 2026-08-12. The EP04 note was "the background is still all
# black", and it was measurable: the whole frame sat between 12 and 23 of 255, so the
# grade that was supposedly there spanned 11 levels and no viewer could see it. Dark
# documentary does not mean black paper. INK still measures ~14:1 on this ground.
BG_DEEP     = (0.043, 0.051, 0.067)   # #0B0D11 recessed panel, now DARKER than BG
INK         = (0.949, 0.941, 0.918)   # #F2F0EA off-white type and strokes
MUTED       = (0.478, 0.518, 0.576)   # #7A8493 labels, dimmed geometry
ACCENT      = (0.961, 0.651, 0.137)   # #F5A623 amber — the thread the eye follows
FAIL        = (1.000, 0.278, 0.341)   # #FF4757 the failure path — use sparingly
OK          = (0.024, 0.839, 0.627)   # #06D6A0 healthy path
HILITE      = (0.961, 0.651, 0.137)   # amber doubles as the highlight wash
CODE_BG     = (0.086, 0.098, 0.118)   # #16191E code block fill
CODE_FG     = (0.878, 0.878, 0.859)   # #E0E0DB code text

# Full-bleed section fields. One per script section, so the viewer can *see* the episode
# change chapter without being told. Used for section-opening cards and hero numbers.
# Hook red and takeaway teal darkened 2026-08-07 (EP03): FIELD_INK measured 4.74:1 on the
# old red and 4.59:1 on the old teal, so every card on those fields was the weakest text in
# the episode. A straight 0.7 multiply keeps the hue and lifts both past 8:1 (measured
# 8.01:1 and 8.04:1). Deliberate art-direction change, decided with the channel owner —
# HOUSE_STYLE §11 records the measurement.
FIELDS = {
    "hook":      (0.571, 0.137, 0.170),   # #92232B deep red (was #D0323E at 4.74:1)
    "context":   (0.071, 0.149, 0.227),   # #12263A navy
    "breakdown": (0.086, 0.098, 0.118),   # near-black — the long analytical middle
    "takeaway":  (0.016, 0.341, 0.307),   # #04574E deep teal (was #018073 at 4.59:1)
}
FIELD_INK = (1.000, 0.973, 0.941)         # #FFF8F0 type on a colour field


def field_of(section: str) -> tuple[float, float, float]:
    return FIELDS.get((section or "").lower(), FIELDS["breakdown"])

# ---------------------------------------------------------------- type
# Aesthetic decision (2026-07-31): rough stroke GEOMETRY, clean sans TYPE.
# A full hand-drawn font (Comic Sans / Segoe Print are the only ones installed) reads as
# playful and undercuts the authoritative register this audience expects. Rough boxes and
# arrows give the Excalidraw warmth; clean type keeps it credible.
# Drop Virgil.ttf (Excalidraw's own font, OFL) into assets/fonts/ to get the true look —
# it is first in the chain, so it activates automatically if present.
FONT_SKETCH = ["Virgil", "Segoe Print", "Segoe UI"]
FONT_SANS   = ["Inter", "Segoe UI Variable", "Segoe UI", "Arial"]     # Segoe UI * present
FONT_MONO   = ["JetBrains Mono", "Cascadia Mono", "Consolas", "Courier New"]  # Consolas present

FONT_LABEL = FONT_SANS   # diagram node labels — sans by the decision above

SZ_TITLE   = 132
SZ_METRIC  = 190      # the big number cards
SZ_HEAD    = 56
SZ_ANNOT   = 42       # labels attached to a drawing — see note below
SZ_LABEL   = 34       # diagram node labels
SZ_BODY    = 30
SZ_CODE    = 28
SZ_CAPTION = 24

# SZ_ANNOT exists because SZ_BODY was doing two jobs. A label pinned to an illustration
# ("written in 2003, never removed") carries as much meaning as the drawing it sits under,
# but it was being set at SZ_BODY — sized for running text seen up close, not for a caption
# read at phone size from across a room. On a 1080 frame that is ~2.8% of frame height and
# it disappeared. Annotations are part of the picture; size them like it.

# ---------------------------------------------------------------- sketch look
# The dark direction wants confident, precise geometry, not a sketchbook. Loose double-pass
# strokes read as timid hairlines against a near-black ground, and the doubling muddies
# edges that now have to carry the whole image. Heavier, cleaner, single pass.
STROKE       = 5.0     # base line width
ROUGHNESS    = 0.6     # px of jitter along a stroke; 0 = clean CAD, 3 = very loose
SKETCH_PASSES = 1      # strokes drawn once; 2 was for the hand-drawn look
SEED         = 7       # jitter is seeded so renders are byte-reproducible

# ---------------------------------------------------------------- audio
SAMPLE_RATE = 48000
VO_GAIN     = 1.0
SFX_GAIN    = 0.35     # effects sit well under the voice

# Procedural ambient bed (pipeline/music.py). Synthesised per episode against its own
# chapter marks, so there is nothing to license and the drone changes where the story does.
# Peak amplitude, before the voice is mixed over it — roughly 26 dB down. Set to 0 to mute.
MUSIC_GAIN  = 0.05
HEAD_SILENCE = 0.35    # seconds of silence before the first word
TAIL_SILENCE = 1.20    # seconds after the last word

# Clip trimming. edge-tts pads every utterance to a container length: a 0.5s line comes
# back as a 1.78s file with ~1s of trailing silence. Left alone that dead air lands after
# every short line and makes the edit feel slack, so each clip is trimmed to its real
# speech bounds and the gap between lines is set here instead.
TRIM_ENABLED   = True
TRIM_THRESHOLD = 0.012   # amplitude below this counts as silence
TRIM_HEAD_PAD  = 0.05    # seconds of silence kept before the first sample of speech
TRIM_TAIL_PAD  = 0.08    # ... and after the last
LINE_GAP       = 0.16    # inserted between consecutive spoken lines
SENTENCE_GAP   = 0.30    # ... between lines that end a paragraph/beat

# ---------------------------------------------------------------- TTS
# Backend is swappable:
#   edge        free, no key, Microsoft neural voices — accurate but emotionally flat
#   gemini      free tier, key in .env — takes natural-language delivery direction
#   polly       AWS, keys in .env — deterministic, and a REAL speaking-rate dial
#   kokoro      fully local, no network (not wired)
#   elevenlabs  paid (not wired)
TTS_BACKEND = "gemini"

# Voice names are backend-specific, so keep them side by side rather than making the
# operator remember to change two settings together when switching.
VOICE_BY_BACKEND = {
    "edge": "en-US-BrianMultilingualNeural",
    # Iapetus, chosen 2026-08-12 when the channel moved back to Gemini for emotional
    # range. The owner ruled out Orus and Achernar by ear and left the pick to
    # measurement; on the bake-off passage Iapetus had the widest DYNAMICS (18.4 dB
    # against 12.3-16.1) and near-widest intonation (14.0 st), i.e. it leans on words and
    # backs off them, which is what "doesn't have emotions" was asking for. Gacrux, the
    # incumbent, measured among the FLATTEST (11.4 st / 14.7 dB) and is also the narrator
    # of the tiny_rules channel — two live channels should not share a voice.
    # Convenient accident: Iapetus reads at 168.0 WPM against Gacrux's 168.1, so
    # GEMINI_TEMPO solved on Gacrux transfers almost exactly. Still re-solve after the
    # first rendered episode; a synthetic passage is not a calibration.
    "gemini": "Iapetus",
    "polly": "Ruth",             # chosen 2026-08-07 from the engine bake-off
}

# --- Polly backend --------------------------------------------------------
# generative | long-form | neural | standard. Engine changes the voice completely, so it
# is part of the clip fingerprint — leaving it out would serve generative audio from a
# neural cache and look like a working cache. Same trap GEMINI_BATCH fell into.
#
# generative was picked over long-form and neural on a listen. Neural is the same class as
# the edge backend that was rejected for flatness, so it was never the reason to come here.
# Free tier is 100k characters/month for 12 months; an episode is about 6,700, and all
# three channels together run ~40k/month. After that it is $30 per million, so about 20
# cents an episode.
POLLY_ENGINE = "generative"
POLLY_SAMPLE_RATE = 24000        # mp3 out of Polly; _to_wav resamples to SAMPLE_RATE

# --- Gemini backend -------------------------------------------------------
GEMINI_TTS_MODEL = "gemini-3.1-flash-tts-preview"

# Free-tier quota is per DAY and per MODEL, so an exhausted model is not an exhausted
# account. Falling through this list turns 10 requests/day into roughly 30. Ordered best
# first; the native-audio models are excluded because they only expose bidiGenerateContent.
GEMINI_TTS_FALLBACKS = [
    "gemini-3.1-flash-tts-preview",
    "gemini-2.5-flash-preview-tts",
    "gemini-2.5-pro-preview-tts",
]

# Refuse to fall back to a different MODEL mid-episode. Added 2026-08-12 (EP05).
#
# The fallback list is a survivor of the batched era, when a whole episode was ~12 requests
# and never left the first key+model pair. At GEMINI_BATCH = 1 an episode is ~130 requests
# and blows through every combo: EP05's second run exhausted the preferred model on all
# four keys within seven log lines and then bought roughly forty clips from two different
# fallback models. A different model is a different voice, so that is one episode narrated
# by up to three people.
#
# Worse, it was SILENT: `_fingerprint()` records `config.GEMINI_TTS_MODEL` — the model we
# asked for — not the model that actually served the request. So a fallback clip's
# fingerprint claims it is the preferred model's audio and it will never be re-bought.
# Same class of bug as GEMINI_BATCH and POLLY_ENGINE missing from the key, both already
# documented above.
#
# With this True, a run stops when the preferred model is out and resumes there tomorrow.
# That is the behaviour solo synthesis needs: clips are content-addressed, so a stall
# costs nothing but time, while a voice change costs the episode.
GEMINI_SINGLE_MODEL = True

GEMINI_TTS_RATE = 24000        # the API always returns raw 16-bit mono PCM at 24 kHz

# Gemini exposes no speaking-rate parameter. This time-stretches without changing pitch,
# restoring a predictable rate dial.
#
# Solved from a fully rendered EP01 on Gacrux, which is the only calibration that does not
# lie: 1144 words, 375.1s of trimmed speech plus 28.8s of gaps and pauses at tempo 0.97
# = 403.9s, i.e. 170.0 WPM. Far too fast for a general audience being taught a mechanism.
# Scaling the speech portion alone (the gaps are fixed) to the 145 WPM the house style is
# built on gave 0.8183 and a 7m53s episode.
#
# Re-solved after dropping GEMINI_BATCH 12 -> 4: the same words came back 5% longer, because
# the model paces a short batch differently from a long one. Batch size is therefore a rate
# change as well as a timbre change, and both need re-solving. 0.8183 delivered 141.8 WPM;
# 0.8379 puts it back on 145.
#     python -m pipeline.tools.solve_rate <episode>     re-solve after any voice change
# Changing this is now free: tempo is applied to a cached raw clip, so no API request is
# spent. Run `python -m pipeline.tts --backfill <episode>` first on any episode whose clips
# predate the raw cache.
GEMINI_TEMPO = 0.972

# Free-tier TTS is rate limited to a handful of requests per minute. Firing a whole
# episode at it unthrottled fails most calls with 429 even with aggressive backoff, so
# space them deliberately: ~110 lines at 18s spacing is a ~35 minute background render,
# which is fine, whereas hammering and retrying is neither faster nor reliable.
GEMINI_MIN_INTERVAL = 18.0

# Lines narrated per request. Measured against EP01, pitch deviation from the episode
# median (95th percentile):
#     batch 12, newline-joined    5.89 semitones
#     batch 12, paragraph-joined  5.01
#     batch  4                    3.73
#     solo  (batch 1)             ~1-4      <- CHOSEN from EP05
# Handed several sentences at once the model performs them as a SET and swings register by
# up to an octave; "The eighth did not." came back 11.96 semitones below the median batched
# and 1.00 below it alone. A listener hears that as a second narrator, and it is exactly the
# defect the channel owner reported on EP02 ("the narrator switches from a female to a male
# voice around 02:54" - 51 of 130 clips out of tolerance).
#
# **Solo is now the setting, because batching is the cause and solo is the cure.** It costs
# one request per line - about 120 for an episode - against a free-tier ceiling of roughly
# 4 keys x 3 models x 10/day. That is a margin of a handful of requests, so a run MAY hit
# quota partway through. That is safe and cheap: clips are content-addressed on disk, so
# re-running the build the next day resumes from cache and only buys what is missing.
# Never "fix" a quota stall by raising this number - that trades the defect back in.
GEMINI_BATCH = 1
# How far either side of the word-count estimate to hunt for a quiet point to cut on,
# used only when there are too few real pauses to align against.
GEMINI_SPLIT_WINDOW = 0.55     # seconds
GEMINI_SPLIT_MIN_GAP = 0.12    # seconds of quiet that can count as a sentence boundary
# How strongly the aligner prefers a long pause over one closer to the word-count estimate.
# Deviations are squared fractions of total duration (~1e-4..2e-3), so this is the scale
# at which "that was a proper sentence break" outweighs "that was near where I expected".
GEMINI_SPLIT_GAP_WEIGHT = 0.0012

# Delivery direction, prepended to every line. This is the whole reason to prefer Gemini:
# pace and emotion become part of the episode's authorship instead of one global rate dial.
# The model speaks only the line, not the instruction.
# Measured against this exact wording: asking for "a beat of space before a revelation"
# and "measured and calm" dropped delivery to 82 WPM, which would run a 1,150-word script
# to nearly 14 minutes. Drama has to be asked for without asking for slowness.
#
# There is a REAL TENSION in this string, and it is worth naming rather than discovering.
# The channel came back to Gemini (2026-08-12) because Polly's generative engine "doesn't
# have emotions" - so this prompt has to ask for feeling. But the anti-swing clause below
# asks the model to hold one register, and register variation is part of how a reader sounds
# expressive. Pushed too far in either direction you get a flat read or a second narrator.
#
# The resolution: ask for emotional COLOUR (weight, intent, landing a number) while pinning
# vocal IDENTITY (same person, same pitch centre). Emotion is allowed in emphasis and pace;
# it is not allowed in who is speaking.
#
# At solo synthesis the swing risk is far lower than it was at batch 4 or 12 - the model is
# no longer performing a set - so this can afford to ask for more than the batched version
# did. Verify after ANY change to this string with pipeline/tools/voice_qc.py, and remember
# the style text is part of the clip fingerprint, so editing it re-buys the whole episode.
#
# Do NOT ask for "quietly" or "softly": the model whispers, and a whispered line in the
# middle of an episode is unusable. Do not ask for slowness either - "a beat of space before
# a revelation" plus "measured and calm" measured 82 WPM, which would run a 1,150-word
# script to nearly 14 minutes. Drama has to be asked for without asking for slow.
# CHANGED 2026-08-12 (EP05), for two independent reasons.
#
# 1. THE OWNER ASKED FOR DRIER, FUNNIER DELIVERY, in the register of Fireship: quick,
#    clipped, deadpan, faintly amused rather than warm and announcer-ish.
#
# 2. THE PREVIOUS 70-WORD VERSION WAS CORRUPTING CLIPS. The prompt is sent in-band as
#    f"{TTS_STYLE}\n\n{text}" (tts.py), and when a line was short relative to the
#    instruction the model sometimes PERFORMED THE INSTRUCTION as well as the line.
#    Measured on the first nine clips of EP05, 2 were defective (22%):
#
#        line 6   16 words   31.04 s   ( 6.0x expected)
#        line 7    7 words   37.16 s   (15.4x expected)
#
#    Both were 78% voiced across their whole length — continuous hallucinated speech, not
#    silence. It is intermittent, not length-deterministic: line 1 is also seven words and
#    came back correct. Re-probed on this shorter version, the same two lines returned
#    6.96 s and 2.77 s. **Keep this prompt short.** A long delivery direction reads to the
#    model as content, and the failure it causes is invisible to voice_qc, which measures
#    pitch. `pipeline/tools/clip_qc.py` now gates on duration and exists because of this.
#
# Rate is NOT the reason for the change and did not move: raw 153.2 WPM here against
# ~152 for the old style, measured on the same lines. Whatever the pace problem is, the
# style prompt is not the dial for it.
# THE LAST CLAUSE IS LOad-BEARING — measured, and re-added 2026-08-12 after removing it.
# The first short version dropped the old prompt's "do not drop into a lower register for
# short sentences", and EP05's dry rewrite had deliberately made most lines SHORT. Result
# on 56 clips: 27% beyond 2.5 semitones from the episode median, against a voice_qc halt
# threshold of 10%. The worst offenders were the shortest lines, exactly as the old
# comment predicted:
#     "It is called Consul."           4 words   +4.01 st
#     "The trigger was an improvement." 5 words   -4.68 st
# Solo synthesis reduces register swing; it does not remove it. Keep this clause, and keep
# the whole prompt short — see the hallucination note above.
TTS_STYLE = (
    "Dry, deadpan tech commentary. Quick and clipped, faintly amused, never warm or "
    "announcer-ish. Land the numbers hard. One narrator, one pitch centre from first word "
    "to last. Never drop into a lower register for a short sentence."
)

# Gemini prebuilt voices worth auditioning for a narrator role.
GEMINI_VOICE_CANDIDATES = [
    "Charon",        # informative
    "Rasalgethi",    # informative, warmer
    "Alnilam",       # firm
    "Gacrux",        # mature
    "Schedar",       # even
    "Iapetus",       # clear
    "Orus",          # firm, lower
    "Achernar",      # soft
]

# Set after the user picks from the sample sheet (pipeline/tts.py --samples).
def voice() -> str:
    """The voice for the active backend."""
    return VOICE_BY_BACKEND.get(TTS_BACKEND, "en-US-BrianMultilingualNeural")


TTS_VOICE = VOICE_BY_BACKEND[TTS_BACKEND]
# Polly's generative engine QUANTISES prosody rate into about three buckets — measured
# 70% and 85% returning byte-identical durations, likewise 95/100/105 and 115/130. So this
# is not a dial here, it is a choice of slow (~117 WPM), medium (~159) or fast (~195).
# Medium is the only usable one, hence +0%. Long-form and neural honour the rate smoothly
# if fine control is ever needed back.
TTS_RATE  = "+0%"       # generative's medium bucket; anything 95-105% is the same audio
TTS_PITCH = "+0Hz"

# Real measured words-per-minute for TTS_VOICE at TTS_RATE. lint.py derives the
# per-section word budgets from this instead of assuming 140 WPM.
# Re-run `python -m pipeline.tts --calibrate` whenever voice or rate changes.
# Solved from a fully rendered episode, which is the only calibration that is not a guess.
#
# Two earlier attempts were both wrong, in opposite directions:
#   138.9  measured on one untrimmed line   -> counted edge-tts padding as speech
#   140.2  measured on a synthetic passage  -> passage was far more digit-dense than a real
#                                              script, and digits are slow to speak
# Ground truth from EP01: 1125 words, 383.1s of trimmed speech plus 27.8s of gaps, pauses
# and head/tail silence = 410.8s at rate -4%, i.e. 164.3 WPM. Solving that model for the
# ~140 WPM the house style wants gives -19%, which drags; -16% lands ~145 and still sounds
# deliberate. Re-solve with `python -m pipeline.tools.solve_rate <ep>` after any voice change.
# Polly Ruth / generative, solved from the RENDERED EP03 on 2026-08-07 (ground truth):
# 1286 words over 420.8s of trimmed speech + 24.4s of gaps, pauses and head/tail silence
# = 445.2s at TTS_RATE +0%, i.e. 173.3 WPM. The synthetic-passage figure used before the
# first render said 159.0 — 8.3% slow, the third time that method has been wrong. Since
# generative quantises the rate into buckets, this number is a MEASUREMENT of the voice's
# middle bucket, not a target: word budgets scale from it, the voice does not move to it.
MEASURED_WPM = 173.3

# Pure speech rate, excluding gaps, pauses and head/tail silence. MEASURED_WPM is an
# episode-wide average that already absorbs those; using it per-section silently
# under-counts any section carrying more than its share of [PAUSE:] directives. The hook
# is exactly that section, and the 45-second rule is the one deadline that must not slip,
# so lint.py models sections as speech + explicit pauses + inter-line gaps instead.
# Derived from EP01 on Gacrux: 1144 words over 375.1s of speech at tempo 0.97 scales to
# 444.6s at tempo 0.8183, i.e. 154.4 WPM of actual talking. Within 0.2 of the figure the
# edge backend produced at its own solved rate, which is a useful sanity check: the house
# style's pacing targets are a property of the writing, not of whichever voice reads it.
# Polly Ruth / generative, from the same rendered-EP03 solve as MEASURED_WPM:
# 1286 words over 420.8s of pure speech = 183.4. The synthetic figure said 165.8,
# 9.6% slow.
SPEECH_WPM = 183.4

# Candidates rendered by --samples. Male/female, US/UK, warm//authoritative.
VOICE_CANDIDATES = [
    "en-US-AndrewMultilingualNeural",   # warm, measured, documentary
    "en-US-BrianMultilingualNeural",    # deeper, news-anchor
    "en-US-GuyNeural",                  # crisp, neutral
    "en-US-ChristopherNeural",          # older, authoritative
    "en-GB-RyanNeural",                 # UK, dry
    "en-US-EmmaMultilingualNeural",     # female, warm
    "en-US-AvaMultilingualNeural",      # female, bright
    "en-GB-SoniaNeural",                # UK female, cool
]

SAMPLE_LINE = (
    "On August 1st, 2012, Knight Capital lost $460 million in 45 minutes. "
    "The cause was a deployment that reached seven of its eight servers."
)

# Calibration passage: representative of real scripts, mixing long explanatory sentences
# with the short punch lines the house style favours. Measuring on one long sentence
# overstates the rate, because short lines carry proportionally more gap.
CALIBRATION_LINES = [
    "On the morning of August 1st, 2012, Knight Capital lost $460 million in 45 minutes.",
    "Knight was not a startup running an experiment.",
    "It was one of the largest market makers in American equities.",
    "It was a routine deployment that reached seven of its eight servers.",
    "One did not.",
    "Power Peg was still counting.",
    "Nothing was updating the number it counted.",
    "Those 212 orders produced over 4 million executions across 154 stocks.",
]
