"""Swappable TTS layer.

The whole render depends on one thing this module provides: the *measured* duration of
every spoken line. Frame timing is built from these numbers, never estimated, which is
why the video stays in sync without anyone touching an editor.

Backends are chosen by config.TTS_BACKEND:
    gemini      free tier, key in .env, takes delivery direction  (current)
    edge        free, no API key, Microsoft neural voices         (fallback)
    kokoro      fully local ONNX model, no network                (not wired)
    elevenlabs  best quality, needs ELEVENLABS_API_KEY            (not wired)

Swapping backends must never require touching an episode. Everything downstream
consumes Clip objects only.

Clips are cached in two stages — raw (what the backend produced, and on a metered API what
was paid for) and final (raw plus tempo and trim, both free and reproducible). See
_fingerprint(). That split is what makes a pacing change cost nothing.

CLI:
    python -m pipeline.tts --samples              render the voice sample sheet
    python -m pipeline.tts --probe "some line"    hear one line in the current voice
    python -m pipeline.tts --calibrate            measure WPM across speaking rates
    python -m pipeline.tts --backfill <episode>   build the raw cache from existing clips
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import os
import re
import shutil
import subprocess
import time
import wave
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

import numpy as np

from . import config


@dataclass
class Clip:
    """One spoken line, rendered and measured."""
    text: str
    path: Path
    duration: float          # seconds, measured from the decoded wav — never estimated
    silent: bool = False     # a placeholder with no file behind it; see dry_clips()

    @property
    def samples(self) -> np.ndarray:
        return silence(self.duration) if self.silent else read_wav(self.path)


# --------------------------------------------------------------------- ffmpeg
def _ffmpeg() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def _to_wav(src: Path, dst: Path, tempo: float = 1.0) -> None:
    """Decode whatever the backend produced into mono PCM at the channel sample rate.

    `tempo` time-stretches without shifting pitch (ffmpeg's atempo). This is how the
    Gemini backend gets a speaking-rate dial: the API has no rate parameter, and steering
    pace purely through the style prompt tops out around 128 WPM and varies line to line.
    atempo is transparent to about 1.5x; beyond that it starts to sound processed.
    """
    filters = []
    if abs(tempo - 1.0) > 1e-3:
        t = max(0.5, min(2.0, tempo))
        filters += ["-filter:a", f"atempo={t:.4f}"]
    subprocess.run(
        [_ffmpeg(), "-y", "-loglevel", "error", "-i", str(src), *filters,
         "-ac", "1", "-ar", str(config.SAMPLE_RATE), "-sample_fmt", "s16", str(dst)],
        check=True,
    )


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        raw = w.readframes(w.getnframes())
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def write_wav(path: Path, samples: np.ndarray) -> None:
    clipped = np.clip(samples, -1.0, 1.0)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(config.SAMPLE_RATE)
        w.writeframes((clipped * 32767).astype(np.int16).tobytes())


def duration_of(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def silence(seconds: float) -> np.ndarray:
    return np.zeros(int(max(0.0, seconds) * config.SAMPLE_RATE), dtype=np.float32)


def trim_silence(samples: np.ndarray) -> np.ndarray:
    """Cut a clip down to its actual speech, keeping a small pad each side.

    edge-tts returns a fixed-length container for short utterances: "One did not." comes
    back as 1.78 seconds of which 0.72 is speech. Concatenating those raw leaves a full
    second of dead air after every short line. Trimming here puts pacing under the
    pipeline's control via config.LINE_GAP instead of the TTS backend's padding.
    """
    if not config.TRIM_ENABLED or samples.size == 0:
        return samples
    loud = np.abs(samples) > config.TRIM_THRESHOLD
    if not loud.any():
        return samples
    first = int(np.argmax(loud))
    last = len(samples) - int(np.argmax(loud[::-1]))
    head = int(config.TRIM_HEAD_PAD * config.SAMPLE_RATE)
    tail = int(config.TRIM_TAIL_PAD * config.SAMPLE_RATE)
    return samples[max(0, first - head):min(len(samples), last + tail)]


# ------------------------------------------------------------------ normalise
_MARKUP = re.compile(r"\*(.+?)\*")


def spoken_form(line: str) -> str:
    """Strip authoring markup so the voice reads clean text.

    edge-tts takes plain text plus rate/pitch, not arbitrary SSML, so *emphasis* is
    dropped here rather than faked. Backends that do support SSML override this.
    HOUSE_STYLE already bans em-dashes and parentheses in spoken lines; this is a
    safety net for when one slips through, not a licence to write them.
    """
    line = _MARKUP.sub(r"\1", line)
    line = line.replace("—", ", ").replace("–", ", ")
    line = re.sub(r"\s*\([^)]*\)", "", line)
    return re.sub(r"\s+", " ", line).strip()


# ------------------------------------------------------------------- backends
async def _edge_synth(text: str, out_mp3: Path, voice: str, rate: str, pitch: str) -> None:
    import edge_tts
    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await comm.save(str(out_mp3))


def _synth_edge(text: str, out_wav: Path, voice: str, rate: str, pitch: str) -> None:
    tmp = out_wav.with_suffix(".mp3")
    asyncio.run(_edge_synth(text, tmp, voice, rate, pitch))
    _to_wav(tmp, out_wav)
    with contextlib.suppress(OSError):
        tmp.unlink()


def _load_dotenv() -> None:
    """Load case_studies/.env into the environment without clobbering real env vars.

    boto3 reads credentials from the environment, and this repo keeps secrets in a
    gitignored .env rather than in the shell profile, so the two have to be bridged.
    setdefault, not assignment: a value already exported wins, which is what you want
    when overriding a key for one run.
    """
    env = config.ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def _gemini_keys() -> list[str]:
    """Every key we hold, in order.

    Free-tier quota is per project, so separate keys have separate daily allowances and
    rotating across them multiplies the budget. Read explicitly rather than letting the
    SDK pick: it prefers GOOGLE_API_KEY over GEMINI_API_KEY when both are set, and this
    machine has an unrelated GOOGLE_API_KEY in the environment.
    """
    import os
    keys: list[str] = []
    env = config.ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY") and "=" in line:
                val = line.split("=", 1)[1].strip()
                if val and val not in keys:
                    keys.append(val)
    for name in ("GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"):
        val = os.environ.get(name, "").strip()
        if val and val not in keys:
            keys.append(val)
    if not keys:
        raise RuntimeError(
            "No Gemini key. Put GEMINI_API_KEY in case_studies/.env (gitignored)."
        )
    return keys


_GEMINI_LAST = 0.0      # monotonic timestamp of the last successful Gemini call

# (key index, model) pairs known to be out of daily quota. Process-lifetime scope is exactly
# right: a daily cap holds for the rest of this render, but resets at Pacific midnight, so a
# later run should probe again. Without this each batch re-tried every dead combo from the
# top, spending three wasted round-trips per request before reaching a live one.
_GEMINI_DEAD: set[tuple[int, str]] = set()

# Round-robin position across key/model combos, MODULE-LEVEL so it survives between calls.
#
# It used to be a local initialised to 0 inside _synth_gemini and advanced only on
# failure, which meant every clip started at live[0]: key 1 absorbed every request until
# it hit its daily cap, then key 2, and so on. Two things went wrong with that.
#
# 1. A plain rate-limit 429 (not a daily cap) made the call back off and step to the next
#    key — and then the NEXT clip reset the cursor to 0 and hit the same rate-limited key
#    again, discarding the backoff. The throttle was being paid and not used.
# 2. The keys are SHARED with the tiny_rules channel, which round-robins properly
#    (voice.py advances its cursor on every attempt). Two producers where one always
#    attacks key 1 first means they collide on key 1 far more than on the rest.
#
# Advancing on every attempt spreads load evenly and keeps a rate-limited key out of the
# way until the rotation comes back to it. Model-major ordering is unaffected: `combos` is
# still built model-major, so every key is spent on the preferred model before any
# fallback is touched (and with GEMINI_SINGLE_MODEL there is only one model anyway).
_GEMINI_CURSOR = 0

# How many times one line may be re-bought when the model returns speech that is not in
# the script. Three is deliberate: at the measured ~13% defect rate the chance of three
# consecutive bad rolls is under 0.3%, and an unbounded retry would let one pathological
# line eat a whole day's quota on its own.
GEMINI_MAX_REROLLS = 3


def _duration(path: Path) -> float:
    """Seconds of audio in a wav, without decoding the samples."""
    import wave
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def _write_pcm(path: Path, pcm: bytes, rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)


def _synth_gemini(text: str, out_wav: Path, voice: str, rate: str, pitch: str) -> None:
    """Gemini TTS.

    Unlike edge-tts there is no rate or pitch parameter. Delivery is directed in natural
    language via config.TTS_STYLE, which is the reason to use this backend at all: pace and
    emotion become authorable per episode instead of one flat setting for everything.
    Because rate is not a dial, re-run `python -m pipeline.tools.solve_rate <ep>` after
    switching to it.
    """
    import time

    from google import genai
    from google.genai import types

    # Self-throttle. The free tier's limit is low enough that back-to-back calls fail
    # regardless of retry policy; spacing them is what actually makes a full episode work.
    global _GEMINI_LAST
    wait = config.GEMINI_MIN_INTERVAL - (time.monotonic() - _GEMINI_LAST)
    if wait > 0:
        time.sleep(wait)

    prompt = f"{config.TTS_STYLE.strip()}\n\n{text}" if config.TTS_STYLE else text

    # Daily quota is per (project, model), so walk the whole grid of keys x models before
    # giving up. Three keys against three models is roughly 90 requests a day, and a
    # batched episode needs about a dozen.
    keys = _gemini_keys()
    if getattr(config, "GEMINI_SINGLE_MODEL", False):
        # One model for the whole episode, or none. See the note in config.py: a fallback
        # is a different voice, and the fingerprint cannot see that it happened.
        models = [config.GEMINI_TTS_MODEL]
    else:
        models = [config.GEMINI_TTS_MODEL] + [
            m for m in config.GEMINI_TTS_FALLBACKS if m != config.GEMINI_TTS_MODEL]
    # MODEL-MAJOR, not key-major. Daily quota is per (project, model), so the old
    # key-major order exhausted key 0 on the preferred model and then moved key 0 to the
    # NEXT MODEL — changing models every ~10 requests. That is invisible while batching
    # (a dozen requests an episode never leaves the first combo) and catastrophic at
    # solo synthesis, where ~120 requests would walk all three models and narrate one
    # episode in up to three different voices. Spend every key on the preferred model
    # before degrading to a different one.
    combos = [(ki, m) for m in models for ki in range(len(keys))]
    exhausted = _GEMINI_DEAD          # shared across every call in this run, see above

    last: Exception | None = None
    rerolls = 0
    global _GEMINI_CURSOR
    for attempt in range(4 * len(combos)):
        live = [c for c in combos if c not in exhausted]
        if not live:
            raise RuntimeError(
                f"All {len(keys)} key(s) are out of free-tier quota across "
                f"{len(models)} models. Quota resets at Pacific midnight."
            )
        key_i, model = live[_GEMINI_CURSOR % len(live)]
        _GEMINI_CURSOR += 1          # advance on EVERY attempt, not only on failure
        try:
            client = genai.Client(api_key=keys[key_i])
            resp = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice))),
                ),
            )
            pcm = resp.candidates[0].content.parts[0].inline_data.data
            if not pcm:
                raise RuntimeError("Gemini returned no audio data")
            # Gemini emits raw 16-bit mono PCM at 24 kHz; hand it to ffmpeg to resample
            # properly rather than interpolating it here.
            tmp = out_wav.with_suffix(".g24.wav")
            _write_pcm(tmp, pcm, config.GEMINI_TTS_RATE)
            # Deliberately untempo'd. Backends produce raw audio; pace is applied in
            # _derive(), which keeps a rate change a local ffmpeg job rather than a
            # re-synthesis. See _fingerprint().
            _to_wav(tmp, out_wav)
            with contextlib.suppress(OSError):
                tmp.unlink()
            _GEMINI_LAST = time.monotonic()

            # ---- Reject a clip that is far longer than its line, and re-roll it.
            #
            # The style prompt is sent in-band as f"{TTS_STYLE}\n\n{text}", and the model
            # intermittently PERFORMS THE INSTRUCTION as well as the line. Measured on
            # EP05: 2 of 9 clips at the original 70-word style, still 2 of 15 after
            # shortening it to 23 words. It is not deterministic on line length or
            # content — "It had been working exactly as promised." came back at 37.16s,
            # then 2.77s on a probe, then 14.24s in the real run.
            #
            # Shortening the prompt reduces it; nothing removes it. So it is handled here,
            # at the point of purchase, where a re-roll is one request and the run keeps
            # going. `tools/clip_qc.py` still gates the whole episode afterwards, because
            # a check that only runs inline cannot catch clips bought before it existed.
            secs = _duration(out_wav)
            limit = len(text.split()) / (config.SPEECH_WPM / 60.0) * 2.4 + 2.5
            if secs > limit and rerolls < GEMINI_MAX_REROLLS:
                rerolls += 1
                print(f"  [gemini] clip is {secs:.1f}s for a {len(text.split())}-word line "
                      f"(limit {limit:.1f}s) — hallucinated speech, re-roll "
                      f"{rerolls}/{GEMINI_MAX_REROLLS}")
                with contextlib.suppress(OSError):
                    out_wav.unlink()
                continue
            if secs > limit:
                print(f"  [gemini] WARNING: still {secs:.1f}s after {rerolls} re-rolls; "
                      f"keeping it for clip_qc to flag")
            return
        except Exception as exc:                       # noqa: BLE001 — retry any transport error
            last = exc
            msg = str(exc)
            _GEMINI_LAST = time.monotonic()   # a refused call still spends the interval
            wait = min(60.0, 4.0 * (2 ** min(attempt, 4)))
            if "PerDay" in msg or "RequestsPerDay" in msg:
                # Daily cap for this key+model pair. Retrying it is pointless; move on.
                exhausted.add((key_i, model))
                # Counted against `combos`, not len(exhausted): the dead set is shared and
                # may outlive a config change, so subtracting its size could go negative.
                print(f"  [gemini] key {key_i + 1}/{model} out of daily quota, "
                      f"{sum(c not in exhausted for c in combos)} combos left")
                continue
            if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
                print(f"  [gemini] key {key_i + 1}/{model} rate limited, waiting {wait:.0f}s")
            elif "503" in msg or "UNAVAILABLE" in msg:
                # Server-side capacity, not our budget. Another model will usually take it,
                # so move on immediately instead of sitting out the backoff.
                print(f"  [gemini] key {key_i + 1}/{model} unavailable (503), rotating")
                continue
            else:
                print(f"  [gemini] {type(exc).__name__}, retry in {wait:.0f}s: {msg[:120]}")
            time.sleep(wait)
    raise RuntimeError(f"Gemini TTS failed after retries: {last}")


def _synth_kokoro(text: str, out_wav: Path, voice: str, rate: str, pitch: str) -> None:
    raise NotImplementedError(
        "Kokoro backend not wired yet. Install `kokoro-onnx onnxruntime soundfile` and "
        "implement here when/if edge-tts becomes unreliable."
    )


def _synth_elevenlabs(text: str, out_wav: Path, voice: str, rate: str, pitch: str) -> None:
    raise NotImplementedError(
        "ElevenLabs backend not wired yet. Needs ELEVENLABS_API_KEY and a paid plan."
    )


_POLLY = None


def _polly():
    """One boto3 client for the process. Credentials come from .env, same as Gemini's."""
    global _POLLY
    if _POLLY is None:
        import boto3
        _load_dotenv()
        region = os.environ.get("AWS_REGION", "us-east-1")
        if not os.environ.get("AWS_ACCESS_KEY_ID"):
            raise RuntimeError(
                "No AWS_ACCESS_KEY_ID. Put AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / "
                "AWS_REGION in case_studies/.env (gitignored)."
            )
        _POLLY = boto3.client("polly", region_name=region)
    return _POLLY


def _polly_rate(rate: str) -> str:
    """Pipeline rates are signed and relative ("-16%"); Polly's are absolute (20-200%).

    Unsigned values are passed through as absolute, so both conventions are expressible.
    """
    r = (rate or "+0%").strip().rstrip("%")
    pct = 100.0 + float(r) if r[:1] in "+-" else float(r)
    return f"{max(20.0, min(200.0, pct)):.0f}%"


def _synth_polly(text: str, out_wav: Path, voice: str, rate: str, pitch: str) -> None:
    """Amazon Polly.

    Chosen over Gemini for two structural reasons rather than taste. Polly is
    deterministic, so the register cannot wander between lines the way a batched Gemini
    request does — the defect that put 51 of EP02's 130 clips out of tolerance. And
    `<prosody rate>` is a real speaking-rate dial, so `_tempo()` returns 1.0 here and the
    audio is never time-stretched; EP02 stretched every clip by 19%.

    Neural, long-form and generative voices ignore `pitch`, so a non-zero TTS_PITCH is
    reported rather than silently dropped. Generative additionally requires the prosody
    tag to wrap whole sentences, which is already the house rule for a script line.
    """
    from botocore.exceptions import ClientError

    if pitch and pitch not in ("+0Hz", "+0%", "0", ""):
        print(f"  [polly] ignoring TTS_PITCH={pitch}: the {config.POLLY_ENGINE} engine "
              f"does not support prosody pitch")

    ssml = (f'<speak><prosody rate="{_polly_rate(rate)}">'
            f'{xml_escape(text)}</prosody></speak>')

    last: Exception | None = None
    for attempt in range(5):
        try:
            resp = _polly().synthesize_speech(
                Text=ssml, TextType="ssml", VoiceId=voice,
                Engine=config.POLLY_ENGINE,
                OutputFormat="mp3", SampleRate=str(config.POLLY_SAMPLE_RATE),
            )
            tmp = out_wav.with_suffix(".polly.mp3")
            tmp.write_bytes(resp["AudioStream"].read())
            # Deliberately untempo'd, like every other backend: pace is already correct
            # because it was asked for, not applied afterwards. See _tempo().
            _to_wav(tmp, out_wav)
            with contextlib.suppress(OSError):
                tmp.unlink()
            return
        except ClientError as exc:
            last = exc
            code = exc.response.get("Error", {}).get("Code", "")
            if code in ("ThrottlingException", "TooManyRequestsException"):
                wait = 2.0 * (2 ** attempt)
                print(f"  [polly] throttled, waiting {wait:.0f}s")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(f"Polly failed after retries: {last}")


_BACKENDS = {"edge": _synth_edge, "gemini": _synth_gemini, "polly": _synth_polly,
             "kokoro": _synth_kokoro, "elevenlabs": _synth_elevenlabs}


# ---------------------------------------------------------------------- public
def _fingerprint(text: str, voice: str, rate: str, pitch: str, *,
                 stage: str = "final") -> str:
    """Identity of a clip's *content*, not its filename.

    Two stages, because they go stale for different reasons:

        raw     what the backend was actually asked for, and on a metered API, what was
                paid for. Invalidated by the text, voice or model changing.
        final   raw plus local post-processing (tempo, trim), all of which is free and
                reproducible from the raw clip with ffmpeg.

    Splitting them is what makes a pacing change cost nothing. Speaking rate is the setting
    most likely to need several passes to get right, and with a single fingerprint every
    pass re-synthesised the whole episode and burned a day of free-tier quota.

    GEMINI_BATCH belongs in here, and leaving it out was a real bug. How many lines share a
    request changes the audio the model returns — it performs a dozen sentences as a set and
    swings register by up to an octave, where four stay close. With batch size missing from
    the hash, changing it re-used the old audio and reported "0 requests", which looks like a
    working cache and is in fact the exact stale-clip failure this function exists to stop.
    """
    if stage == "raw":
        parts = [text, voice, rate, pitch, config.TTS_BACKEND, str(config.SAMPLE_RATE),
                 # Gemini has no rate dial — delivery lives in the style prompt, the model
                 # id and the batch size, so all three must invalidate the cache.
                 config.TTS_STYLE, config.GEMINI_TTS_MODEL, str(config.GEMINI_BATCH),
                 # Polly's engine changes the voice outright, for the same reason.
                 config.POLLY_ENGINE]
    else:
        parts = [text, voice, rate, pitch, config.TTS_BACKEND,
                 str(config.TRIM_ENABLED), str(config.TRIM_THRESHOLD),
                 str(config.TRIM_HEAD_PAD), str(config.TRIM_TAIL_PAD),
                 str(config.SAMPLE_RATE), config.TTS_STYLE, config.GEMINI_TTS_MODEL,
                 str(config.GEMINI_TEMPO), str(config.GEMINI_BATCH),
                 config.POLLY_ENGINE]
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:16]


def _tempo() -> float:
    """The speaking-rate multiplier for the active backend.

    Only Gemini needs one: edge exposes a real rate parameter, so its clips come back at
    the requested pace and must not be stretched again.
    """
    return config.GEMINI_TEMPO if config.TTS_BACKEND == "gemini" else 1.0


def _raw_path(out_wav: Path) -> Path:
    return out_wav.parent / "raw" / out_wav.name


def _fresh(path: Path, stamp: Path, want: str) -> bool:
    return (path.exists() and stamp.exists()
            and stamp.read_text(encoding="utf-8").strip() == want)


def _derive(raw_wav: Path, out_wav: Path) -> None:
    """Raw clip -> deliverable clip. Local only: tempo, then trim."""
    tempo = _tempo()
    if abs(tempo - 1.0) > 1e-3:
        _to_wav(raw_wav, out_wav, tempo=tempo)
    else:
        shutil.copyfile(raw_wav, out_wav)
    # Trim in place so the cached file is the trimmed one and duration_of() reports the
    # figure the schedule will actually use.
    write_wav(out_wav, trim_silence(read_wav(out_wav)))


def _backfill_raw(out_wav: Path, raw_wav: Path, want_raw: str) -> None:
    """Reconstruct a missing raw clip from a final one that is already correct.

    Only for clips synthesised before the raw cache existed. Undoing the tempo recovers
    audio that is equivalent for re-deriving at a different pace: the trim has already
    happened, but trimming is idempotent, and a second atempo pass at these ratios is
    inaudible. The alternative is re-synthesising audio that was already paid for.
    """
    raw_wav.parent.mkdir(parents=True, exist_ok=True)
    tempo = _tempo()
    if abs(tempo - 1.0) > 1e-3:
        _to_wav(out_wav, raw_wav, tempo=1.0 / tempo)
    else:
        shutil.copyfile(out_wav, raw_wav)
    raw_wav.with_suffix(".fingerprint").write_text(want_raw, encoding="utf-8")


def synth(text: str, out_wav: Path, *, voice: str | None = None,
          rate: str | None = None, pitch: str | None = None,
          cache: bool = True) -> Clip:
    """Render one line and return it measured.

    The cache is content-addressed via a sidecar fingerprint, not keyed on the filename
    alone. Keying on the path means changing the voice or the speaking rate silently
    reuses the old audio and the episode renders in a voice nobody selected — a failure
    that produces a perfectly valid-looking file and is invisible until playback.
    """
    spoken = spoken_form(text)
    voice = voice or config.TTS_VOICE
    rate = rate if rate is not None else config.TTS_RATE
    pitch = pitch if pitch is not None else config.TTS_PITCH

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    stamp = out_wav.with_suffix(".fingerprint")
    want = _fingerprint(spoken, voice, rate, pitch)

    raw_wav = _raw_path(out_wav)
    raw_stamp = raw_wav.with_suffix(".fingerprint")
    want_raw = _fingerprint(spoken, voice, rate, pitch, stage="raw")

    if cache and _fresh(out_wav, stamp, want):
        if not _fresh(raw_wav, raw_stamp, want_raw):
            _backfill_raw(out_wav, raw_wav, want_raw)
        return Clip(text=spoken, path=out_wav, duration=duration_of(out_wav))

    if cache and _fresh(raw_wav, raw_stamp, want_raw):
        # Same words, same voice, different post-processing. Nothing to buy.
        _derive(raw_wav, out_wav)
    else:
        raw_wav.parent.mkdir(parents=True, exist_ok=True)
        _BACKENDS[config.TTS_BACKEND](spoken, raw_wav, voice, rate, pitch)
        raw_stamp.write_text(want_raw, encoding="utf-8")
        _derive(raw_wav, out_wav)
    stamp.write_text(want, encoding="utf-8")

    return Clip(text=spoken, path=out_wav, duration=duration_of(out_wav))


def synth_lines(lines: list[str], out_dir: Path, **kw) -> list[Clip]:
    if config.TTS_BACKEND == "gemini" and config.GEMINI_BATCH > 1:
        return _synth_lines_batched(lines, out_dir, **kw)
    return [synth(t, out_dir / f"line_{i:03d}.wav", **kw) for i, t in enumerate(lines)]


# ----------------------------------------------------------------- no-network clips
def dummy_clips(lines: list[str]) -> list[Clip]:
    """Zero-length placeholders for a `--smoke` run. Spends nothing.

    A smoke render is a VISUAL dry run: schedule.build() gives every visual a fixed 0.6s
    span and lays a silent track under it, so the measured durations are never read. Calling
    the backend anyway bought a whole day of Gemini free-tier quota to produce a fifteen
    second silent video — and smoke is by definition the run you make *before* you are
    confident, which is to say the one you make most often.
    """
    return [Clip(text=spoken_form(t), path=Path(), duration=0.0, silent=True)
            for t in lines]


def dry_clips(lines: list[str], out_dir: Path, **kw) -> tuple[list[Clip], int]:
    """Real cached clips where they exist, estimated silence where they do not.

    For checking the picture at something close to true pace when the API is unavailable —
    an exhausted daily quota, or no network. Nothing here calls a backend, so it can never
    spend anything or block.

    The estimate is only ever used for lines that have no audio yet, and it is flagged in
    the return value so the caller can say so. A file built this way is a *proof*, never a
    deliverable: HOUSE_STYLE's whole timing model is that durations are measured, and
    quietly shipping estimated ones is exactly the silent-corruption class the frame
    verifier exists to catch.
    """
    voice = kw.get("voice") or config.TTS_VOICE
    rate = kw.get("rate") if kw.get("rate") is not None else config.TTS_RATE
    pitch = kw.get("pitch") if kw.get("pitch") is not None else config.TTS_PITCH
    sps = config.SPEECH_WPM / 60.0

    clips, estimated = [], 0
    for i, text in enumerate(lines):
        spoken = spoken_form(text)
        path = out_dir / f"line_{i:03d}.wav"
        want = _fingerprint(spoken, voice, rate, pitch)
        if _fresh(path, path.with_suffix(".fingerprint"), want):
            clips.append(Clip(text=spoken, path=path, duration=duration_of(path)))
        else:
            estimated += 1
            clips.append(Clip(text=spoken, path=path,
                              duration=max(0.45, len(spoken.split()) / sps), silent=True))
    return clips, estimated


# --------------------------------------------------------------- batched Gemini
def _split_by_words(samples: np.ndarray, word_counts: list[int]) -> list[np.ndarray]:
    """Cut one batch narration into per-line clips.

    Gemini's free tier limits REQUESTS PER DAY, not characters, so narrating a whole
    section in one call and cutting it up turns a 137-request episode into 12. That is the
    difference between the free tier being unusable and being enough for an episode a day.

    Strategy: estimate each boundary from cumulative word count, then snap it to the
    quietest point in a window around that estimate. Picking the "N-1 longest silences"
    instead sounds smarter and is not — consecutive short sentences barely pause, so the
    longest silences cluster in the wrong places and the whole batch misaligns.

    This always returns exactly len(word_counts) pieces. It degrades to a proportional cut
    when no silence is found, which is far better than re-requesting audio already paid for.
    """
    # A single-line batch has no interior boundary to solve for, and the DP below indexes
    # `targets` unconditionally. This fires whenever the line count divides to leave a
    # remainder of one — 137 lines at 4 per request does exactly that, and it did not at 12,
    # which is why the crash only appeared after the batch size changed.
    if len(word_counts) <= 1:
        return [samples]

    total_words = max(1, sum(word_counts))
    n = len(samples)
    window = int(config.GEMINI_SPLIT_WINDOW * config.SAMPLE_RATE)
    # Loudness envelope, smoothed, so "quietest point" is not a single stray zero crossing.
    env = np.abs(samples)
    k = max(1, int(0.02 * config.SAMPLE_RATE))
    env = np.convolve(env, np.ones(k) / k, mode="same")

    # Targets as a fraction of total duration, from cumulative word count.
    targets, acc = [], 0
    for w in word_counts[:-1]:
        acc += w
        targets.append(acc / total_words)

    # Candidate boundaries: the centre of every silence long enough to be a sentence break.
    quiet = env < config.TRIM_THRESHOLD
    min_run = int(config.GEMINI_SPLIT_MIN_GAP * config.SAMPLE_RATE)
    runs: list[tuple[int, int]] = []          # (centre, length)
    run_start = None
    for i, q in enumerate(quiet):
        if q and run_start is None:
            run_start = i
        elif not q and run_start is not None:
            if i - run_start >= min_run:
                runs.append(((run_start + i) // 2, i - run_start))
            run_start = None
    if run_start is not None and len(quiet) - run_start >= min_run:
        runs.append(((run_start + len(quiet)) // 2, len(quiet) - run_start))

    # Keep only the longest few. A sentence boundary is a longer pause than a breath
    # taken mid-sentence, and leaving the breaths in lets the aligner cut inside a line.
    keep = max(4 * len(targets), 8)
    runs.sort(key=lambda r: -r[1])
    runs = runs[:keep]
    longest = max((ln for _, ln in runs), default=1) or 1
    runs.sort()
    cands = [c for c, _ in runs]
    bonus = {c: ln / longest for c, ln in runs}

    if len(cands) < len(targets):
        # Not enough real pauses to align to; fall back to a local search per boundary.
        cuts = []
        for frac in targets:
            target = int(n * frac)
            lo, hi = max(0, target - window), min(n, target + window)
            cuts.append(target if hi - lo < 2 else lo + int(np.argmin(env[lo:hi])))
    else:
        # Choose the increasing subset of candidates closest to the targets overall.
        # Deciding each boundary independently mis-assigns whenever the speaker's pace
        # varies between lines, which it does: 85 WPM on one line and 153 on the next.
        m, k = len(cands), len(targets)
        INF = float("inf")
        GAP_W = config.GEMINI_SPLIT_GAP_WEIGHT

        def unit(j: int, b: int) -> float:
            return (cands[j] / n - targets[b]) ** 2 - GAP_W * bonus[cands[j]]

        cost = [[INF] * m for _ in range(k)]
        back = [[-1] * m for _ in range(k)]
        for j in range(m):
            cost[0][j] = unit(j, 0)
        for b in range(1, k):
            best, best_j = INF, -1
            for j in range(m):
                if j > 0 and cost[b - 1][j - 1] < best:
                    best, best_j = cost[b - 1][j - 1], j - 1
                if best < INF:
                    cost[b][j] = best + unit(j, b)
                    back[b][j] = best_j
        end = min(range(m), key=lambda j: cost[k - 1][j])
        cuts, b = [], k - 1
        while b >= 0 and end >= 0:
            cuts.append(cands[end])
            end = back[b][end]
            b -= 1
        cuts.reverse()

    cuts = sorted(set(cuts))
    bounds = [0, *cuts, n]
    # Guarantee the piece count even if two boundaries collapsed onto each other.
    while len(bounds) - 1 < len(word_counts):
        widest = max(range(len(bounds) - 1), key=lambda i: bounds[i + 1] - bounds[i])
        bounds.insert(widest + 1, (bounds[widest] + bounds[widest + 1]) // 2)
    return [samples[bounds[i]:bounds[i + 1]] for i in range(len(word_counts))]


def _synth_lines_batched(lines: list[str], out_dir: Path, **kw) -> list[Clip]:
    out_dir.mkdir(parents=True, exist_ok=True)
    clips: list[Clip] = []
    n = config.GEMINI_BATCH

    for start in range(0, len(lines), n):
        chunk = lines[start:start + n]
        spoken = [spoken_form(t) for t in chunk]
        paths = [out_dir / f"line_{start + i:03d}.wav" for i in range(len(chunk))]

        voice = kw.get("voice") or config.TTS_VOICE
        rate = kw.get("rate") or config.TTS_RATE
        pitch = kw.get("pitch") or config.TTS_PITCH

        want = [_fingerprint(s, voice, rate, pitch) for s in spoken]
        stamps = [p.with_suffix(".fingerprint") for p in paths]
        raws = [_raw_path(p) for p in paths]
        raw_stamps = [r.with_suffix(".fingerprint") for r in raws]
        want_raw = [_fingerprint(s, voice, rate, pitch, stage="raw") for s in spoken]

        # 1. Deliverable clips already correct — nothing to do but top up the raw cache.
        if all(_fresh(p, st, w) for p, st, w in zip(paths, stamps, want)):
            for p, r, rs, wr in zip(paths, raws, raw_stamps, want_raw):
                if not _fresh(r, rs, wr):
                    _backfill_raw(p, r, wr)
            clips += [Clip(text=s, path=p, duration=duration_of(p))
                      for s, p in zip(spoken, paths)]
            continue

        # 2. Raw audio still valid — only the post-processing changed. Re-derive locally.
        if all(_fresh(r, rs, wr) for r, rs, wr in zip(raws, raw_stamps, want_raw)):
            print(f"  [gemini] batch {start}-{start + len(chunk) - 1} "
                  f"re-derived from cache, no request", flush=True)
            for p, st, w, r, s in zip(paths, stamps, want, raws, spoken):
                _derive(r, p)
                st.write_text(w, encoding="utf-8")
                clips.append(Clip(text=s, path=p, duration=duration_of(p)))
            continue

        # 3. Nothing usable. This is the only branch that spends quota.
        merged = out_dir / f"_batch_{start:03d}.wav"
        print(f"  [gemini] batch {start}-{start + len(chunk) - 1} "
              f"({len(chunk)} lines) in one request", flush=True)
        _synth_gemini("\n".join(spoken), merged, voice, rate, pitch)

        # Split before tempo, not after: atempo scales time uniformly, so the cut points
        # are the same either way, and this keeps every raw piece at the pace the model
        # actually produced.
        audio = read_wav(merged)
        words = [max(1, len(s.split())) for s in spoken]
        pieces = _split_by_words(audio, words)

        raws[0].parent.mkdir(parents=True, exist_ok=True)
        for p, st, w, r, rs, wr, s, piece in zip(paths, stamps, want, raws, raw_stamps,
                                                 want_raw, spoken, pieces):
            write_wav(r, piece)
            rs.write_text(wr, encoding="utf-8")
            _derive(r, p)
            st.write_text(w, encoding="utf-8")
            clips.append(Clip(text=s, path=p, duration=duration_of(p)))
        with contextlib.suppress(OSError):
            merged.unlink()

    return clips


# ------------------------------------------------------------------------ CLI
def _samples() -> None:
    out = config.SCRATCH / "voice_samples"
    out.mkdir(parents=True, exist_ok=True)
    print(f"Rendering {len(config.VOICE_CANDIDATES)} candidates -> {out}\n")
    for i, voice in enumerate(config.VOICE_CANDIDATES, 1):
        path = out / f"{i:02d}_{voice}.wav"
        clip = synth(config.SAMPLE_LINE, path, voice=voice, cache=False)
        print(f"  {i:02d}. {voice:<38} {clip.duration:5.2f}s  {path.name}")
    print(f"\nListen, then set TTS_VOICE in pipeline/config.py to the one you want.")


def _probe(text: str) -> None:
    path = config.SCRATCH / "probe.wav"
    clip = synth(text, path, cache=False)
    print(f"{clip.duration:.2f}s -> {path}")
    print(f"spoken as: {clip.text}")


def _calibrate(voice: str | None = None) -> None:
    """Measure real words-per-minute for a voice across speaking rates.

    Measured over a multi-line passage with the real inter-line gaps applied, not over one
    sentence. Two reasons: a single short line is mostly container padding and reports a
    nonsense rate, and the gaps between lines are part of the delivered runtime that the
    word budgets have to account for.
    """
    voice = voice or config.TTS_VOICE
    words = sum(len(spoken_form(l).split()) for l in config.CALIBRATION_LINES)
    gap_total = config.LINE_GAP * (len(config.CALIBRATION_LINES) - 1)
    print(f"voice: {voice}")
    print(f"calibration passage: {words} words over {len(config.CALIBRATION_LINES)} lines "
          f"(+{gap_total:.2f}s of inter-line gap)\n")
    print(f"{'rate':>6} {'speech':>8} {'total':>8} {'WPM':>7}   runtime @1150 words")
    print("-" * 56)
    for rate in ("-8%", "-4%", "+0%", "+6%", "+12%", "+18%"):
        tag = rate.replace("%", "").replace("+", "p").replace("-", "m")
        speech = sum(
            synth(line, config.SCRATCH / f"cal_{tag}_{i}.wav", voice=voice, rate=rate,
                  cache=False).duration
            for i, line in enumerate(config.CALIBRATION_LINES)
        )
        total = speech + gap_total
        wpm = words / total * 60
        mins = 1150 / wpm
        print(f"{rate:>6} {speech:7.2f}s {total:7.2f}s {wpm:7.1f}   "
              f"{int(mins)}m{round(mins % 1 * 60):02d}s")
    print("\nSet config.MEASURED_WPM to the rate you pick. lint.py derives word budgets from it.")


def _backfill(episode: Path) -> None:
    """Give every already-synthesised clip in an episode a raw counterpart.

    Run this BEFORE changing GEMINI_TEMPO. Tempo lives in the final fingerprint, so once it
    changes the deliverable clips go stale, and a clip with no raw copy has to be bought
    again. Backfilling first turns the next pacing change into an ffmpeg job.

        python -m pipeline.tts --backfill episodes/ep01_knight_capital
    """
    from . import script as script_mod

    ep = episode if episode.is_absolute() else config.ROOT / episode
    doc = script_mod.parse(ep / "script.md")
    lines = [b.text for b in doc.spoken]      # same list build.py hands to synth_lines
    out_dir = ep / "out" / "vo"

    made = skipped = missing = 0
    for i, text in enumerate(lines):
        spoken = spoken_form(text)
        final = out_dir / f"line_{i:03d}.wav"
        raw = _raw_path(final)
        want = _fingerprint(spoken, config.TTS_VOICE, config.TTS_RATE, config.TTS_PITCH)
        want_raw = _fingerprint(spoken, config.TTS_VOICE, config.TTS_RATE,
                                config.TTS_PITCH, stage="raw")
        if _fresh(raw, raw.with_suffix(".fingerprint"), want_raw):
            skipped += 1
        elif _fresh(final, final.with_suffix(".fingerprint"), want):
            _backfill_raw(final, raw, want_raw)
            made += 1
        else:
            missing += 1

    print(f"backfilled {made}, already had {skipped}, no usable clip for {missing}")
    if missing:
        print("  (those will be synthesised on the next build — they were already stale)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="TTS layer")
    ap.add_argument("--samples", action="store_true", help="render the voice sample sheet")
    ap.add_argument("--probe", metavar="TEXT", help="synthesise one line in the current voice")
    ap.add_argument("--calibrate", action="store_true", help="measure WPM across speaking rates")
    ap.add_argument("--voice", metavar="NAME", help="override voice for --calibrate")
    ap.add_argument("--backfill", metavar="EPISODE", type=Path,
                    help="build the raw cache from existing clips, before a tempo change")
    args = ap.parse_args()

    if args.samples:
        _samples()
    elif args.calibrate:
        _calibrate(args.voice)
    elif args.probe:
        _probe(args.probe)
    elif args.backfill:
        _backfill(args.backfill)
    else:
        ap.print_help()
