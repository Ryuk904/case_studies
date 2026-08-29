"""Scene renderers — the things `[VISUAL: <name> ...]` can name in script.md.

Every renderer here is self-laying-out: it measures its own content and fits it inside the
safe area. An episode never specifies a coordinate or a point size. That is deliberate —
the first preview render had a metric overflowing 1200px into a code block because sizes
were hardcoded, and any system where the author can specify a size is a system where that
happens again on episode 14 at 2am.

Signature contract: render(ctx, visual, t, dur) where
    visual  script.Visual — the parsed directive
    t       0..1 progress through this visual's screen time
    dur     that screen time in SECONDS

`dur` matters: animation timings are absolute, not proportional. A diagram should take
about two and a half seconds to draw itself whether the beat lasts four seconds or forty.
Driving draw-on from `t` alone makes short beats frantic and long beats glacial.
"""

from __future__ import annotations

import math

import cairo

from . import config, diagram, illustrate, sketch, stickman
from .script import Visual

CONTENT_W = config.W - config.SAFE * 2


def _chrome(ctx: cairo.Context, sub: str = "", on_field: bool = False) -> None:
    """Persistent channel mark, top-left. Present on every scene so cuts feel continuous.

    `MUTED` is chosen for the near-black ground, where it sits at 5.03:1 — subordinate but
    legible. On a saturated colour field it disappears: measured 1.28:1 against the takeaway
    teal and 1.32:1 against the hook red, where 4.5:1 is the floor for text this size. So a
    field scene draws the mark in the field ink instead, at 0.8 alpha to keep it from
    competing with the headline (3.5:1 on the saturated fields, ~10:1 on the dark ones).
    """
    col = config.FIELD_INK if on_field else config.MUTED
    a = 0.80 if on_field else 1.0
    sketch.text(ctx, config.CHANNEL, config.SAFE, config.SAFE - 20,
                config.SZ_CAPTION, col, config.FONT_SANS, alpha=a)
    if sub:
        sketch.text(ctx, sub, config.W - config.SAFE, config.SAFE - 20,
                    config.SZ_CAPTION, col, config.FONT_SANS, align="right", alpha=a)


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def _phase(t: float, dur: float, seconds: float, delay: float = 0.0) -> float:
    """Progress 0..1 of an animation lasting `seconds`, starting `delay` in."""
    if dur <= 0:
        return 1.0
    return max(0.0, min(1.0, (t * dur - delay) / max(seconds, 1e-6)))


def _rphase(t: float, dur: float, seconds: float, delay: float = 0.0) -> float:
    """Eased reveal progress — the DEFAULT for anything drawing on (HOUSE_STYLE §11).

    `_ease` existed from EP02 but was wired to 3 of 24 reveal sites, so most motion ran
    linear and read cheap. Reveals ease out; raw `_phase` stays for clocks that must be
    literal (a counter's pacing, `world`'s 2.29-second wave, `windows`' fall schedule),
    where easing would misstate the quantity the scene is about.
    """
    return _ease(_phase(t, dur, seconds, delay))


def _drift(ctx: cairo.Context, t: float, dur: float, amount: float = 16.0) -> None:
    """A very slow pan across the frame, snapped to whole pixels.

    Held perfectly still, a 20-second card reads as a stalled video. A little movement
    keeps the frame alive — but it has to land on the pixel grid.

    Sub-pixel translation was the cause of the "glitching text" in the first cut. Moving the
    origin by 0.4px a frame re-antialiases every glyph edge thirty times a second, which
    reads as the type vibrating and makes h264 spend its bitrate on the shimmer instead of
    the edges. Measured on a static title card: 15,947 changed pixels per frame before,
    0 after.

    Travel is a fixed total across the scene rather than a rate per second. As a rate, the
    old 12px/s slid a 20-second card 240px off its own layout while a 4-second card barely
    moved at all.

    `t` is ALREADY progress 0..1 through this scene; `dur` is only there so animations can be
    timed in real seconds. Dividing t by dur therefore cancelled the very behaviour this
    function exists for, and inverted it: a 25-second card ended up with 0.48px of total
    travel, which rounds to a dead stop, while a 3.4-second card got 3.5px. The scenes that
    read as stalled video were exactly the ones receiving no pan at all.

    Invisible on a contact sheet, because a sheet renders one moment. Found by diffing raw
    cairo surfaces frame to frame with no encoder in the path, which is also the only way to
    tell a real still from h264 ringing around a keyframe.
    """
    if dur <= 0:
        return
    k = amount * min(1.0, max(0.0, t))
    ctx.translate(-round(k), -round(k * 0.35))


# ------------------------------------------------------------------- staging
# EP04 first-watch note: "the video needs life... humans, buildings, props... the
# background needs to be better." Icons on a featureless void read as recycled clip-art
# however good the icon. These helpers put subjects IN somewhere: a ground to stand on,
# a sky or a room behind them, and a contact shadow so nothing floats.


def _shadow(ctx: cairo.Context, cx: float, gy: float, w: float,
            alpha: float = 0.42) -> None:
    """Soft contact shadow under a subject. The single cheapest cure for floating."""
    rx = w * 0.55
    ry = max(10.0, w * 0.075)
    ctx.save()
    ctx.translate(cx, gy)
    ctx.scale(1.0, ry / rx)
    g = cairo.RadialGradient(0, 0, rx * 0.05, 0, 0, rx)
    g.add_color_stop_rgba(0, 0, 0, 0, alpha)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.0)
    ctx.set_source(g)
    ctx.rectangle(-rx, -rx, rx * 2, rx * 2)
    ctx.fill()
    ctx.restore()


def _photo(ctx: cairo.Context, v: Visual, default: str = "", **kw) -> bool:
    """Lay this scene's photographic plate, if it has one.

    `photo="none"` opts a scene out of its renderer's default plate.
    """
    name = v.get("photo") or default
    if not name or name == "none":
        return False
    return sketch.photo_backdrop(ctx, name, **kw)


def _stage(ctx: cairo.Context, kind: str, t: float, gy: float) -> None:
    """An environment behind the subject: "night" is an exterior (stars, horizon lift,
    ground), "room" an interior (floor, warm wall pool). Painted in device space like
    sketch.field(), so the pan can never leave a seam of bare backdrop at the edges."""
    ctx.save()
    m = ctx.get_matrix()
    ctx.identity_matrix()

    if kind == "night":
        for i in range(64):
            sx = (sketch._noise(i * 331, 1) * 0.5 + 0.5) * config.W
            sy = (sketch._noise(i * 331, 2) * 0.5 + 0.5) * (gy - 320)
            a = 0.18 + 0.30 * abs(sketch._noise(i * 331, 3))
            if i % 6 == 0:                       # a handful of them breathe
                a *= 0.45 + 0.55 * (0.5 + 0.5 * math.sin(t * 1.3 + i * 1.7))
            ctx.set_source_rgba(0.93, 0.95, 1.0, a)
            s = 1.4 + abs(sketch._noise(i * 331, 4)) * 1.4
            ctx.rectangle(round(sx), round(sy), s, s)
            ctx.fill()
        # A cold lift where the sky meets the ground, so there is a horizon at all.
        g = cairo.LinearGradient(0, gy - 190, 0, gy)
        g.add_color_stop_rgba(0, 0.13, 0.17, 0.26, 0.0)
        g.add_color_stop_rgba(1, 0.13, 0.17, 0.26, 0.26)
        ctx.set_source(g)
        ctx.rectangle(0, gy - 190, config.W, 190)
        ctx.fill()
        ctx.set_source_rgba(0, 0, 0, 0.30)          # the ground plane falls darker
        ctx.rectangle(0, gy, config.W, config.H - gy)
        ctx.fill()
        ctx.set_source_rgba(*config.MUTED, 0.38)
        ctx.rectangle(0, gy, config.W, 2)
        ctx.fill()
    elif kind == "room":
        # Warm pool on the back wall, floor line, floor falling darker toward the viewer.
        g = cairo.RadialGradient(config.W / 2, gy - 340, 60, config.W / 2, gy - 340, 980)
        g.add_color_stop_rgba(0, *config.ACCENT, 0.055)
        g.add_color_stop_rgba(1, *config.ACCENT, 0.0)
        ctx.set_source(g)
        ctx.rectangle(0, 0, config.W, config.H)
        ctx.fill()
        ctx.set_source_rgba(0, 0, 0, 0.26)
        ctx.rectangle(0, gy, config.W, config.H - gy)
        ctx.fill()
        ctx.set_source_rgba(*config.MUTED, 0.30)
        ctx.rectangle(0, gy, config.W, 2)
        ctx.fill()

    ctx.set_matrix(m)
    ctx.restore()


# ---------------------------------------------------------------- composition
# Every frame in the first cut used the same layout — headline top-centre, subject centre,
# caption bottom-centre — fifty-four times. That, more than anything drawn inside it, is
# what made the video monotonous. Layouts are picked per visual, and when the script does
# not say, they cycle by position so consecutive cards always differ.
LAYOUTS = ("left", "right", "hero")


def _layout(v: Visual, default: str = "") -> str:
    lay = v.get("layout")
    if lay in ("left", "right", "center", "hero"):
        return lay
    if default:
        return default
    # Cycled by position, not hashed from the text. A hash distributes well on average and
    # still clusters locally, which is the only thing that matters here — the viewer sees a
    # run of eight identical frames, never the average.
    return LAYOUTS[int(v.get("ord") or 0) % len(LAYOUTS)]


# ------------------------------------------------------------------- motifs
# Even after the rebuild, 22% of the runtime was a frame with nothing on it but a
# sentence — and a sentence on screen is the one thing the narration is already doing.
# Every text scene now names a motif and gets a picture in the column the type does not
# use. The left and right layouts already reserved that column; only hero had to give
# width back.
#
# Spec syntax is "name" or "name:arg", so a script stays one line per visual.
#
# The free column is measured, not eyeballed. With type running to 0.56 of the content
# width, a motif centred at 0.745 of the frame has only ~300px of clearance on its left —
# the first pass overflowed into the text because the centre was chosen before the box was.
MOTIF_BOX_W = 620.0


def _motif_spot(lay: str) -> tuple[float, float]:
    """Centre of the column the type is not using."""
    if lay == "right":
        return (config.SAFE + config.W * 0.44 - 40) / 2, config.H / 2 + 10
    text_right = config.SAFE + 24 + CONTENT_W * 0.56
    return (text_right + 40 + config.W - config.SAFE) / 2, config.H / 2 + 10


def _draw_motif(ctx: cairo.Context, name: str, arg: str,
                cx: float, cy: float, tt: float, p: float) -> None:
    """Scales solved from each primitive's measured ink extent, not guessed.

    Guessing was wrong by 3-5x in both directions: `people` came out 409x75, a thin strip
    beside 180pt type, while `dashboard` came out 881 wide — wider than the column it had
    to sit in.
    """
    if name == "switch":
        illustrate.switch(ctx, cx, cy, 1.49, on=arg == "on", progress=p)
    elif name == "servers":
        n = max(1, int(arg or 4))
        illustrate.servers(ctx, cx, cy, n=n, bad={n - 1} if n > 1 else set(),
                           scale=min(2.1, MOTIF_BOX_W / (156 * n)), progress=p)
    elif name == "mail":
        # "mail:1" is one envelope, not a pile. The single-message card runs straight into
        # the scene showing all ninety-seven, so a pile beside a pile read as a repeat —
        # one message growing into a stack reads as a build.
        if arg == "1":
            w, h = 420.0, 272.0
            illustrate.envelope(ctx, cx - w / 2, cy - h / 2, w, h,
                                sketch.Pen(color=config.FAIL, width=config.STROKE * 1.3),
                                progress=p)
        else:
            illustrate.mail_pile(ctx, cx, cy, n=6, scale=1.48, progress=p)
    elif name == "alarm":
        illustrate.alarm(ctx, cx, cy, scale=1.35, t=tt, progress=p)
    elif name == "counter":
        illustrate.counter(ctx, cx, cy, arg or "50000", scale=1.0, progress=p)
    elif name == "calendar":
        illustrate.calendar(ctx, cx, cy, (arg or "2003|2012").split("|"),
                            mark=0, scale=0.9, progress=p)
    elif name == "loop":
        illustrate.loop(ctx, cx, cy, radius=158, t=tt, progress=p)
    elif name == "link":
        illustrate.broken_link(ctx, cx, cy, scale=1.15, progress=p)
    elif name == "lock":
        illustrate.padlock(ctx, cx, cy - 20, scale=1.24, progress=p)
    elif name == "clock":
        illustrate.clock(ctx, cx, cy, radius=225, fraction=float(arg or 1.0), progress=p)
    elif name == "people":
        illustrate.people(ctx, cx, cy, n=4, highlight=int(arg or 0), scale=1.5, progress=p)
    elif name == "dashboard":
        illustrate.dashboard(ctx, cx, cy, cols=2, rows=3, t=tt, progress=p)
    elif name == "checklist":
        # A leading "+" ticks the row. Without it every motif checklist drew empty boxes,
        # which is a picture of "none of this happened" — the exact opposite of the beat it
        # was sitting beside, where the whole point is that every step WAS carried out.
        raw = (arg or "one|two").split("|")
        items = [s.lstrip("+") for s in raw]
        marks = ["tick" if s.startswith("+") else "" for s in raw]
        illustrate.checklist(ctx, cx, cy, items, marks=marks, scale=1.18, progress=p)
    elif name == "stick":
        # A cycling motif, not a frozen one: a figure that breathes beside a title card is
        # the cheapest possible answer to "the pictures appear and then hold".
        stickman.draw(ctx, cx, cy + 250, scale=2.13,
                      pose=stickman.animate(arg or "idle", tt), progress=p)
    elif name == "gauge":
        illustrate.gauge(ctx, cx, cy - 40, value=float(arg or 1.0), scale=0.62,
                         t=tt, progress=p)
    elif name == "world":
        illustrate.world(ctx, cx, cy, scale=0.46, spread=min(1.0, max(0.0, tt / 2.29)),
                         t=tt, progress=p)
    elif name == "windows":
        illustrate.windows(ctx, cx, cy, cols=2, rows=2, bad=float(arg or 0.75),
                           t=tt, scale=0.74, progress=p)
    elif name == "barrier":
        illustrate.barrier(ctx, cx, cy, scale=0.46, t=tt, progress=p)
    elif name == "door":
        illustrate.door(ctx, cx, cy, scale=0.58, t=tt, progress=p)


def _motif(ctx: cairo.Context, v: Visual, t: float, dur: float, lay: str,
           *, delay: float = 0.7, alpha: float = 1.0) -> None:
    spec = v.get("motif")
    if not spec:
        return
    name, _, arg = spec.partition(":")
    p = _rphase(t, dur, min(1.7, max(0.8, dur * 0.34)), delay=delay)
    if p <= 0.0:
        return
    cx, cy = _motif_spot(lay)
    # Grouped so alpha applies to the composed drawing. Painting each stroke at alpha
    # instead lets overlapping strokes accumulate, and every primitive here overlaps
    # itself somewhere.
    ctx.push_group()
    try:
        _draw_motif(ctx, name, arg, cx, cy, t * dur, p)
    finally:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(alpha)


def _column(lay: str, motif: bool = False) -> tuple[float, float]:
    """(x anchor, max width) for a type block in this layout."""
    if lay == "left":
        return config.SAFE + 24, CONTENT_W * 0.56
    if lay == "right":
        return config.W * 0.44, CONTENT_W * 0.54
    # Hero runs full measure, unless a motif is sharing the frame with it.
    return config.SAFE + 24, CONTENT_W * (0.56 if motif else 0.86)


# ------------------------------------------------------------------ renderers
def title_card(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    lay = _layout(v)
    ctx.save()
    _drift(ctx, t, dur, 12.0)

    if lay == "hero":
        # Full-bleed section colour, sliding up. This is what gives the episode visible
        # chapters without a narrator ever saying "chapter two".
        col = config.field_of(v.get("section"))
        sketch.field(ctx, col, progress=_ease(_phase(t, dur, 0.55)))
        ink, muted, rule = config.FIELD_INK, config.FIELD_INK, config.FIELD_INK
    else:
        sketch.vignette(ctx, config.W * (0.30 if lay == "left" else 0.72), config.H * 0.45)
        ink, muted, rule = config.INK, config.MUTED, config.ACCENT
    _chrome(ctx, on_field=lay == "hero")

    _motif(ctx, v, t, dur, lay, alpha=0.85 if lay == "hero" else 1.0)
    x, maxw = _column(lay, bool(v.get("motif")))
    size, lines = sketch.fit_block(
        ctx, v.get("text"), config.SZ_TITLE * (1.30 if lay == "hero" else 1.18),
        maxw, config.H * 0.58, config.FONT_SANS, bold=True)
    lh = size * 1.16
    y0 = config.H / 2 - (len(lines) - 1) * lh / 2

    if label := v.get("label"):
        sketch.smallcaps(ctx, label, x, y0 - size * 1.10, 30,
                         rule if lay != "hero" else muted,
                         progress=_rphase(t, dur, 0.5))

    per = min(0.85, max(0.35, dur * 0.30 / max(1, len(lines))))
    last_w = 0.0
    for i, ln in enumerate(lines):
        last_w = sketch.text_size(ctx, ln, size, config.FONT_SANS, bold=True)[0]
        sketch.text(ctx, ln, x, y0 + i * lh, size, ink, config.FONT_SANS, bold=True,
                    progress=_rphase(t, dur, per, delay=0.1 + i * per))

    done = 0.1 + len(lines) * per
    if v.get("mark", "underline") != "off":
        uy = y0 + (len(lines) - 1) * lh + size * 0.32
        up = _phase(t, dur, 0.55, delay=done)
        sketch.line(ctx, x, uy, x + last_w * _ease(up), uy,
                    sketch.Pen(color=rule, width=config.STROKE * 1.6, passes=1))

    if sub := v.get("sub"):
        sketch.text(ctx, sub, x, y0 + len(lines) * lh + 62, config.SZ_HEAD * 0.78,
                    muted, config.FONT_SANS,
                    progress=_rphase(t, dur, 0.6, delay=done + 0.3))
    ctx.restore()


def metric_card(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """The big number. Left-anchored and oversized, deliberately running to the frame edge.

    A number set small and centred is a caption. The same number at 300pt with its own
    baseline rule is a quantity, and that is the whole job of this scene.
    """
    hero = _layout(v, "hero" if v.get("field") == "on" else "left") == "hero"
    ctx.save()
    _drift(ctx, t, dur, 10.0)
    if hero:
        sketch.field(ctx, config.field_of(v.get("section")),
                     progress=_ease(_phase(t, dur, 0.5)))
        ink, muted, rule = config.FIELD_INK, config.FIELD_INK, config.FIELD_INK
    else:
        sketch.vignette(ctx, config.W * 0.32, config.H * 0.46)
        ink, muted, rule = config.INK, config.MUTED, config.ACCENT
    _chrome(ctx, on_field=hero)

    x = config.SAFE + 24
    value = v.get("value")
    # Fill the measure rather than fit inside it: SZ_METRIC is a ceiling, not a target.
    # The ceiling scales with how few characters there are, because a flat cap makes short
    # values look weedy next to long ones — "8" and "397,000,000" both hit 340 and only the
    # long one filled the frame. Short values have the room, so let them take it.
    cap = 340.0 if len(value) > 4 else (620.0 if len(value) <= 2 else 460.0)
    size = sketch.fit_size(ctx, value, cap, CONTENT_W * 0.94, config.FONT_SANS, bold=True)
    tw, th = sketch.text_size(ctx, value, size, config.FONT_SANS, bold=True)

    if label := v.get("label"):
        sketch.smallcaps(ctx, label, x, config.H / 2 - th * 0.72 - 46, 30, rule,
                         progress=_rphase(t, dur, 0.5))

    count = _phase(t, dur, min(1.7, dur * 0.55), delay=0.15)
    shown = value if v.get("count") == "off" else sketch.count_up(value, count)
    baseline = config.H / 2 + th / 2
    sketch.text(ctx, shown, x, baseline, size, ink, config.FONT_SANS, bold=True)

    # A rule under the number instead of a wash behind it. On a near-black ground an amber
    # highlighter at half alpha turns olive and muddies the glyphs it is supposed to lift.
    ry = baseline + size * 0.20
    sketch.line(ctx, x, ry, x + tw * _ease(count), ry,
                sketch.Pen(color=rule, width=9.0, passes=1))

    if sub := v.get("sub"):
        sketch.text(ctx, sub, x, ry + config.SZ_HEAD + 24, config.SZ_HEAD,
                    muted, config.FONT_SANS,
                    progress=_rphase(t, dur, 0.7, delay=min(1.7, dur * 0.55)))
    ctx.restore()


def diagram_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    ctx.save()
    _drift(ctx, t, dur, 8.0)
    _chrome(ctx, v.get("caption"))
    if title := v.get("title"):
        sketch.text(ctx, title, config.W / 2, config.SAFE + 70, config.SZ_HEAD,
                    config.INK, config.FONT_SANS, align="center", bold=True,
                    progress=_rphase(t, dur, 0.55))
    top = config.SAFE + (120 if v.get("title") else 40)

    # Every diagram draws itself now. The old default painted the finished figure on
    # frame one, which is what made the video feel like a slide deck.
    draw_secs = max(1.2, min(2.8, dur * 0.72))
    reveal = _rphase(t, dur, draw_secs, delay=0.35)
    # Dots keep moving once the drawing lands, so the frame never fully freezes.
    flow_phase = ((t * dur) * 0.42) % 1.0 if v.get("flow", "on") != "off" else None

    diagram.draw(ctx, v.get("nodes"), highlight=v.get("highlight"), dim=v.get("dim"),
                 reveal=reveal, flow_phase=flow_phase,
                 flow_only=v.get("flow") != "all",
                 box=(config.SAFE, top, CONTENT_W, config.H - top - config.SAFE))
    ctx.restore()


def _code_runs(line: str, hot: str) -> list[tuple[str, tuple[float, float, float]]]:
    """Split a code line into coloured runs — HOUSE_STYLE §11's syntax-colour note.

    Three colours, chosen for legibility rather than language fidelity: words in the code
    ink, punctuation and operators muted, digits in the accent. Digits get the accent
    because on this channel the digit is usually the payload — `db1` versus `db2` is one
    character, and that character is the story. An optional `hot` substring renders in the
    failure red, for the fragment the narration is pointing at.
    """
    def classify(seg: str) -> list[tuple[str, tuple[float, float, float]]]:
        cols = {"word": config.CODE_FG, "digit": config.ACCENT, "punct": config.MUTED}
        out: list[tuple[str, str]] = []
        cur, kind = "", ""
        for c in seg:
            k = ("digit" if c.isdigit()
                 else "word" if (c.isalnum() or c in " _") else "punct")
            if k != kind and cur:
                out.append((cur, kind))
                cur = ""
            kind, cur = k, cur + c
        if cur:
            out.append((cur, kind))
        return [(s, cols[k]) for s, k in out]

    if not hot or hot not in line:
        return classify(line)
    runs: list[tuple[str, tuple[float, float, float]]] = []
    i = 0
    while i < len(line):
        j = line.find(hot, i)
        if j < 0:
            runs += classify(line[i:])
            break
        runs += classify(line[i:j])
        runs.append((hot, config.FAIL))
        i = j + len(hot)
    return runs


def code(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """Code block, auto-sized to its longest line.

    `body="…"` with `\\n` between lines, or `file="snippet.txt"` to load it from a file
    beside the episode. The file form exists because a param value is delimited by double
    quotes and therefore cannot contain one — which rules out most real code.

    `syntax="on"` colours each line (words / digits / punctuation, plus `hot="…"` in the
    failure red). Off by default so EP01/EP02 re-render byte-identically.
    """
    ctx.save()
    _drift(ctx, t, dur, 8.0)
    _chrome(ctx, v.get("lang"))
    if src := v.get("file"):
        from pathlib import Path
        body = (Path(v.get("_dir", ".")) / src).read_text(encoding="utf-8").rstrip("\n")
    else:
        body = v.get("body")
    lines = body.replace("\\n", "\n").split("\n")
    hl = int(v.num("highlight", -1))

    # Size the block to FILL a target measure, not to fit its content. Shrink-only sizing
    # left a 3-line snippet as a postage stamp in the middle of a 1080p frame.
    target_w = CONTENT_W * 0.62
    widest_at_base = max((sketch.text_size(ctx, ln, config.SZ_CODE, config.FONT_MONO)[0]
                          for ln in lines), default=1) or 1
    size = config.SZ_CODE * (target_w / widest_at_base)
    # The ceiling scales with how little there is to set. A flat 2.2x cap exists to stop a
    # ten-line file becoming billboard lettering, but applied to a seven-character snippet
    # it produced a 320px block in a 1920px frame — on the one beat whose entire job is
    # "look at this exact text". Few short lines have the room, so let them take it.
    longest = max((len(ln) for ln in lines), default=1)
    ceiling = 2.2 if len(lines) > 3 else (7.0 if longest <= 12 else 3.2)
    size = max(config.SZ_CODE * 0.75, min(size, config.SZ_CODE * ceiling))
    # Never let it exceed the safe area, however few characters are in the longest line.
    for ln in lines:
        size = min(size, sketch.fit_size(ctx, ln, size, CONTENT_W * 0.84, config.FONT_MONO))
    # Width alone is not enough: sizing to fill a target measure lets a tall block run off
    # the top and bottom of the frame and pushes the caption off-screen entirely.
    pad_est, cap_room = 40.0, 110.0
    avail_h = config.H - config.SAFE * 2 - cap_room
    needed_h = len(lines) * size * 1.55 + pad_est * 2
    if needed_h > avail_h:
        size *= avail_h / needed_h
    lh = size * 1.55
    widest = max((sketch.text_size(ctx, ln, size, config.FONT_MONO)[0] for ln in lines),
                 default=0)
    # HOUSE_STYLE §12: prompt="on" dresses the block as a terminal — deeper ground, window
    # dots, an accent chevron, and a block cursor that types with the reveal then blinks.
    # The DRESSING is always fair game; what may appear inside it is governed by §12's
    # command-content rules, which are the script's job, not this renderer's.
    term = v.get("prompt") == "on"
    pre = sketch.text_size(ctx, "> ", size, config.FONT_MONO)[0] if term else 0.0
    bar = 44.0 if term else 0.0
    # Height from the ink, not from the line count. `len(lines) * lh` counts a full line of
    # leading below the last line but none above the first, which left the block hugging its
    # top border with a hand's width of dead space underneath.
    pad = 40.0
    bw = widest + pre + pad * 2
    bh = (len(lines) - 1) * lh + size * 1.25 + pad * 2 + bar
    bx, by = config.W / 2 - bw / 2, config.H / 2 - bh / 2
    base0 = by + bar + pad + size    # baseline of the first line

    p0 = _rphase(t, dur, 0.55)
    sketch.rect(ctx, bx, by, bw, bh, sketch.INK_PEN,
                fill=config.BG if term else config.CODE_BG, progress=p0)
    if term and p0 > 0.6:
        pb = min(1.0, (p0 - 0.6) / 0.4)
        for k in range(3):
            sketch.ellipse(ctx, bx + 30 + k * 32, by + bar / 2, 8, 8,
                           sketch.Pen(color=config.MUTED, width=2.2, alpha=0.85),
                           fill=config.MUTED, fill_alpha=0.25, progress=pb)
        sketch.line(ctx, bx, by + bar, bx + bw, by + bar,
                    sketch.Pen(color=config.MUTED, width=1.8, alpha=0.5, passes=1),
                    progress=pb)
    per = min(0.45, max(0.16, dur * 0.30 / max(1, len(lines))))
    coloured = v.get("syntax") == "on"
    last_p, last_w = 0.0, 0.0
    for i, ln in enumerate(lines):
        p = _rphase(t, dur, per, delay=0.5 + i * per)
        if p <= 0.0:
            break
        if term and i == 0:
            sketch.text(ctx, ">", bx + pad, base0, size, config.ACCENT,
                        config.FONT_MONO, bold=True, progress=min(1.0, p * 2))
        if i == hl:
            # The highlight lands after the line is typed, so the eye is already there.
            sketch.wash(ctx, bx + pad + pre - 8, base0 + i * lh - size * 0.85,
                        (widest + 16) * _ease(_phase(t, dur, 0.45,
                                                     delay=0.5 + (i + 1) * per)),
                        lh * 0.9, config.FAIL, 0.22)
        lw = sketch.text_size(ctx, ln, size, config.FONT_MONO)[0] or 1.0
        last_p, last_w = p, lw
        if coloured and i != hl:
            # One left-to-right wipe across the whole line: each run converts the line's
            # progress into its own share by cumulative width, so the reveal is continuous
            # rather than every run typing at once.
            rx = 0.0
            for run, col in _code_runs(ln, v.get("hot")):
                rw = sketch.text_size(ctx, run, size, config.FONT_MONO)[0]
                rp = max(0.0, min(1.0, (p * lw - rx) / max(rw, 1e-6)))
                if rp > 0.0:
                    sketch.text(ctx, run, bx + pad + pre + rx, base0 + i * lh, size,
                                col, config.FONT_MONO, progress=rp)
                rx += rw
        else:
            sketch.text(ctx, ln, bx + pad + pre, base0 + i * lh, size,
                        config.FAIL if i == hl else config.CODE_FG, config.FONT_MONO,
                        progress=p)

    if term and last_p > 0.0:
        # The cursor rides the typing edge of the last revealed line, then blinks in
        # place. Whole-pixel positions: a cursor is a rectangle of pure edge, and
        # sub-pixel placement is the shimmer the motion rules exist to prevent.
        li = next((i for i in range(len(lines) - 1, -1, -1)
                   if _rphase(t, dur, per, delay=0.5 + i * per) > 0.0), 0)
        lp = _rphase(t, dur, per, delay=0.5 + li * per)
        lw_i = sketch.text_size(ctx, lines[li], size, config.FONT_MONO)[0]
        typed = lp < 1.0
        show = typed or ((t * dur) % 1.06) < 0.58
        if show:
            cx0 = bx + pad + pre + min(1.0, lp) * lw_i + 6
            ctx.set_source_rgba(*config.CODE_FG, 0.85)
            ctx.rectangle(round(cx0), round(base0 + li * lh - size * 0.82),
                          max(3, round(size * 0.52)), max(4, round(size * 1.02)))
            ctx.fill()

    if cap := v.get("caption"):
        # SZ_ANNOT, not SZ_BODY. HOUSE_STYLE §8.4: a caption pinned to a drawing is part of
        # the picture, and at SZ_BODY it is 2.8% of frame height and gone on a phone.
        csz = sketch.fit_size(ctx, cap, config.SZ_ANNOT, CONTENT_W * 0.9, config.FONT_SANS)
        sketch.text(ctx, cap, config.W / 2, by + bh + 62, csz,
                    config.MUTED, config.FONT_SANS, align="center",
                    progress=_rphase(t, dur, 0.5, delay=0.5 + len(lines) * per))
    ctx.restore()


def timeline(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """Horizontal timeline. marks="label|label|label" spaced evenly between from and to.

    The line draws left to right and each mark lands as the line reaches it, so the
    viewer's eye travels with time rather than being handed a finished chart.
    """
    ctx.save()
    _drift(ctx, t, dur, 8.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    marks = [m.strip() for m in v.get("marks").split("|") if m.strip()]
    # Below centre, because the headline now occupies the top band. Stems are long enough
    # that alternating labels clear each other at annotation size — at the old 58px they
    # were tucked against the rule and read as part of it.
    y = config.H / 2 + 56
    x0, x1 = config.SAFE + 70, config.W - config.SAFE - 70
    stem = 84

    draw_secs = max(1.4, min(3.0, dur * 0.7))
    swept = _rphase(t, dur, draw_secs, delay=0.3)

    sketch.line(ctx, x0, y, x1, y, sketch.INK_PEN, progress=swept)
    sketch.text(ctx, v.get("from"), x0, y + 62, config.SZ_ANNOT, config.MUTED,
                config.FONT_SANS, align="center", progress=_rphase(t, dur, 0.4))
    sketch.text(ctx, v.get("to"), x1, y + 62, config.SZ_ANNOT, config.MUTED,
                config.FONT_SANS, align="center",
                progress=_rphase(t, dur, 0.4, delay=0.3 + draw_secs))

    hot = v.get("highlight")
    for i, m in enumerate(marks):
        frac = (i + 1) / (len(marks) + 1)
        if swept < frac:
            continue
        local = min(1.0, (swept - frac) / 0.12) if swept < frac + 0.12 else 1.0
        mx = x0 + (x1 - x0) * frac
        is_hot = m == hot
        pen = sketch.FAIL_PEN if is_hot else sketch.INK_PEN
        r = 13 * local
        sketch.ellipse(ctx, mx, y, r, r, pen, fill=config.FAIL if is_hot else config.INK)
        up = i % 2 == 0
        sketch.line(ctx, mx, y, mx, y + (-stem if up else stem), pen, progress=local)
        size = sketch.fit_size(ctx, m, config.SZ_ANNOT, (x1 - x0) / (len(marks) + 1) * 1.5,
                               config.FONT_SANS)
        sketch.text(ctx, m, mx, y + (-stem - 24 if up else stem + size), size,
                    config.FAIL if is_hot else config.INK, config.FONT_SANS,
                    align="center", progress=local)
    ctx.restore()


def end_card(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """The last frame, so it gets the takeaway field and real type scale.

    It was sizing the next-episode title with fit_size — the unwrapped-string trap the
    house style warns about. A fourteen-word sentence forced onto a single line came out
    at caption size, on the one frame whose whole job is selling the next watch.
    """
    ctx.save()
    _drift(ctx, t, dur, 10.0)
    sketch.field(ctx, config.field_of("takeaway"), progress=_ease(_phase(t, dur, 0.55)))
    _chrome(ctx, on_field=True)
    x = config.SAFE + 24
    _motif(ctx, v, t, dur, "left", delay=0.9, alpha=0.85)
    sketch.smallcaps(ctx, "NEXT", x, config.H * 0.30, 34, config.FIELD_INK,
                     progress=_rphase(t, dur, 0.4))
    nxt = v.get("next")
    size, lines = sketch.fit_block(ctx, nxt, config.SZ_TITLE,
                                   CONTENT_W * (0.56 if v.get("motif") else 0.88),
                                   config.H * 0.34, config.FONT_SANS, bold=True)
    lh = size * 1.14
    y0 = config.H * 0.30 + 96
    per = min(0.80, max(0.35, dur * 0.28 / max(1, len(lines))))
    for i, ln in enumerate(lines):
        sketch.text(ctx, ln, x, y0 + i * lh, size, config.FIELD_INK, config.FONT_SANS,
                    bold=True, progress=_rphase(t, dur, per, delay=0.4 + i * per))
    sketch.text(ctx, config.TAGLINE, x, y0 + len(lines) * lh + 52, config.SZ_ANNOT,
                config.FIELD_INK, config.FONT_SANS,
                progress=_rphase(t, dur, 0.5, delay=0.4 + len(lines) * per + 0.3))
    ctx.restore()


def quote(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """A verbatim line from the primary source, attributed. Builds trust — use often."""
    ctx.save()
    _drift(ctx, t, dur, 10.0)
    _chrome(ctx)
    # A quote sits left so its motif can take the right column; without one it runs wide.
    _motif(ctx, v, t, dur, "left", delay=0.9)
    meas = CONTENT_W * (0.54 if v.get("motif") else 0.82)
    body = f'"{v.get("text")}"'
    # Start well above SZ_HEAD and shrink to fit. Starting AT SZ_HEAD meant a short quote
    # could only ever be set at 56pt however much room it had, which is 5% of frame height
    # on the frames whose whole job is that the words are somebody else's.
    size = config.SZ_HEAD * 1.55
    lines = sketch.wrap(ctx, body, size, meas, config.FONT_SANS)
    while len(lines) > 5 and size > 24:
        size -= 4
        lines = sketch.wrap(ctx, body, size, meas, config.FONT_SANS)

    lh = size * 1.4
    y0 = config.H / 2 - (len(lines) - 1) * lh / 2
    sketch.line(ctx, config.SAFE + 60, y0 - size, config.SAFE + 60,
                y0 + (len(lines) - 1) * lh + 20, sketch.MUTED_PEN,
                progress=_rphase(t, dur, 0.5))
    per = min(0.8, max(0.3, dur * 0.42 / max(1, len(lines))))
    for i, ln in enumerate(lines):
        sketch.text(ctx, ln, config.SAFE + 110, y0 + i * lh, size,
                    config.INK, config.FONT_SANS,
                    progress=_rphase(t, dur, per, delay=0.3 + i * per))
    if src := v.get("source"):
        sketch.text(ctx, f"— {src}", config.SAFE + 110,
                    y0 + len(lines) * lh + 30, config.SZ_BODY,
                    config.MUTED, config.FONT_SANS,
                    progress=_rphase(t, dur, 0.5, delay=0.3 + len(lines) * per))
    ctx.restore()


# ------------------------------------------------------- pictorial illustrations
def _headline(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """The line above an illustration.

    Alignment alternates from the content hash rather than being centred every time. The
    illustration scenes are the bulk of the episode, and with one fixed headline slot they
    all opened identically no matter how different the drawing underneath was — the same
    monotony the layouts fixed for the text cards, just moved somewhere less obvious.

    Left-set headlines get more size because they have the full measure to run into; a
    centred one has to stay clear of both margins.
    """
    title = v.get("title")
    if not title:
        return
    left = int(v.get("ord") or 0) % 2 == 0
    x = config.SAFE + 24 if left else config.W / 2
    size = sketch.fit_size(ctx, title, config.SZ_HEAD * (1.34 if left else 1.0),
                           CONTENT_W * (0.92 if left else 0.80), config.FONT_SANS,
                           bold=True)
    sketch.text(ctx, title, x, config.SAFE + 40 + size * 0.62, size,
                config.INK, config.FONT_SANS, align="left" if left else "center",
                bold=True, progress=_rphase(t, dur, 0.55))


def _caption(ctx: cairo.Context, v: Visual, t: float, dur: float, delay: float) -> None:
    if cap := v.get("caption"):
        sketch.text(ctx, cap, config.W / 2, config.H - config.SAFE - 20,
                    config.SZ_HEAD, config.MUTED, config.FONT_SANS, align="center",
                    progress=_rphase(t, dur, 0.6, delay=delay))


def switch_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """A literal wall switch. `state="flip"` throws it on screen instead of cutting to it."""
    ctx.save()
    # §13.3: an inherited renderer may be reused only if it is re-staged into this story's
    # world. Both are opt-in and default to nothing, so EP01-EP04 render byte-identically.
    if v.get("photo"):
        _photo(ctx, v, "", darken=0.74, blur=18, tint=(0.15, 0.17, 0.25), desat=0.78)
    _drift(ctx, t, dur, 8.0)
    if v.get("stage"):
        _stage(ctx, v.get("stage"), t * dur, config.H * 0.86)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    state = v.get("state", "off").lower()
    p = _rphase(t, dur, max(1.2, min(2.4, dur * 0.6)), delay=0.4)
    throw = None
    if state == "flip":
        at = v.num("at", max(1.4, min(3.0, dur * 0.45)))
        throw = _ease(_phase(t, dur, 0.34, delay=at))
    illustrate.switch(ctx, config.W / 2, config.H / 2 + 40, scale=1.95,
                      on=state == "on", throw=throw, progress=p)
    if lbl := v.get("label"):
        sketch.text(ctx, lbl, config.W / 2, config.H / 2 + 372, config.SZ_ANNOT,
                    config.MUTED, config.FONT_SANS, align="center",
                    progress=_rphase(t, dur, 0.5, delay=1.6))
    _caption(ctx, v, t, dur, delay=2.0)
    ctx.restore()


def mail_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """A pile of unread warnings, with the count ticking beside it."""
    ctx.save()
    _drift(ctx, t, dur, 8.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    n = int(v.num("shown", 7))
    p = _rphase(t, dur, max(1.4, min(3.0, dur * 0.7)), delay=0.3)
    illustrate.mail_pile(ctx, config.W * 0.32, config.H / 2 + 40, n=n,
                         scale=2.05, progress=p)
    if value := v.get("value"):
        size = sketch.fit_size(ctx, value, config.SZ_METRIC * 0.8, CONTENT_W * 0.34,
                               config.FONT_SANS, bold=True)
        shown = sketch.count_up(value, p)
        sketch.text(ctx, shown, config.W * 0.74, config.H / 2, size,
                    config.FAIL, config.FONT_SANS, align="center", bold=True)
        if sub := v.get("sub"):
            # Constrained to the right column: at annotation size this line is wide enough
            # to run past the safe margin if left unchecked.
            ssz = sketch.fit_size(ctx, sub, config.SZ_ANNOT, CONTENT_W * 0.44,
                                  config.FONT_SANS)
            sketch.text(ctx, sub, config.W * 0.74, config.H / 2 + 96, ssz,
                        config.MUTED, config.FONT_SANS, align="center",
                        progress=_rphase(t, dur, 0.6, delay=1.2))
    ctx.restore()


def scale_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """Two quantities as dot fields, so the ratio is seen rather than stated."""
    ctx.save()
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.6, min(3.4, dur * 0.75)), delay=0.3)
    illustrate.scale_compare(
        ctx, config.W / 2, config.H / 2 + 30,
        small_n=int(v.num("small", 212)), small_label=v.get("small_label"),
        big_n=int(v.num("big", 4000)), big_label=v.get("big_label"),
        progress=p)
    ctx.restore()


def clock_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.4, min(3.0, dur * 0.7)), delay=0.3)
    cy, radius = config.H / 2 + 30, 280
    illustrate.clock(ctx, config.W / 2, cy, radius=radius,
                     fraction=v.num("fraction", 1.0), progress=p)
    if lbl := v.get("label"):
        # Below the dial, measured from it. The old fixed offset put the baseline 10px
        # above the clock's own bottom edge, so the label read through the face.
        sketch.text(ctx, lbl, config.W / 2, cy + radius + 74, config.SZ_HEAD,
                    config.INK, config.FONT_SANS, align="center", bold=True,
                    progress=_rphase(t, dur, 0.6, delay=1.4))
    ctx.restore()


def people_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.2, min(2.6, dur * 0.65)), delay=0.3)
    # The articulated rig, not the old ad-hoc figures: same crowd, but they stand like
    # people and the highlighted one can be given its own posture.
    n = max(1, int(v.num("n", 10)))
    hot = int(v.num("highlight", 1))
    step = min(190.0, CONTENT_W * 0.92 / n)
    x0 = config.W / 2 - (n - 1) * step / 2
    ground = config.H * 0.74
    scale = min(1.15, step / 150.0)
    for i in range(n):
        pi = max(0.0, min(1.0, p * n - i))
        if pi <= 0:
            continue
        is_hot = i < hot
        stickman.draw(ctx, x0 + i * step, ground, scale=scale,
                      pose=stickman.cycle(stickman.IDLE_BREATH, t * dur + i * 0.37),
                      color=config.FAIL if is_hot else config.MUTED,
                      alpha=1.0 if is_hot else 0.75, progress=pi)
    _caption(ctx, v, t, dur, delay=1.6)
    ctx.restore()


def counter_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """A mechanical tally counter. `blank="on"` empties the windows.

    `roll="12"` keeps the digits turning at 12 a second for the whole scene instead of
    settling on a final reading, which is what a counter that has no stop condition
    actually looks like.
    """
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.2, min(2.6, dur * 0.65)), delay=0.3)
    value = v.get("value", "0")
    roll = v.num("roll", 0.0)
    if roll > 0:
        width = len(value)
        n = int(max(0.0, t * dur - 0.6) * roll) % (10 ** width)
        value = str(n).rjust(width, "0")
    illustrate.counter(ctx, config.W / 2, config.H / 2 + 20, value,
                       scale=2.7, blank=v.get("blank") == "on",
                       label=v.get("label"), progress=p)
    _caption(ctx, v, t, dur, delay=1.8)
    ctx.restore()


def alarm_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """figure="look|panic|type" stands someone under the alarm — a person being paged,
    not an icon ringing in a void (EP04 staging note)."""
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    fig = v.get("figure")
    secs = t * dur
    if fig:
        _stage(ctx, "room", secs, config.H * 0.845)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.2, min(2.4, dur * 0.6)), delay=0.3)
    cy = config.H * (0.42 if fig else 0.5) + 30
    illustrate.alarm(ctx, config.W * (0.44 if fig else 0.5), cy,
                     scale=2.0 if fig else 2.9,
                     ringing=v.get("ringing", "on") != "off", t=secs, progress=p)
    if fig and p > 0.5:
        fp = _rphase(t, dur, 0.8, delay=0.8)
        gy = config.H * 0.845
        _shadow(ctx, config.W * 0.72, gy, 200, alpha=0.35 * fp)
        stickman.draw(ctx, round(config.W * 0.72), gy, scale=1.9,
                      pose=stickman.animate(fig, secs), color=config.INK,
                      progress=fp)
    _caption(ctx, v, t, dur, delay=1.6)
    ctx.restore()


def calendar_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """years="2003|2004|...|2012" mark="9" — a span of dormant time."""
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    years = [s.strip() for s in v.get("years").split("|") if s.strip()]
    p = _rphase(t, dur, max(1.4, min(3.0, dur * 0.7)), delay=0.3)
    illustrate.calendar(ctx, config.W / 2, config.H / 2 + 30, years,
                        mark=int(v.num("mark", -1)), scale=1.7,
                        caption=v.get("note"), progress=p)
    _caption(ctx, v, t, dur, delay=2.0)
    ctx.restore()


def checklist_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """items="a|b|c" marks="cross|cross|tick" — empty box if a mark is omitted.

    `reveal="24"` spreads the item draw across that many seconds instead of the default
    ~3.4, so a checklist being *narrated item by item* lands its rows with the narration.
    Added for EP03, where the five-nets card sat finished for thirty seconds of a
    thirty-four-second beat — the exact hold HOUSE_STYLE §8 forbids.
    """
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    items = [s.strip() for s in v.get("items").split("|") if s.strip()]
    marks = [s.strip() for s in v.get("marks").split("|")] if v.get("marks") else []
    secs = v.num("reveal", 0.0) or max(1.6, min(3.4, dur * 0.75))
    p = _rphase(t, dur, secs, delay=0.3)
    illustrate.checklist(ctx, config.W / 2, config.H / 2 + 30, items,
                         marks=marks, scale=1.55, progress=p)
    ctx.restore()


def loop_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.2, min(2.6, dur * 0.65)), delay=0.3)
    illustrate.loop(ctx, config.W / 2 - 250, config.H / 2 + 40, radius=310,
                    t=t * dur, label=v.get("label"), progress=p)
    _caption(ctx, v, t, dur, delay=1.8)
    ctx.restore()


def dashboard_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    ctx.save()
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.2, min(2.6, dur * 0.65)), delay=0.3)
    illustrate.dashboard(ctx, config.W / 2, config.H / 2 + 30,
                         cols=int(v.num("cols", 4)), rows=int(v.num("rows", 3)),
                         bad=int(v.num("bad", -1)), t=t * dur, progress=p)
    _caption(ctx, v, t, dur, delay=1.8)
    ctx.restore()


def servers_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """n="8" bad="8" — bad is a 1-based, comma-separated list, to read like the script.

    `fall="2.4"` turns that list into a sequence: the machines go over one at a time across
    2.4 seconds instead of the frame arriving with the answer already on it. Watching the
    failure spread is the beat; being shown the aftermath is a caption.
    """
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    order = [int(s) - 1 for s in v.get("bad").replace(" ", "").split(",") if s.isdigit()]
    # Mirror illustrate.servers' squeeze so the machines stand ON the floor, not near it.
    n_srv = int(v.num("n", 8))
    w0, h0, gap0 = 132 * 2.2, 232 * 2.2, 26 * 2.2
    total = n_srv * w0 + (n_srv - 1) * gap0
    k = min(1.0, (config.W - config.SAFE * 2) / total)
    gy = config.H / 2 + 10 + (h0 * k) / 2 + 4
    if not _photo(ctx, v, "server_room", darken=0.86, blur=21,
                  tint=(0.12, 0.16, 0.24), desat=0.84):
        _stage(ctx, "room", t * dur, gy)
    _shadow(ctx, config.W / 2, gy, min(total * k, CONTENT_W) * 0.9, alpha=0.30)
    p = _rphase(t, dur, max(1.4, min(3.0, dur * 0.7)), delay=0.3)
    fall = v.num("fall", 0.0)
    if fall > 0 and order:
        # Starts once the row itself has finished drawing, so nothing goes red before the
        # machine it belongs to exists.
        q = _phase(t, dur, fall, delay=v.num("fall_at", 0.3 + max(1.4, min(3.0, dur * 0.7))))
        order = order[:int(len(order) * q + 1e-6)]
    illustrate.servers(ctx, config.W / 2, config.H / 2 + 10, n=int(v.num("n", 8)),
                       bad=set(order), scale=2.2, label=v.get("label"), progress=p)
    _caption(ctx, v, t, dur, delay=2.0)
    ctx.restore()


def link_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.2, min(2.6, dur * 0.65)), delay=0.3)
    illustrate.broken_link(ctx, config.W / 2, config.H / 2 + 30, scale=2.6,
                           left=v.get("left"), right=v.get("right"), progress=p)
    _caption(ctx, v, t, dur, delay=1.8)
    ctx.restore()


def stick_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """Stick figures acting a beat out.

        [VISUAL: stick pose="type" n="1" title="a routine change, on a Tuesday"]
        [VISUAL: stick pose="panic" n="4" hot="2" title="the war room"]
        [VISUAL: stick pose="walk" travel="520" then="look" at="2.6" ...]

    `pose` names a cycle (walk, run, idle, type, panic, wave, look, badge) or a still pose
    from stickman.POSES. `then`/`at` blend into a second pose partway through, so a figure
    can walk in and then stop and look around. `travel` slides the figure that many pixels
    across the scene — SNAPPED TO WHOLE PIXELS, because a figure sliding on subpixel
    positions makes its own outline shimmer exactly the way drifting type does.

    EP01 used four static poses and never called a cycle once; the whole point of having a
    skeleton instead of sprites was going unused.
    """
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    sketch.vignette(ctx, config.W / 2, config.H * 0.52)
    _chrome(ctx)
    _headline(ctx, v, t, dur)

    n = max(1, int(v.num("n", 1)))
    hot = int(v.num("hot", 0))
    name = v.get("pose", "idle")
    secs = t * dur

    scale = v.num("scale", 2.7 if n == 1 else 1.7)
    ground = config.H * (0.80 if n == 1 else 0.78)
    if not _photo(ctx, v, "office_night", darken=0.76, blur=21,
                  tint=(0.15, 0.18, 0.25), desat=0.80):
        _stage(ctx, "room", secs, ground + 4)
    step = min(360.0, (CONTENT_W * 0.9) / max(1, n))
    x0 = config.W / 2 - (n - 1) * step / 2
    p = _rphase(t, dur, max(0.8, min(1.8, dur * 0.4)), delay=0.25)

    switch_at = v.num("at", 0.0)
    second = v.get("then")

    # Scale so no pose in this beat can reach the headline. Measured off the rig rather than
    # assumed: a standing figure and the same figure with both arms above its head differ by
    # ~90 rig units, and at the single-figure default the panic pose put its hands 110px
    # ABOVE the headline baseline and drew straight through the type. Solving from the
    # actual joints covers every pose, including ones added later, and both ends of a
    # pose-to-pose blend.
    headroom = config.SAFE + (156 if v.get("title") else 20)
    for candidate in filter(None, (name, second)):
        jj = stickman.joints(0.0, 0.0, 1.0,
                             stickman.resolve(stickman.animate(candidate, 0.0)))
        top = min(jj["head"][1] - stickman.HEAD_R, jj["hand_l"][1], jj["hand_r"][1])
        if top < -1e-6:
            scale = min(scale, (headroom - ground) / top)

    # Travel, rounded. A walk cycle on the spot reads as a treadmill; the same cycle moving
    # 500px across the frame reads as someone arriving. The figure walks IN to its mark
    # rather than away from it — ending `travel` pixels off-centre leaves the composition
    # lopsided for the rest of the beat, which is most of it.
    travel = v.num("travel", 0.0)
    move_secs = max(0.4, v.num("travel_secs", min(2.6, dur * 0.45)))
    dx = -round(travel * (1.0 - _ease(_phase(t, dur, move_secs, delay=0.2))))

    for i in range(n):
        col = config.FAIL if (hot and i == hot - 1) else config.INK
        # Stagger entry, so a row of figures assembles rather than appearing at once.
        pi = max(0.0, min(1.0, p * n - i))
        if pi <= 0:
            continue
        _shadow(ctx, round(x0 + i * step) + dx, ground + 2, 140 * scale,
                alpha=0.35 * pi)
        # Offset each figure's clock so a crowd is not one person drawn n times.
        local = secs + i * 0.41
        if second and switch_at > 0 and secs >= switch_at:
            pose = stickman.enter(second, secs - switch_at, from_pose=name, secs=0.45)
        else:
            pose = stickman.enter(name, local, from_pose="idle", secs=0.4)
        j = stickman.draw(ctx, round(x0 + i * step) + dx, ground, scale=scale, pose=pose,
                          color=col, flip=v.get("flip") == "on", progress=pi)
        if i == 0 and v.get("prop") == "box":
            stickman.box(ctx, j, scale=scale, label=v.get("prop_label"))
        elif i == 0 and v.get("prop") == "desk":
            stickman.desk(ctx, j, scale=scale, label=v.get("prop_label"))
    _caption(ctx, v, t, dur, delay=1.6)
    ctx.restore()


def lock_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.2, min(2.4, dur * 0.6)), delay=0.3)
    # A padlock is the tallest primitive here: shackle arch, body, then its own label. At
    # 2.2 the arch ran up through the headline and the label fell off the bottom edge. The
    # band between the headline and the safe margin is ~775px, which caps the scale at 1.66.
    _shadow(ctx, config.W / 2, config.H / 2 + 10 + 56 * 1.6 + 118 * 1.6 + 10,
            420, alpha=0.32 * min(1.0, p * 1.5))
    illustrate.padlock(ctx, config.W / 2, config.H / 2 + 10, scale=1.6,
                       intact=v.get("broken") != "on", caption=v.get("label"),
                       progress=p)
    _caption(ctx, v, t, dur, delay=1.8)
    ctx.restore()


# ------------------------------------------------------- EP02: moving pictures
# Each of these is built around a state CHANGING rather than a state being true, and each
# one has something still happening after the reveal has landed. See illustrate.py.
def gauge_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """A CPU dial pinning. `value` is 0..1 of full scale."""
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.6, min(3.2, dur * 0.7)), delay=0.3)
    illustrate.gauge(ctx, config.W / 2, config.H / 2 + 30, value=v.num("value", 1.0),
                     scale=1.0, t=t * dur, label=v.get("label"), progress=p)
    ctx.restore()


def world_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """A change propagating to every machine on earth. `secs` is how long the wave takes."""
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.0, min(2.0, dur * 0.4)), delay=0.25)
    spread = _phase(t, dur, v.num("secs", 2.29), delay=v.num("at", 1.2))
    illustrate.world(ctx, config.W / 2, config.H / 2 - 10, scale=1.0, spread=spread,
                     bad=v.get("good") != "on", t=t * dur,
                     origin=int(v.num("origin", 12)), progress=p)
    _caption(ctx, v, t, dur, delay=2.4)
    ctx.restore()


def windows_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """A wall of sites going to an error page, one at a time."""
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.2, min(2.4, dur * 0.5)), delay=0.25)
    fall = _phase(t, dur, v.num("secs", 2.2), delay=v.num("at", 1.6))
    illustrate.windows(ctx, config.W / 2, config.H / 2 + 60,
                       cols=int(v.num("cols", 4)), rows=int(v.num("rows", 3)),
                       bad=v.num("bad", 0.8) * fall, t=t * dur,
                       code=v.get("code", "502"), scale=1.08, progress=p)
    _caption(ctx, v, t, dur, delay=2.4)
    ctx.restore()


def barrier_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """A guard rail with a section missing, and the thing it was meant to stop."""
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.6, min(3.2, dur * 0.7)), delay=0.3)
    illustrate.barrier(ctx, config.W / 2, config.H / 2 + 60, scale=1.0,
                       gap=v.get("gap", "on") != "off", t=t * dur,
                       label=v.get("label"), progress=p)
    _caption(ctx, v, t, dur, delay=2.4)
    ctx.restore()


def backtrack_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """The mechanism, enumerated on screen. The one scene that must survive 15 seconds."""
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.2, min(2.4, dur * 0.45)), delay=0.25)
    target = int(v.num("target", 0))
    # Pace the counter off the beat's real length so it lands on the target near the end.
    # A hand-set rate is a guess about a duration that only exists after the audio is
    # measured, and getting it wrong means either a counter that stalls for twenty seconds
    # or one that is still at 40 when the narration has moved on.
    rate = v.num("rate", 0.0) or (target / max(1.0, dur * 0.80 - 0.4) if target else 7.0)
    illustrate.backtrack(ctx, config.W / 2, config.H / 2 + 80, v.get("text", "x=x"),
                         scale=1.0, t=t * dur, rate=rate, target=target, progress=p)
    _caption(ctx, v, t, dur, delay=2.6)
    ctx.restore()


def door_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """Someone walking up to a door that will not let them in."""
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    sketch.vignette(ctx, config.W * 0.60, config.H * 0.52)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.2, min(2.4, dur * 0.5)), delay=0.25)
    spot_x, spot_y = illustrate.door(ctx, config.W * 0.62, config.H / 2 + 60, scale=1.0,
                                     locked=v.get("open") != "on", t=t * dur,
                                     label=v.get("label"), progress=p)
    # The figure walks in from the left, then reaches for the reader and stays there.
    arrive = v.num("arrive", 2.0)
    secs = t * dur
    walk = _ease(_phase(t, dur, arrive, delay=0.5))
    x = round(config.W * 0.10 + (spot_x - config.W * 0.10) * walk)
    if secs < 0.5 + arrive:
        pose = stickman.enter("walk", max(0.0, secs - 0.5), from_pose="idle", secs=0.35)
    else:
        pose = stickman.enter("badge", secs - 0.5 - arrive, from_pose="walk_a", secs=0.4)
    fig = _rphase(t, dur, 0.6, delay=0.35)
    if fig > 0:
        stickman.draw(ctx, x, spot_y, scale=2.05, pose=pose, color=config.INK,
                      progress=fig)
    _caption(ctx, v, t, dur, delay=2.6)
    ctx.restore()


# ------------------------------------------------------- EP04: two coasts, one pen
def coasts_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """Two data centres and the cable between them — the episode's recurring stage.

        [VISUAL: coasts pen="left" title="two rooms, one pen"]
        [VISUAL: coasts pen="left" snap="1.6" dead="left" cue="on" ...]
        [VISUAL: coasts pen="left" pen_to="right" pen_at="2.2" snap="0" ...]
        [VISUAL: coasts pen="right" snap="0" heal="1.8" cue="on" ...]

    `snap` severs the cable at that second (0 = starts severed); `heal` rejoins it.
    (Named snap, not cut: cut is already the episode-wide transition-style param.)
    `dead="left"` darkens that building while the cable is down. `pen` hangs the write-pen
    badge over a site; `pen_to`/`pen_at` fly it across — the failover, depicted. While the
    cable is up, traffic dots flow TOWARD the pen, because writes travel to whoever holds
    it. Declares cue times (snap, heal, flight) for schedule-time SFX via `cue="on"`.
    """
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    secs = t * dur
    scale = 1.0
    lx, rx_ = config.W * 0.22, config.W * 0.78
    cy = config.H * 0.55
    gy = cy + 230 * scale + 2
    # A real skyline behind the buildings, not an empty sky. `photo="none"` opts out.
    if not _photo(ctx, v, "night_city", darken=0.62, blur=15,
                  tint=(0.16, 0.20, 0.32), desat=0.58):
        _stage(ctx, "night", secs, gy)
    else:
        ctx.save(); ctx.identity_matrix()
        ctx.set_source_rgba(0, 0, 0, 0.44)
        ctx.rectangle(0, gy, config.W, config.H - gy); ctx.fill()
        ctx.restore()
        sketch.line(ctx, 0, gy, config.W, gy,
                    sketch.Pen(color=config.MUTED, width=2.2, alpha=0.4, passes=1))
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.4, min(2.8, dur * 0.6)), delay=0.3)

    cut_at, heal_at = v.num("snap", -1.0), v.num("heal", -1.0)
    was_cut = cut_at >= 0 and secs >= cut_at
    healed = heal_at >= 0 and secs >= heal_at
    cut_open = was_cut and not healed
    gp = _ease(_phase(t, dur, 0.45, delay=max(0.0, cut_at))) if was_cut else 0.0
    if healed:
        gp *= 1.0 - _ease(_phase(t, dur, 0.5, delay=heal_at))

    dead_side = v.get("dead")
    dead_l = dead_side == "left" and cut_open
    dead_r = dead_side == "right" and cut_open

    _shadow(ctx, lx, gy, 400 * scale)
    _shadow(ctx, rx_, gy, 400 * scale)
    top_l = illustrate.datacenter(ctx, lx, cy, scale=scale,
                                  label=v.get("left", "East Coast"),
                                  dead=dead_l, t=secs, progress=min(1.0, p * 1.25))
    top_r = illustrate.datacenter(ctx, rx_, cy, scale=scale,
                                  label=v.get("right", "West Coast"),
                                  dead=dead_r, t=secs + 0.9,
                                  progress=max(0.0, min(1.0, p * 1.25 - 0.2)))
    # Warm spill at each living building's door — light leaking out of a place where
    # people are working, and it breathes a little.
    if p > 0.7:
        for bx, dead in ((lx, dead_l), (rx_, dead_r)):
            if not dead:
                sketch.glow(ctx, bx, gy - 24, 150,
                            config.ACCENT, 0.10 + 0.025 * math.sin(secs * 2.6 + bx))

    # crew="left"/"right": the maintenance crew, at work against that building — a
    # ladder, a toolbox and a person, because the story has a person in it.
    if crew := v.get("crew"):
        bx = lx if crew == "left" else rx_
        wall = bx + 175 * scale
        cp2 = _rphase(t, dur, 1.2, delay=0.7)
        if cp2 > 0:
            # Human scale: a person is small next to a data centre. The first pass drew
            # the figure at two thirds of the building's height and it read as a giant.
            illustrate.ladder(ctx, wall + 128, gy, h=232, lean=-116, progress=cp2)
            _shadow(ctx, wall + 210, gy, 120, alpha=0.35)
            stickman.draw(ctx, round(wall + 214), gy, scale=0.98,
                          pose=stickman.animate("look", secs), color=config.INK,
                          flip=True, progress=cp2)
            illustrate.toolbox(ctx, wall + 282, gy, scale=0.85, progress=cp2)

    # The cable, with a real sag. Severed, the free ends droop; healing pulls them back.
    x1, x2 = lx + 175 * scale + 14, rx_ - 175 * scale - 14
    yc = cy - 96 * scale
    sag = 44.0 * scale
    n = 56
    cp = min(1.0, max(0.0, (p - 0.35) / 0.55))
    gap = 0.085 * gp
    pen_cable = sketch.Pen(color=config.INK, width=config.STROKE * 1.1)
    pts = []
    for i in range(n + 1):
        u = i / n
        droop = 0.0
        if gap > 0:
            # Extra droop as each half approaches its torn end.
            edge_l, edge_r = 0.5 - gap, 0.5 + gap
            if u < edge_l:
                droop = max(0.0, (u - (edge_l - 0.16)) / 0.16) ** 2 * 34 * gp
            elif u > edge_r:
                droop = max(0.0, ((edge_r + 0.16) - u) / 0.16) ** 2 * 34 * gp
        pts.append((x1 + (x2 - x1) * u, yc + sag * math.sin(math.pi * u) + droop))
    upto = max(1, int(n * cp))
    for i in range(1, upto + 1):
        u = i / n
        if gap > 0 and 0.5 - gap < u <= 0.5 + gap + 1e-9:
            continue
        sketch.line(ctx, *pts[i - 1], *pts[i], pen_cable)

    # The snap itself: a red tear flaring at the cut moment, fading over a second.
    if was_cut and cut_at >= 0:
        flare = max(0.0, 1.0 - (secs - cut_at) / 1.0) if not healed else 0.0
        if flare > 0 and cut_at > 0:
            mx, my = (x1 + x2) / 2, yc + sag
            sketch.glow(ctx, mx, my, 150, config.FAIL, 0.4 * flare)
            tp = sketch.Pen(color=config.FAIL, width=config.STROKE * 1.9,
                            alpha=min(1.0, flare * 1.6))
            zig = [(mx - 26, my - 44), (mx + 22, my - 12), (mx - 20, my + 16),
                   (mx + 26, my + 46)]
            for i in range(1, len(zig)):
                sketch.line(ctx, *zig[i - 1], *zig[i], tp)
    if healed and heal_at >= 0:
        flare = max(0.0, 1.0 - (secs - heal_at) / 0.8)
        if flare > 0:
            sketch.glow(ctx, (x1 + x2) / 2, yc + sag, 130, config.OK, 0.3 * flare)

    # Traffic, flowing toward whoever holds the pen.
    pen_side = v.get("pen")
    pen_to, pen_at = v.get("pen_to"), v.num("pen_at", -1.0)
    flown = pen_to and pen_at >= 0 and secs >= pen_at
    holder = pen_to if flown else pen_side
    if cp >= 1.0 and not cut_open and holder:
        for k in range(3):
            u = (secs * 0.30 + k / 3.0) % 1.0
            if holder == "left":
                u = 1.0 - u
            fx, fy = x1 + (x2 - x1) * u, yc + sag * math.sin(math.pi * u)
            ctx.set_source_rgba(*config.ACCENT, 0.9)
            ctx.arc(fx, fy, 7.0, 0, math.tau)
            ctx.fill()

    # The pen badge: a circle with the quill in it, breathing over its building's inner
    # shoulder. Roof height, shifted toward the centre — hung above the mast it collided
    # with the headline band on every left-aligned title (caught on the contact sheet).
    if holder and p > 0.6:
        fp = _ease(_phase(t, dur, 0.9, delay=pen_at)) if (pen_to and pen_at >= 0) else \
            (1.0 if flown else 0.0)
        roof_y = cy - 230 * scale - 6
        ax = lx + 150 if pen_side == "left" else rx_ - 150
        bx = ((lx + 150 if pen_to == "left" else rx_ - 150) if pen_to else ax)
        px = ax + (bx - ax) * fp
        py = roof_y - 90 * math.sin(math.pi * fp)
        py += 6.0 * math.sin(secs * 1.7)
        py = max(py, 268.0)          # never into the headline band, even mid-flight
        r = 52.0
        sketch.glow(ctx, px, py, r * 2.2, config.ACCENT, 0.20)
        sketch.ellipse(ctx, px, py, r, r,
                       sketch.Pen(color=config.ACCENT, width=config.STROKE * 1.3),
                       fill=config.BG_DEEP, fill_alpha=0.9)
        illustrate.quill(ctx, px + 12, py + 30, scale=0.95)
    _caption(ctx, v, t, dur, delay=2.0)
    ctx.restore()


def ledgers_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """Two copies of the same ledger, both being written in — split brain, depicted.

        [VISUAL: ledgers left_n="6" right_n="22" left_until="0.35" tear="on"
                 left_label="the East Coast copy" right_label="the West Coast copy"]

    `left_n`/`right_n` entries land across the beat; the left page stops at `left_until`
    (fraction of the beat) and its pen vanishes — a copy frozen mid-thought. The right
    page keeps writing to the end, so the frame never settles. `tear="on"` runs the red
    seam between them: one book, no longer one book.
    """
    ctx.save()
    _drift(ctx, t, dur, 6.0)
    secs = t * dur
    cy = config.H * 0.54
    scale = 0.86
    gy = cy + 310 * scale + 92
    if not _photo(ctx, v, "office_night", darken=0.74, blur=20,
                  tint=(0.15, 0.17, 0.24), desat=0.78):
        _stage(ctx, "room", secs, gy)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.2, min(2.4, dur * 0.5)), delay=0.3)

    # Each copy sits on a writing desk under its own pool of lamp light — two rooms on
    # two coasts, not two rectangles in space.
    slab_y = cy + 310 * scale + 10
    for px_ in (config.W * 0.29, config.W * 0.71):
        sketch.glow(ctx, px_, cy - 130, 470, config.ACCENT, 0.07)
        _shadow(ctx, px_, gy, 660 * scale)
        sketch.rect(ctx, px_ - 330 * scale, slab_y, 660 * scale, 18,
                    sketch.Pen(color=config.MUTED, width=config.STROKE * 0.9),
                    fill=config.BG_DEEP, fill_alpha=0.8,
                    progress=min(1.0, p * 1.6))
        if p > 0.5:
            for sign in (-1, 1):
                lx_ = px_ + sign * 250 * scale
                sketch.line(ctx, lx_, slab_y + 18, lx_, gy,
                            sketch.Pen(color=config.MUTED, width=config.STROKE * 0.9),
                            progress=min(1.0, (p - 0.5) * 2))

    left_n, right_n = v.num("left_n", 6.0), v.num("right_n", 20.0)
    until = max(0.05, min(1.0, v.num("left_until", 1.0)))
    write_span = max(1e-6, dur * 0.85)
    wl = left_n * min(1.0, secs / max(1e-6, dur * until * 0.85))
    stopped = v.num("left_until", 1.0) < 1.0 and secs >= dur * until * 0.85
    wl = min(wl, left_n)
    wr = min(right_n, right_n * secs / write_span)

    start = min(1.0, p * 1.4)
    illustrate.ledger(ctx, config.W * 0.29, cy, scale=scale, written=wl * start,
                      color=config.INK, label=v.get("left_label"),
                      nib=not stopped, t=secs, progress=start)
    illustrate.ledger(ctx, config.W * 0.71, cy, scale=scale, written=wr * start,
                      color=config.ACCENT, label=v.get("right_label"),
                      nib=True, t=secs + 0.7,
                      progress=max(0.0, min(1.0, p * 1.4 - 0.15)))

    if v.get("tear", "on") != "off" and p > 0.5:
        q = min(1.0, (p - 0.5) / 0.5)
        tp = sketch.Pen(color=config.FAIL, width=config.STROKE * 2.0)
        h = 620 * scale
        zig = [(config.W / 2 - 24, cy - h * 0.58), (config.W / 2 + 22, cy - h * 0.22),
               (config.W / 2 - 22, cy + 0.10 * h), (config.W / 2 + 24, cy + 0.44 * h),
               (config.W / 2 - 18, cy + 0.60 * h)]
        for i in range(1, len(zig)):
            seg = max(0.0, min(1.0, q * (len(zig) - 1) - (i - 1)))
            if seg <= 0:
                break
            sketch.line(ctx, *zig[i - 1], *zig[i], tp, progress=seg)
    _caption(ctx, v, t, dur, delay=2.0)
    ctx.restore()


# ==================================================== EP04 rebuild: places, not icons
# The note on the first cut named four timestamps, and all four were EP01/EP02 icons
# dropped into this story unchanged (a smoke alarm, a CPU dial twice, a status board).
# These six replace them with the thing the sentence is actually about, staged in a real
# place. Each takes a photographic plate for its ground, so no beat is line art on black.


def nightdesk_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """A pager going off on a desk at night, and the person it wakes.

    Replaces the smoke-alarm icon at 22:54. The beat is "the humans find out two minutes
    after it was already over", so the picture has to contain a human finding out.
    """
    ctx.save()
    secs = t * dur
    _photo(ctx, v, "office_night", darken=0.62, blur=16,
           tint=(0.16, 0.20, 0.30), desat=0.62)
    _drift(ctx, t, dur, 6.0)
    gy = config.H * 0.84
    ctx.save()
    ctx.identity_matrix()
    ctx.set_source_rgba(0, 0, 0, 0.42)
    ctx.rectangle(0, gy, config.W, config.H - gy)
    ctx.fill()
    ctx.restore()
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.2, min(2.4, dur * 0.5)), delay=0.3)

    # The desk, its monitor, and the pager that will not stop.
    dx, dw = config.W * 0.38, 620.0
    dy = gy - 150
    _shadow(ctx, dx + dw * 0.35, gy, dw * 0.95, alpha=0.45)
    sketch.rect(ctx, dx, dy, dw, 20, sketch.Pen(color=config.INK, width=config.STROKE),
                fill=config.BG_DEEP, fill_alpha=0.9, progress=min(1.0, p * 1.6))
    for lx in (dx + 40, dx + dw - 40):
        sketch.line(ctx, lx, dy + 20, lx, gy,
                    sketch.Pen(color=config.MUTED, width=config.STROKE * 0.9),
                    progress=min(1.0, max(0.0, p * 1.6 - 0.3)))
    if p > 0.45:
        mp = min(1.0, (p - 0.45) / 0.4)
        mw, mh = 300.0, 200.0
        mx, my = dx + 60, dy - mh
        sketch.rect(ctx, mx, my, mw, mh,
                    sketch.Pen(color=config.MUTED, width=config.STROKE * 0.9),
                    fill=config.BG_DEEP, fill_alpha=0.92, progress=mp)
        if mp >= 1.0:
            # Alert rows stacking up on the screen, then scrolling — the frame keeps
            # moving for as long as it is held.
            n = int(min(6, max(0, (secs - 1.6) * 2.2)))
            for i in range(n):
                yy = my + 26 + i * 28
                sketch.line(ctx, mx + 18, yy, mx + 18 + 150 + 90 * abs(
                    sketch._noise(i * 71 + int(secs * 0.7) * 13, 3)), yy,
                    sketch.Pen(color=config.FAIL, width=6.0, alpha=0.85, passes=1))

    # The pager: buzzing hard enough to shake, blinking on its own clock.
    if p > 0.6:
        pp = min(1.0, (p - 0.6) / 0.4)
        buzz = round(2.6 * math.sin(secs * 34.0))
        px, py = dx + dw - 150, dy - 46
        on = (secs % 0.86) < 0.45
        if on:
            sketch.glow(ctx, px + 34, py + 22, 190, config.FAIL, 0.42)
        sketch.rect(ctx, px + buzz, py, 68, 46,
                    sketch.Pen(color=config.FAIL if on else config.MUTED,
                               width=config.STROKE * 1.2),
                    fill=config.FAIL, fill_alpha=0.55 if on else 0.12, progress=pp)

    # The person: asleep in the chair, then bolt upright when the pager fires.
    wake = v.num("wake", 2.4)
    fp = _rphase(t, dur, 0.7, delay=0.5)
    if fp > 0:
        fx = round(config.W * 0.735)
        _shadow(ctx, fx, gy, 210, alpha=0.4 * fp)
        pose = (stickman.enter("panic", secs - wake, from_pose="idle", secs=0.4)
                if secs >= wake else stickman.animate("idle", secs))
        stickman.draw(ctx, fx, gy, scale=2.0, pose=pose, color=config.INK, progress=fp)
    _caption(ctx, v, t, dur, delay=1.8)
    ctx.restore()


def crossing_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """One write crossing a continent and coming back, over and over.

    Replaces the CPU dial. A dial is a number about latency; this is the distance itself,
    with a packet physically making the trip and a counter of how many round trips have
    completed while you watched.
    """
    ctx.save()
    secs = t * dur
    _photo(ctx, v, "night_city", darken=0.68, blur=13,
           tint=(0.14, 0.18, 0.28), desat=0.70)
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.2, min(2.4, dur * 0.45)), delay=0.3)

    y = config.H * 0.62
    # Inset far enough that a centred end-label cannot run off frame: the label is wider
    # than the node it sits under, so the endpoint spacing is set by the TEXT, not the dot.
    x0, x1 = config.SAFE + 330, config.W - config.SAFE - 330
    # The two ends: where the work is, and where the pen is.
    for x, lbl in ((x0, v.get("from", "the application, East Coast")),
                   (x1, v.get("to", "the pen, West Coast"))):
        sketch.ellipse(ctx, x, y, 54, 54,
                       sketch.Pen(color=config.INK, width=config.STROKE * 1.5),
                       fill=config.BG_DEEP, fill_alpha=0.92,
                       progress=min(1.0, p * 1.5))
        sketch.ellipse(ctx, x, y, 18, 18,
                       sketch.Pen(color=config.ACCENT, width=2.6),
                       fill=config.ACCENT, fill_alpha=0.8,
                       progress=min(1.0, p * 1.5))
        size = sketch.fit_size(ctx, lbl, config.SZ_ANNOT * 1.1, 620, config.FONT_SANS)
        sketch.text(ctx, lbl, x, y + 132, size, config.INK, config.FONT_SANS,
                    align="center", progress=min(1.0, p * 1.5))
    sketch.line(ctx, x0, y, x1, y,
                sketch.Pen(color=config.MUTED, width=2.4, alpha=0.55, passes=1),
                progress=p)

    if p >= 1.0:
        # One round trip per `secs_per` seconds, with the packet easing out and back.
        per = max(0.8, v.num("secs_per", 2.6))
        k = ((secs - 1.2) % per) / per if secs > 1.2 else 0.0
        trips = int(max(0.0, secs - 1.2) // per)
        out = k < 0.5
        u = _ease(k * 2) if out else 1.0 - _ease((k - 0.5) * 2)
        px = x0 + (x1 - x0) * u
        col = config.ACCENT if out else config.OK
        sketch.glow(ctx, px, y, 230, col, 0.40)
        for k in range(1, 7):                   # a trail, so the eye reads travel
            u2 = max(0.0, min(1.0, u - (0.035 * k) * (1 if out else -1)))
            tx = x0 + (x1 - x0) * u2
            ctx.set_source_rgba(*col, 0.30 * (1 - k / 7))
            ctx.arc(tx, y, 16.0 * (1 - k / 9), 0, math.tau)
            ctx.fill()
        sketch.rect(ctx, round(px) - 52, y - 38, 104, 76,
                    sketch.Pen(color=col, width=config.STROKE * 1.5),
                    fill=col, fill_alpha=0.30)
        sketch.line(ctx, round(px) - 52, y - 38, round(px), y + 4,
                    sketch.Pen(color=col, width=4.0, passes=1))
        sketch.line(ctx, round(px) + 52, y - 38, round(px), y + 4,
                    sketch.Pen(color=col, width=4.0, passes=1))
        if trips:
            sketch.text(ctx, f"{trips}", config.W / 2, y - 190, 230,
                        config.INK, config.FONT_SANS, align="center", bold=True)
            sketch.text(ctx, v.get("counter", "round trips, just while you watched"),
                        config.W / 2, y - 128, config.SZ_HEAD * 0.85, config.MUTED,
                        config.FONT_SANS, align="center")
    _caption(ctx, v, t, dur, delay=2.2)
    ctx.restore()


def clockwall_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """A wall of screens all answering the same question with different times.

    Replaces the healthy-dashboard icon. The beat is "the site is up and showing people
    the past", so every screen carries a clock and they disagree, visibly, forever.
    """
    ctx.save()
    secs = t * dur
    _photo(ctx, v, "control_room", darken=0.70, blur=18,
           tint=(0.15, 0.19, 0.27), desat=0.72)
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.4, min(2.8, dur * 0.6)), delay=0.3)

    cols, rows = 4, 2
    cw, ch = 340.0, 250.0
    gx, gy_ = 44.0, 52.0
    x0 = config.W / 2 - (cols * cw + (cols - 1) * gx) / 2
    y0 = config.H * 0.56 - (rows * ch + (rows - 1) * gy_) / 2
    n = cols * rows
    shown = int(round(p * n + 0.001))
    for i in range(shown):
        r, c = divmod(i, cols)
        x, y = x0 + c * (cw + gx), y0 + r * (ch + gy_)
        lag = (0.0, 3.5, 0.6, 7.2, 1.4, 5.0, 0.2, 9.1)[i % 8]
        if v.get("state") == "caught":
            lag = 0.0                            # the payoff: everyone agrees again
        stale = lag > 1.0
        col = config.FAIL if stale else config.OK
        local = max(0.35, min(1.0, p * n - i))
        sketch.rect(ctx, x, y, cw, ch,
                    sketch.Pen(color=config.MUTED, width=config.STROKE * 0.9),
                    fill=config.BG_DEEP, fill_alpha=0.9, progress=local)
        if local < 1.0:
            continue
        # Each screen runs its own clock, all ticking, none agreeing.
        ccx, ccy, rr = x + cw * 0.30, y + ch * 0.52, 62.0
        illustrate.clock(ctx, ccx, ccy, radius=rr,
                         fraction=((secs * 0.06 + i * 0.13 - lag * 0.045) % 1.0),
                         accent=col, progress=1.0)
        txt = "now" if not stale else f"{lag:.0f}h behind".replace(".0", "")
        sketch.text(ctx, txt, x + cw * 0.66, y + ch * 0.58, 40, col,
                    config.FONT_SANS, align="center", bold=True)
    _caption(ctx, v, t, dur, delay=2.4)
    ctx.restore()


def sunrise_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """Sunrise, and a crowd arriving — the morning rush as people, not a needle.

    Replaces the second CPU dial. Figures walk in from both edges and keep arriving for
    the length of the beat, so the load is a crowd you can count rather than a number.
    """
    ctx.save()
    secs = t * dur
    _photo(ctx, v, "sunrise_city", darken=0.58, blur=15,
           tint=(0.30, 0.20, 0.16), desat=0.55)
    _drift(ctx, t, dur, 6.0)
    gy = config.H * 0.76
    ctx.save()
    ctx.identity_matrix()
    ctx.set_source_rgba(0, 0, 0, 0.32)
    ctx.rectangle(0, gy, config.W, config.H - gy)
    ctx.fill()
    ctx.restore()
    _chrome(ctx)
    _headline(ctx, v, t, dur)

    n = int(v.num("n", 14))
    arrive = max(1.0, v.num("over", max(2.0, dur * 0.72)))
    for i in range(n):
        # Deterministic scatter: staggered arrival, alternating sides, varied gait.
        due = arrive * (i / max(1, n - 1)) * 0.92
        if secs < due:
            continue
        age = secs - due
        side = -1 if i % 2 == 0 else 1
        target = config.W * (0.14 + 0.72 * ((i * 0.37) % 1.0))
        walk = _ease(min(1.0, age / 1.5))
        x = round(target + side * (1.0 - walk) * 620)
        sc = 0.86 + 0.30 * ((i * 0.29) % 1.0)
        pose = ("walk" if walk < 1.0 else "idle")
        _shadow(ctx, x, gy + 2, 120 * sc, alpha=0.34)
        stickman.draw(ctx, x, gy, scale=sc,
                      pose=stickman.animate(pose, secs + i * 0.41),
                      color=config.INK if i % 3 else config.ACCENT,
                      alpha=0.92, flip=side > 0, progress=min(1.0, age / 0.4))
    _caption(ctx, v, t, dur, delay=1.6)
    ctx.restore()


def fork_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """A junction with two roads and someone standing at it.

    Replaces a two-row tick/cross checklist. A decision drawn as a list of boxes is a
    form; drawn as a fork with one road barricaded it is a situation.
    """
    ctx.save()
    secs = t * dur
    _photo(ctx, v, "night_city", darken=0.74, blur=20,
           tint=(0.13, 0.16, 0.24), desat=0.80)
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.4, min(2.8, dur * 0.45)), delay=0.3)

    jx, jy = config.W / 2, config.H * 0.80
    horizon = config.H * 0.40
    lp = sketch.Pen(color=config.INK, width=config.STROKE * 1.5)
    # Two roads running back to the horizon. The tarmac is FILLED, not outlined: two thin
    # lines read as wires, a filled wedge reads as a road you could stand on.
    for sign in (-1, 1):
        ex = jx + sign * config.W * 0.32
        near_i, near_o = jx - sign * 40, jx + sign * 150
        far_i, far_o = ex - sign * 120, ex + sign * 96
        if p > 0.15:
            ctx.save()
            ctx.set_source_rgba(*config.BG_DEEP, 0.92)
            ctx.move_to(near_i, jy)
            ctx.line_to(near_o, jy)
            ctx.line_to(far_o, horizon)
            ctx.line_to(far_i, horizon)
            ctx.close_path()
            ctx.fill()
            ctx.restore()
        sketch.line(ctx, near_i, jy, far_i, horizon, lp, progress=p)
        sketch.line(ctx, near_o, jy, far_o, horizon, lp, progress=p)
        nc, fc = (near_i + near_o) / 2, (far_i + far_o) / 2
        for k in range(5):                      # centre dashes give it depth
            u0, u1 = k / 5 + 0.06, k / 5 + 0.15
            if p < u1:
                break
            sketch.line(ctx, nc + (fc - nc) * u0, jy + (horizon - jy) * u0,
                        nc + (fc - nc) * u1, jy + (horizon - jy) * u1,
                        sketch.Pen(color=config.MUTED, width=4.0 * (1 - u0 * 0.6),
                                   alpha=0.55, passes=1))
    if p < 0.5:
        ctx.restore()
        return

    q = min(1.0, (p - 0.5) / 0.5)
    # The blocked road: a barrier across it, and a sign saying what it would cost.
    blocked = v.get("blocked", "left")
    for sign, side in ((-1, "left"), (1, "right")):
        ex = jx + sign * config.W * 0.235
        label = v.get(f"{side}_label")
        bad = side == blocked
        if bad:
            by = horizon + (jy - horizon) * 0.40
            bw = 470.0
            sketch.glow(ctx, ex, by + 26, 420, config.FAIL, 0.30)
            sketch.rect(ctx, ex - bw / 2, by, bw, 52,
                        sketch.Pen(color=config.FAIL, width=config.STROKE * 1.8),
                        fill=config.FAIL, fill_alpha=0.32, progress=q)
            for k in range(6):
                sketch.line(ctx, ex - bw / 2 + k * 80, by + 52,
                            ex - bw / 2 + k * 80 + 62, by,
                            sketch.Pen(color=config.FAIL, width=6.0, passes=1),
                            progress=q)
            for sx in (ex - bw / 2 + 14, ex + bw / 2 - 14):
                sketch.line(ctx, sx, by + 52, sx, by + 118,
                            sketch.Pen(color=config.FAIL, width=config.STROKE * 1.4),
                            progress=q)
        if label:
            size = sketch.fit_size(ctx, label, config.SZ_HEAD * 1.15, 620,
                                   config.FONT_SANS)
            sketch.text(ctx, label, ex, horizon - 46, size,
                        config.FAIL if bad else config.OK, config.FONT_SANS,
                        align="center", bold=True, progress=q)

    # The person at the junction, looking down the road they cannot take.
    fp = _rphase(t, dur, 0.7, delay=1.1)
    if fp > 0:
        _shadow(ctx, jx, jy + 8, 190, alpha=0.42 * fp)
        stickman.draw(ctx, round(jx), jy + 8, scale=2.25,
                      pose=stickman.animate("look", secs), color=config.INK,
                      flip=blocked == "right", progress=fp)
    _caption(ctx, v, t, dur, delay=2.2)
    ctx.restore()


def haul_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """Crates being dragged down a long line — terabytes, moving at the speed of wire.

    Replaces a four-row checklist about restore steps. The point of the beat is that the
    backups worked and the *distance* was the problem, so the picture is weight in motion.
    """
    ctx.save()
    secs = t * dur
    _photo(ctx, v, "server_room", darken=0.72, blur=17,
           tint=(0.14, 0.18, 0.26), desat=0.74)
    _drift(ctx, t, dur, 6.0)
    gy = config.H * 0.80
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.0, min(2.0, dur * 0.4)), delay=0.3)

    ctx.save()
    ctx.identity_matrix()
    ctx.set_source_rgba(0, 0, 0, 0.40)
    ctx.rectangle(0, gy, config.W, config.H - gy)
    ctx.fill()
    ctx.restore()
    sketch.line(ctx, 0, gy, config.W, gy,
                sketch.Pen(color=config.MUTED, width=2.4, alpha=0.5, passes=1),
                progress=p)

    # Distance markers sliding past, so the crates are visibly making progress against
    # something much longer than the frame.
    speed = v.num("speed", 62.0)
    for i in range(-1, 9):
        mx = (i * 260 - (secs * speed) % 260)
        if -60 < mx < config.W + 60:
            sketch.line(ctx, mx, gy, mx, gy + 26,
                        sketch.Pen(color=config.MUTED, width=2.2, alpha=0.35, passes=1))

    n = int(v.num("n", 3))
    for i in range(n):
        px = config.W * 0.28 + i * 460 - (secs * speed * 0.18) % 60
        if p < (i + 1) / (n + 1):
            continue
        bob = 2.0 * math.sin(secs * 3.1 + i)
        cw_, chh = 268.0, 214.0
        _shadow(ctx, px, gy + 2, cw_ * 1.15, alpha=0.42)
        sketch.rect(ctx, round(px - cw_ / 2), round(gy - chh + bob), cw_, chh,
                    sketch.Pen(color=config.INK, width=config.STROKE * 1.2),
                    fill=config.BG_DEEP, fill_alpha=0.9)
        sketch.line(ctx, px - cw_ / 2, gy - chh * 0.62 + bob,
                    px + cw_ / 2, gy - chh * 0.62 + bob,
                    sketch.Pen(color=config.MUTED, width=2.4, passes=1))
        if lbl := v.get("crate"):
            sketch.text(ctx, lbl, px, gy - chh - 32, config.SZ_ANNOT, config.INK,
                        config.FONT_SANS, align="center", bold=True)
        # Someone dragging it, leaning into the weight.
        fx = round(px - cw_ / 2 - 120)
        _shadow(ctx, fx, gy + 2, 140, alpha=0.3)
        stickman.draw(ctx, fx, gy, scale=1.75,
                      pose=stickman.animate("walk", secs * 0.55 + i * 0.6),
                      color=config.INK, flip=True, progress=1.0)
    _caption(ctx, v, t, dur, delay=2.0)
    ctx.restore()


def vault_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """Shelves of physical copies, each stamped with when it was taken.

    Replaces the three-tick "and yes, the backups" checklist: real objects on a real
    shelf, a new one landing every few seconds, so the frame is never a finished list.
    """
    ctx.save()
    secs = t * dur
    _photo(ctx, v, "tape_backup", darken=0.76, blur=22,
           tint=(0.16, 0.18, 0.24), desat=0.82)
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.2, min(2.4, dur * 0.4)), delay=0.3)

    shelf_x, shelf_w = config.W * 0.16, config.W * 0.68
    rows_n = 3
    top = config.H * 0.34
    rh = 150.0
    for r in range(rows_n):
        yy = top + r * rh
        sketch.line(ctx, shelf_x, yy + rh - 26, shelf_x + shelf_w, yy + rh - 26,
                    sketch.Pen(color=config.MUTED, width=config.STROKE),
                    progress=min(1.0, max(0.0, p * rows_n - r)))
    labels = [s.strip() for s in (v.get("stamps") or "").split("|") if s.strip()]
    per = max(0.55, v.num("every", 1.1))
    landed = int(min(len(labels) or 9, max(0, (secs - 0.9) / per)))
    for i in range(landed):
        r, c = divmod(i, 3)
        if r >= rows_n:
            break
        yy = top + r * rh
        x = shelf_x + 90 + c * (shelf_w / 3)
        drop = max(0.0, 1.0 - (secs - 0.9 - i * per) / 0.35)
        y = yy + rh - 26 - 96 - drop * 120
        sketch.ellipse(ctx, x, y + 48, 52, 52,
                       sketch.Pen(color=config.INK, width=config.STROKE * 1.15),
                       fill=config.BG_DEEP, fill_alpha=0.95)
        sketch.ellipse(ctx, x, y + 48, 16, 16,
                       sketch.Pen(color=config.MUTED, width=2.4))
        if i < len(labels):
            sketch.text(ctx, labels[i], x, y + 132, 32, config.MUTED,
                        config.FONT_SANS, align="center")
    _caption(ctx, v, t, dur, delay=2.0)
    ctx.restore()


# ============================================ EP05: a system throttled by its own bookkeeping
# HOUSE_STYLE §13 second pass: an episode assembled from the existing library is the
# failure mode, so this story gets its own six. The shapes it needs are a queue that will
# not drain, one doorway everything is funnelled through, a warehouse whose inventory of
# empty shelves is bigger than its stock, fifty million people outside a closed shutter,
# four doors that all open onto a wall, and a torch plugged into the thing that is broken.
#
# Two of them are deliberate CALLBACKS rather than repeats: `lockout` returns with the
# shutter going up instead of staying down, and `blindroom` returns with the lamp on its
# own supply. Both change state, which is the only licence §13 grants for a second use.


def _commas(n: float) -> str:
    return f"{int(n):,}"


def registry_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """The enquiry desk every service has to visit before it can do anything at all.

    Consul is service discovery: nothing inside Roblox can talk to anything else without
    first asking where it is. A box-and-arrow diagram states that. A counter with a queue
    at it shows what it *costs* when the answer stops coming, which is the whole episode.

        [VISUAL: registry state="slow" title="..." desk="where is everything?"]

    `state="ok"` keeps the line moving and the answered count climbing. `state="slow"`
    freezes the count and lets the queue grow off the left edge, and the queue keeps
    shuffling for as long as the beat is held.
    """
    ctx.save()
    secs = t * dur
    gy = config.H * 0.82
    if not _photo(ctx, v, "office_night", darken=0.58, blur=15,
                  tint=(0.15, 0.18, 0.26), desat=0.68):
        _stage(ctx, "room", secs, gy)
    _drift(ctx, t, dur, 6.0)
    ctx.save()
    ctx.identity_matrix()
    ctx.set_source_rgba(0, 0, 0, 0.40)
    ctx.rectangle(0, gy, config.W, config.H - gy)
    ctx.fill()
    ctx.restore()
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.0, min(2.2, dur * 0.4)), delay=0.3)

    slow = v.get("state", "ok").lower() == "slow"
    dx0, dx1 = config.W * 0.60, config.W - config.SAFE - 20
    dtop = gy - 210
    cxk = (dx0 + dx1) / 2

    # The clerk goes down first so the counter draws over the legs — the desk has to be
    # in front of the person, or it reads as a table they are standing on.
    if p > 0.30:
        fp = min(1.0, (p - 0.30) / 0.4)
        stickman.draw(ctx, round(cxk), gy - 6, scale=1.9,
                      pose=stickman.animate("look" if slow else "type", secs * 0.9),
                      color=config.INK, progress=fp)
    _shadow(ctx, cxk, gy, (dx1 - dx0) * 1.05, alpha=0.45)
    sketch.rect(ctx, dx0, dtop, dx1 - dx0, 26,
                sketch.Pen(color=config.INK, width=config.STROKE),
                fill=config.BG_DEEP, fill_alpha=0.94, progress=min(1.0, p * 1.6))
    sketch.rect(ctx, dx0 + 18, dtop + 26, dx1 - dx0 - 36, gy - dtop - 26,
                sketch.Pen(color=config.MUTED, width=config.STROKE * 0.8),
                fill=config.BG_DEEP, fill_alpha=0.82, progress=min(1.0, p * 1.6))
    # A hanging sign, well above the clerk's head. Sat at dtop-36 on the first pass, which
    # is exactly where the clerk's arms are: measured overlap, not a matter of taste.
    if lbl := v.get("desk"):
        sy = gy - 470
        sketch.line(ctx, cxk, sy - 46, cxk, sy - 78,
                    sketch.Pen(color=config.MUTED, width=2.6, alpha=0.6, passes=1),
                    progress=min(1.0, p * 1.4))
        sketch.text(ctx, lbl, cxk, sy, config.SZ_ANNOT, config.MUTED,
                    config.FONT_SANS, align="center",
                    progress=_rphase(t, dur, 0.6, delay=1.1))

    # Arrivals never stop; departures do. That asymmetry is the picture.
    rate = max(0.2, v.num("rate", 1.05))
    arrived = rate * max(0.0, secs - 0.6)
    served = min(arrived, v.num("served_max", 3.0)) if slow else arrived
    waiting = max(0.0, arrived - served)

    # 132px of pitch at scale 1.62 drew a hedge, not a queue: the rig is ~120 wide, so
    # every figure touched its neighbour. Wider pitch, fewer of them, and the tail rows
    # sit smaller and dimmer so the line reads as going back rather than being a wall.
    pitch = 168.0
    shift = 0.0 if slow else ((secs * rate) % 1.0) * pitch
    n = int(min(6, 2 + waiting)) if slow else 3
    for i in range(n):
        fx = round(dx0 - 176 - i * pitch + shift)
        if fx < config.SAFE - 60:
            continue
        local = min(1.0, max(0.0, p * 1.8 - i * 0.11))
        if local <= 0:
            continue
        depth = 1.0 - min(0.30, i * 0.06)
        _shadow(ctx, fx, gy, 150 * depth, alpha=0.34 * local * depth)
        stickman.draw(ctx, fx, gy, scale=1.62 * depth,
                      pose=stickman.animate("idle" if slow else "walk",
                                            secs * 0.9 + i * 0.53),
                      color=config.ACCENT if i == 0 else config.INK,
                      alpha=0.55 + 0.45 * depth, progress=local)

    if p >= 1.0:
        ry = dtop + 100
        sketch.text(ctx, f"answered  {_commas(served)}", cxk, ry, config.SZ_HEAD * 0.82,
                    config.MUTED if slow else config.OK, config.FONT_SANS,
                    align="center", bold=True)
        if slow:
            sketch.text(ctx, f"waiting  {_commas(waiting)}", cxk, ry + 64,
                        config.SZ_HEAD * 0.82, config.FAIL, config.FONT_SANS,
                        align="center", bold=True)
    _caption(ctx, v, t, dur, delay=2.2)
    ctx.restore()


def funnel_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """Many lanes into one doorway — cheaper, until the doorway is the only thing there is.

        [VISUAL: funnel mode="poll"]      every lane keeps its own gate, everything flows
        [VISUAL: funnel mode="stream"]    all four converge on one, which then seizes

    The turnstile's rotation is the throughput, integrated in closed form from a load that
    ramps across the beat, so it does not merely stop — it visibly *grinds down*, and the
    backlog piling up behind it keeps growing for as long as the beat runs.
    """
    ctx.save()
    secs = t * dur
    if not _photo(ctx, v, "turnstile", darken=0.74, blur=19,
                  tint=(0.14, 0.17, 0.25), desat=0.78):
        _stage(ctx, "room", secs, config.H * 0.86)
    _drift(ctx, t, dur, 6.0)
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.0, min(2.2, dur * 0.4)), delay=0.3)

    mode = v.get("mode", "stream").lower()
    stream = mode in ("stream", "freed")
    freed = mode == "freed"
    gx = config.W * 0.66
    ymid = config.H * 0.56
    ys = [config.H * 0.33, config.H * 0.46, config.H * 0.60, config.H * 0.73]
    x0 = config.SAFE + 40

    # Throughput. load ramps 0..1 across `span`; the gate is free below 0.45 and fully
    # seized by 0.95. Phi is the integral, so the arms' angle is continuous when the rate
    # changes — an angle computed from the instantaneous rate would jerk.
    span = max(1.0, v.num("span", dur * 0.55))
    u = min(1.0, secs / span) if stream else 0.0
    if freed:
        # The breakthrough, run backwards: the gate frees off and the queue drains. Same
        # closed-form integral, so the arms accelerate smoothly instead of jumping.
        rate_now = min(1.0, max(0.0, u / 0.35))
        phi = (u * u / 0.70) if u <= 0.35 else 0.175 + (u - 0.35)
    elif stream:
        rate_now = max(0.0, min(1.0, 1.0 - (u - 0.45) / 0.5))
        if u <= 0.45:
            phi = u
        elif u < 0.95:
            phi = 0.45 + (u - 0.45) - (u - 0.45) ** 2
        else:
            phi = 0.70
    else:
        rate_now, phi = 1.0, secs / span
    turned = span * phi

    # Poll mode's gates go SIDE BY SIDE, not one above the other. Stacked vertically at a
    # shared x they drew as a single fence — which says the opposite of "everyone has
    # their own counter", the one thing the frame exists to say.
    poll_xs = [config.SAFE + 260 + (CONTENT_W - 520) * i / 3 for i in range(4)]

    for i, y in enumerate(ys):
        local = min(1.0, max(0.0, p * 4 - i * 0.5))
        if local <= 0:
            continue
        if stream:
            # Bend into the shared line rather than four parallel rails.
            bend = x0 + (gx - x0) * 0.46
            sketch.line(ctx, x0, y, bend, y,
                        sketch.Pen(color=config.MUTED, width=2.6, alpha=0.55, passes=1),
                        progress=local)
            sketch.line(ctx, bend, y, bend + 150, ymid,
                        sketch.Pen(color=config.MUTED, width=2.6, alpha=0.55, passes=1),
                        progress=local)
            sketch.flow(ctx, x0, y, bend, y, (turned * 0.42 + i * 0.21) % 1.0,
                        config.ACCENT, n=3, radius=9.0)
        else:
            px_ = poll_xs[i]
            sketch.line(ctx, px_, config.H * 0.28, px_, config.H * 0.80,
                        sketch.Pen(color=config.MUTED, width=2.6, alpha=0.50, passes=1),
                        progress=local)
            sketch.flow(ctx, px_, config.H * 0.80, px_, config.H * 0.28,
                        (turned * 0.42 + i * 0.25) % 1.0, config.ACCENT, n=3, radius=9.0)

    gates = [(gx, ymid)] if stream else [(x, config.H * 0.54) for x in poll_xs]
    for gi, (tx, ty) in enumerate(gates):
        gp = min(1.0, max(0.0, p * 1.6 - gi * 0.08))
        if gp <= 0:
            continue
        # 92 was taller than the 140px lane pitch, so four separate gates drew as one
        # continuous fence — the exact opposite of the "everyone has their own" beat.
        # The poll gates were 12% of frame height and read as four small marks floating on
        # a plate. §8 wants the subject at 50-70%; four gates at 210 gets the group there.
        h = 190.0 if stream else 210.0
        half = 92.0 if stream else 84.0
        hot = stream and not freed and rate_now < 0.25
        col = (config.OK if freed and rate_now > 0.6
               else config.FAIL if hot else config.INK)
        if hot:
            sketch.glow(ctx, tx, ty, 300, config.FAIL, 0.34)
        for sx in (tx - half, tx + half):
            sketch.line(ctx, sx, ty - h, sx, ty + h,
                        sketch.Pen(color=col, width=config.STROKE * 1.3), progress=gp)
        # The exit. In stream mode it is conspicuously empty, which is the whole point of
        # the frame — otherwise the right third is just unused width.
        if stream and gp >= 1.0:
            sketch.line(ctx, tx + half, ty, config.W - config.SAFE, ty,
                        sketch.Pen(color=config.MUTED, width=2.6, alpha=0.40, passes=1))
            if rate_now > 0.05:
                sketch.flow(ctx, tx + half, ty, config.W - config.SAFE, ty,
                            (turned * 0.42) % 1.0, config.OK,
                            n=max(1, int(rate_now * 3)), radius=9.0)
        # The arms. Rotation IS the throughput.
        if gp >= 1.0:
            ang = turned * (1.9 if stream else 1.4)
            if hot:
                # Trembling at the stop, the way `gauge`'s needle does. Without it a
                # seized gate is a frozen drawing, and on a 50-second beat the scene had
                # nothing moving from second 17 onward but the backlog counter.
                ang += 0.045 * math.sin(secs * 8.7) + 0.02 * math.sin(secs * 23.0)
            arm = 84.0 if stream else 52.0
            for k in range(3):
                a = ang + k * math.tau / 3
                sketch.line(ctx, tx, ty, tx + math.cos(a) * arm, ty + math.sin(a) * arm,
                            sketch.Pen(color=col, width=config.STROKE * 1.5))

    if stream and p >= 1.0:
        # The backlog: what arrived minus what got through, drawn as objects, not a number.
        arrivals = v.num("arrivals", 9.0)
        if freed:
            backlog = max(0.0, v.num("backlog0", 42.0) * (1.0 - min(1.0, u / 0.55)))
        else:
            backlog = max(0.0, arrivals * (secs - turned))
        cols, rows = 7, 6
        bx, by = gx - 190, ymid + 158
        for i in range(int(min(cols * rows, backlog))):
            r, c = divmod(i, cols)
            ctx.set_source_rgba(*config.FAIL, 0.80)
            ctx.arc(round(bx - c * 42), round(by - r * 40), 13, 0, math.tau)
            ctx.fill()
        if backlog >= 1:
            sketch.text(ctx, _commas(backlog), gx - 190, ymid + 236,
                        config.SZ_HEAD * 0.9, config.FAIL, config.FONT_SANS,
                        align="center", bold=True)
        # Only label a backlog that exists. Drawn unconditionally, "writes waiting" sat
        # under an empty patch of frame for the whole first half of the beat.
        if backlog >= 1 and (lab := v.get("backlog_label")):
            sketch.text(ctx, lab, gx - 190, ymid + 288, config.SZ_ANNOT, config.MUTED,
                        config.FONT_SANS, align="center")
    _caption(ctx, v, t, dur, delay=2.4)
    ctx.restore()


def freelist_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """The warehouse that never gives space back — the hero image of the episode.

        [VISUAL: freelist target="960000" parcel="16 kilobytes" list_label="..."]
        [VISUAL: freelist state="compact"]        the callback, once it is compacted

    One small parcel waits by the door. Beside it a clerk copies out the inventory of
    empty shelves, and the stack of that inventory grows past the parcel, past the clerk,
    and off the top of the frame. The count accelerates: readable while it teaches the
    mechanism, racing once the point is made (HOUSE_STYLE §10).
    """
    ctx.save()
    secs = t * dur
    gy = config.H * 0.86
    if not _photo(ctx, v, "warehouse", darken=0.72, blur=16,
                  tint=(0.15, 0.17, 0.24), desat=0.76):
        _stage(ctx, "room", secs, gy)
    _drift(ctx, t, dur, 6.0)
    ctx.save()
    ctx.identity_matrix()
    ctx.set_source_rgba(0, 0, 0, 0.44)
    ctx.rectangle(0, gy, config.W, config.H - gy)
    ctx.fill()
    ctx.restore()
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.2, min(2.4, dur * 0.4)), delay=0.3)
    compact = v.get("state", "").lower() == "compact"

    # The parcel. Small, and it never moves — that is its entire job in the frame.
    px = config.W * 0.80
    pw, ph = 104.0, 80.0
    _shadow(ctx, px, gy, pw * 1.3, alpha=0.42)
    sketch.rect(ctx, round(px - pw / 2), round(gy - ph), pw, ph,
                sketch.Pen(color=config.ACCENT, width=config.STROKE * 1.25),
                fill=config.ACCENT, fill_alpha=0.16, progress=min(1.0, p * 1.7))
    sketch.line(ctx, px, gy - ph, px, gy,
                sketch.Pen(color=config.ACCENT, width=2.6, alpha=0.7, passes=1),
                progress=min(1.0, p * 1.7))
    if lbl := v.get("parcel"):
        sketch.text(ctx, lbl, px, gy + 56, config.SZ_ANNOT, config.ACCENT,
                    config.FONT_SANS, align="center", bold=True,
                    progress=_rphase(t, dur, 0.6, delay=1.0))

    # The stack of paper. Accelerating: k^2.6 spends the first seconds legible and then
    # runs away, which is the difference between "a big number" and "this is exploding".
    span = max(1.5, v.num("span", dur * 0.82))
    k = min(1.0, max(0.0, (secs - 0.7) / span))
    grown = k ** 2.6
    target = v.num("target", 960000.0)
    sx = config.W * 0.31
    sw = 380.0
    # 0.62 of the frame put the stack's top at y=258, so the count above it had nowhere to
    # go and landed on the headline. The RATIO to the parcel is what carries the beat, not
    # absolute height: 0.44 still leaves the stack ~6x the parcel and clears the type.
    max_h = config.H * 0.44
    sheets = 3 if compact else int(2 + grown * 44)
    stack_h = 46.0 if compact else min(max_h, 46.0 + grown * (max_h - 46.0))
    _shadow(ctx, sx, gy, sw * 1.25, alpha=0.44)
    for i in range(sheets):
        yy = gy - (i + 1) * (stack_h / max(1, sheets))
        jig = sketch._noise(i * 613, 2) * 11.0
        col = config.OK if compact else config.INK
        sketch.line(ctx, round(sx - sw / 2 + jig), round(yy),
                    round(sx + sw / 2 + jig), round(yy),
                    sketch.Pen(color=col, width=4.4,
                               alpha=0.30 + 0.55 * (i / max(1, sheets)), passes=1),
                    progress=min(1.0, p * 1.8))
    if not compact and p >= 1.0 and grown < 0.72:
        # A sheet still in the air, landing — but only while the stack is short enough to
        # leave airspace. Once it is tall there is no room between its top and the count's
        # subtitle, and the sheet flew straight through the type. Late in the beat the
        # stack's own growth and the racing count carry the motion instead.
        fall = (secs * 2.4) % 1.0
        fy = gy - stack_h - 118 + fall * 112
        sketch.line(ctx, round(sx - sw / 2 + 26), round(fy), round(sx + sw / 2 + 26),
                    round(fy), sketch.Pen(color=config.INK, width=4.4, alpha=0.55,
                                          passes=1))

    # The count, above the stack, clear of it.
    if p >= 1.0:
        val = 940.0 if compact else target * grown
        # Anchored, not floated above the stack. Tracking the stack's top put the count
        # low early in the beat, right in the path of the landing sheet; a fixed slot
        # clears both the headline above it and the stack's maximum height below it.
        cy_ = config.SAFE + 250
        sketch.text(ctx, _commas(val), sx, cy_, config.SZ_METRIC * 0.62,
                    config.OK if compact else config.FAIL, config.FONT_SANS,
                    align="center", bold=True)
        if lab := v.get("list_label"):
            sketch.text(ctx, lab, sx, cy_ + 54, config.SZ_ANNOT, config.MUTED,
                        config.FONT_SANS, align="center")

    # The clerk, copying it out, between the two — the labour is the point.
    if p > 0.45:
        fp = min(1.0, (p - 0.45) / 0.4)
        fx = round(config.W * 0.585)
        _shadow(ctx, fx, gy, 170, alpha=0.36 * fp)
        stickman.draw(ctx, fx, gy, scale=1.86,
                      pose=stickman.animate("shrug" if compact else "type", secs * 1.05),
                      color=config.INK, flip=True, progress=fp)
    _caption(ctx, v, t, dur, delay=2.4)
    ctx.restore()


def lockout_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """Fifty million people outside a shutter that does not go up for three days.

        [VISUAL: lockout state="closed" hours="73"]
        [VISUAL: lockout state="opening" steps="10"]      the callback: it ratchets open

    The closed form holds a crowd that keeps arriving and an hour count that keeps
    climbing. The open form is the same frontage with the shutter stepping up in
    ten-percent notches and figures walking through the gap, which is what "DNS steering,
    ratcheting up access in roughly 10% increments" actually looked like from outside.
    """
    ctx.save()
    secs = t * dur
    gy = config.H * 0.84
    if not _photo(ctx, v, "arcade", darken=0.70, blur=15,
                  tint=(0.17, 0.16, 0.26), desat=0.68):
        _stage(ctx, "night", secs, gy)
    _drift(ctx, t, dur, 6.0)
    ctx.save()
    ctx.identity_matrix()
    ctx.set_source_rgba(0, 0, 0, 0.42)
    ctx.rectangle(0, gy, config.W, config.H - gy)
    ctx.fill()
    ctx.restore()
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.2, min(2.4, dur * 0.4)), delay=0.3)

    state = v.get("state", "closed").lower()
    opening, half = state == "opening", state == "half"
    bx0, bx1 = config.W * 0.30, config.W * 0.76
    btop = config.H * 0.28
    sketch.rect(ctx, bx0, btop, bx1 - bx0, gy - btop,
                sketch.Pen(color=config.INK, width=config.STROKE * 1.2),
                fill=config.BG_DEEP, fill_alpha=0.90, progress=min(1.0, p * 1.5))

    # How far up the shutter is. Closed stays down; opening ratchets in whole notches, so
    # the movement reads as a decision being taken over and over, not as a door swinging.
    steps = max(1, int(v.num("steps", 10)))
    if opening:
        per = max(0.5, v.num("every", max(0.9, dur * 0.78 / steps)))
        done = min(steps, int(max(0.0, secs - 1.0) / per))
        frac = done / steps
    elif half:
        # 16:35 on the 28th: the shutter is coming down, not going up.
        done, frac = 0, 0.5
    else:
        done, frac = 0, 0.0

    inner_h = gy - btop - 24
    shut_h = inner_h * (1.0 - frac)
    if p > 0.3:
        sp = min(1.0, (p - 0.3) / 0.5)
        sketch.rect(ctx, bx0 + 22, btop + 16, bx1 - bx0 - 44, max(6.0, shut_h),
                    sketch.Pen(color=config.MUTED, width=config.STROKE * 0.9),
                    fill=config.BG_DEEP, fill_alpha=0.96, progress=sp)
        slats = int(max(1.0, shut_h) // 34)
        for i in range(slats):
            yy = round(btop + 16 + (i + 1) * 34)
            sketch.line(ctx, bx0 + 30, yy, bx1 - 30, yy,
                        sketch.Pen(color=config.MUTED, width=2.4, alpha=0.55, passes=1),
                        progress=sp)
        if not opening and not half:
            bar_y = btop + 16 + shut_h * 0.42
            sketch.glow(ctx, (bx0 + bx1) / 2, bar_y, 420, config.FAIL, 0.24)
            sketch.text(ctx, v.get("sign", "CLOSED"), (bx0 + bx1) / 2, bar_y + 24,
                        config.SZ_TITLE * 0.58, config.FAIL, config.FONT_SANS,
                        align="center", bold=True, progress=min(1.0, sp * 1.4))
        else:
            sketch.glow(ctx, (bx0 + bx1) / 2, gy - 60, 520, config.ACCENT,
                        0.10 + 0.24 * frac)

    # The crowd. It keeps arriving whether or not anything opens.
    #
    # The first pass spaced them with `(i * 137) % width`, which wraps and stacks figures
    # on top of each other — twelve of them drew as a hedge with a gap. Even pitch with a
    # seeded jitter, and two depths so it reads as a crowd going back rather than a row.
    n = int(v.num("n", 12))
    # Inset by a whole figure width: a stick figure is ~110px across, so a crowd laid out
    # to SAFE had its end members sliced in half by the frame edge.
    left, right = config.SAFE + 120, config.W - config.SAFE - 120
    for i in range(n):
        back = i % 3 == 2
        row = n - (n // 3)
        idx = i - (i // 3) if not back else i // 3
        cnt = row if not back else max(1, n // 3)
        base = left + (right - left) * (idx / max(1, cnt - 1 if cnt > 1 else 1))
        base += sketch._noise(i * 977, 5) * 54.0
        fy = gy + (26 if back else 54)
        sc = 1.16 if back else 1.36
        if opening and i < int(n * frac + 0.5):
            # Through the gap and gone, then round again. Letting them walk off frame
            # emptied the shot by the time it settled — at 85% through, the frame that is
            # meant to show players coming back had four people in it.
            span_x = right - left + 240
            fx = round(left - 60 + ((base - left + 60)
                                    + ((secs * 0.42 + i * 0.37) % 1.0) * span_x) % span_x)
            pose = stickman.animate("walk", secs * 1.1 + i * 0.4)
            away = False
        elif half and i % 2 == 0:
            # Half of them are already leaving, and they leave the way they came.
            fx = round(base - ((secs * 0.34 + i * 0.29) % 1.0) * 460)
            pose = stickman.animate("walk", secs * 1.0 + i * 0.4)
            away = True
        else:
            fx = round(base + 8 * math.sin(secs * 0.7 + i))
            pose = stickman.animate("wave" if i % 5 == 0 else "idle",
                                    secs * 0.8 + i * 0.61)
            away = False
        local = min(1.0, max(0.0, p * 2.2 - i * 0.07))
        if local <= 0:
            continue
        _shadow(ctx, fx, fy, 128 * sc / 1.36, alpha=(0.20 if back else 0.30) * local)
        stickman.draw(ctx, fx, fy, scale=sc, pose=pose, color=config.INK, flip=away,
                      alpha=(0.62 if back else 0.94), progress=local)

    if p >= 1.0:
        if opening or half:
            sketch.text(ctx, f"{int(frac * 100)}%", config.SAFE + 24,
                        config.SAFE + 250, config.SZ_METRIC * 0.60,
                        config.OK if opening else config.FAIL,
                        config.FONT_SANS, bold=True)
            sketch.text(ctx, v.get("readout", "of players let back in"), config.SAFE + 24,
                        config.SAFE + 302, config.SZ_ANNOT, config.MUTED, config.FONT_SANS)
        else:
            # Paced to 0.95 of the beat, not 0.8. At 0.8 the count landed on 73 with a
            # fifth of the scene still to run and then froze — the EP02 "counter that
            # finishes early" defect, on the frame that is meant to feel like waiting.
            hrs = v.num("hours", 73.0) * min(1.0, max(0.0, (secs - 0.8) / max(1.0, dur * 0.95)))
            sketch.text(ctx, f"{int(hrs)}", config.SAFE + 24, config.SAFE + 250,
                        config.SZ_METRIC * 0.60, config.FAIL, config.FONT_SANS, bold=True)
            sketch.text(ctx, v.get("readout", "hours, and counting"), config.SAFE + 24,
                        config.SAFE + 302, config.SZ_ANNOT, config.MUTED, config.FONT_SANS)
    _caption(ctx, v, t, dur, delay=2.4)
    ctx.restore()


def deadends_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """Four doors down one corridor, and every one of them opens onto a wall.

        [VISUAL: deadends labels="bad hardware|bigger machines|our own traffic|smaller machines"]

    The source numbers its own four failed diagnoses, so this is the episode's spine and
    it must not be a tick-box list (§13 retires the checklist). It is a person walking,
    trying, and walking on — and when the last one closes they pace the corridor, so the
    frame is still moving at second fourteen.
    """
    ctx.save()
    secs = t * dur
    gy = config.H * 0.82
    if not _photo(ctx, v, "office_night", darken=0.60, blur=15,
                  tint=(0.14, 0.16, 0.23), desat=0.72):
        _stage(ctx, "room", secs, gy)
    _drift(ctx, t, dur, 6.0)
    ctx.save()
    ctx.identity_matrix()
    ctx.set_source_rgba(0, 0, 0, 0.46)
    ctx.rectangle(0, gy, config.W, config.H - gy)
    ctx.fill()
    ctx.restore()
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.0, min(2.0, dur * 0.34)), delay=0.3)

    labels = [s.strip() for s in (v.get("labels") or "").split("|") if s.strip()]
    n = max(1, len(labels) or int(v.num("n", 4)))
    # 168x306 gave the subjects ~28% of the frame; §8 asks for 50-70%. The doors are the
    # subject here, so they get the height.
    dw, dh = 208.0, 430.0
    inner = CONTENT_W - dw - 120
    xs = [config.SAFE + 60 + dw / 2 + (inner * i / max(1, n - 1)) for i in range(n)]
    per = max(1.2, v.num("every", dur * 0.86 / n))

    for i, dx in enumerate(xs):
        local = min(1.0, max(0.0, p * n * 1.3 - i * 0.6))
        if local <= 0:
            continue
        # Local clock for this door: when the figure reaches it, and when it is crossed.
        tried = max(0.0, min(1.0, (secs - (i * per + per * 0.42)) / 0.55))
        dead = tried >= 1.0
        # An untried door was MUTED on a dark plate and effectively invisible, so the
        # frame read as one door rather than four options waiting to be tried.
        col = config.FAIL if dead else config.INK
        sketch.rect(ctx, round(dx - dw / 2), round(gy - dh), dw, dh,
                    sketch.Pen(color=col, width=config.STROKE * 1.15),
                    fill=config.BG_DEEP, fill_alpha=0.90, progress=local)
        if tried > 0:
            # Bricked up: courses filling the doorway from the bottom.
            rows = int(6 * tried)
            for r in range(rows):
                yy = gy - 26 - r * 46
                off = 24 if r % 2 else 0
                sketch.line(ctx, dx - dw / 2 + 14 + off, yy, dx + dw / 2 - 14, yy,
                            sketch.Pen(color=config.MUTED, width=3.4, alpha=0.7, passes=1))
        if dead:
            cxx, cyy, r = dx, gy - dh * 0.56, 46.0
            sketch.glow(ctx, cxx, cyy, 190, config.FAIL, 0.30)
            for s in (+1, -1):
                sketch.line(ctx, cxx - r, cyy - r * s, cxx + r, cyy + r * s,
                            sketch.Pen(color=config.FAIL, width=config.STROKE * 1.7))
        if i < len(labels):
            size = sketch.fit_size(ctx, labels[i], config.SZ_ANNOT, dw + 96,
                                   config.FONT_SANS)
            # Four red labels under four red crosses was a wall of red with no hierarchy.
            # The cross carries the failure; the label just names the theory.
            sketch.text(ctx, labels[i], dx, gy + 58, size,
                        config.MUTED if dead else config.INK, config.FONT_SANS,
                        align="center", progress=local)

    # The figure. Walking between doors, working each one, and pacing once they run out.
    if p > 0.25:
        total = n * per
        if secs < total:
            i = min(n - 1, int(secs / per))
            frm = xs[i - 1] if i else config.SAFE + 20
            u = (secs - i * per) / per
            fx = frm + (xs[i] - frm) * _ease(min(1.0, u / 0.42))
            pose = ("badge" if u >= 0.42 else "walk")
        else:
            # Pacing the corridor: still moving, and out of ideas.
            u = ((secs - total) / 6.0) % 2.0
            k = u if u < 1 else 2 - u
            fx = xs[0] + (xs[-1] - xs[0]) * k
            pose = "walk"
        # Stood ON the ground line, the figure merged into whichever door it was passing.
        # Bringing it forward and down puts it clearly in front of the corridor.
        fx = round(fx + 148)
        _shadow(ctx, fx, gy + 62, 190, alpha=0.40)
        stickman.draw(ctx, fx, gy + 62, scale=2.24,
                      pose=stickman.animate(pose, secs * 1.05),
                      color=config.ACCENT, progress=min(1.0, (p - 0.25) / 0.4))
    _caption(ctx, v, t, dur, delay=2.4)
    ctx.restore()


def blindroom_scene(ctx: cairo.Context, v: Visual, t: float, dur: float) -> None:
    """The torch is plugged into the thing that is broken.

        [VISUAL: blindroom state="dark"]     the circular dependency, during the outage
        [VISUAL: blindroom state="fixed"]    the callback: its own supply, its own light

    This is the takeaway's picture and it is the one thing a viewer can act on: the
    instrument you would reach for in an outage must not be downstream of the outage.
    """
    ctx.save()
    secs = t * dur
    gy = config.H * 0.80
    fixed = v.get("state", "dark").lower() == "fixed"
    if not _photo(ctx, v, "control_room", darken=0.74 if not fixed else 0.64, blur=18,
                  tint=(0.13, 0.15, 0.22), desat=0.78):
        _stage(ctx, "room", secs, gy)
    _drift(ctx, t, dur, 6.0)
    ctx.save()
    ctx.identity_matrix()
    ctx.set_source_rgba(0, 0, 0, 0.38)
    ctx.rectangle(0, gy, config.W, config.H - gy)
    ctx.fill()
    ctx.restore()
    _chrome(ctx)
    _headline(ctx, v, t, dur)
    p = _rphase(t, dur, max(1.2, min(2.4, dur * 0.42)), delay=0.3)

    # The dead machine, over on the right, with the socket the lamp is fed from.
    mx, mw, mh = config.W * 0.74, 360.0, 470.0
    _shadow(ctx, mx, gy, mw * 1.2, alpha=0.44)
    sketch.rect(ctx, round(mx - mw / 2), round(gy - mh), mw, mh,
                sketch.Pen(color=config.FAIL if not fixed else config.MUTED,
                           width=config.STROKE * 1.2),
                fill=config.BG_DEEP, fill_alpha=0.94, progress=min(1.0, p * 1.5))
    for i in range(4):
        yy = gy - mh + 62 + i * 58
        sketch.line(ctx, mx - mw / 2 + 30, yy, mx + mw / 2 - 30, yy,
                    sketch.Pen(color=config.MUTED, width=3.0, alpha=0.42, passes=1),
                    progress=min(1.0, max(0.0, p * 1.5 - i * 0.1)))
    if not fixed and p > 0.6:
        cxx, cyy, r = mx, gy - mh * 0.5, 52.0
        sketch.glow(ctx, cxx, cyy, 230, config.FAIL, 0.30)
        for s in (+1, -1):
            sketch.line(ctx, cxx - r, cyy - r * s, cxx + r, cyy + r * s,
                        sketch.Pen(color=config.FAIL, width=config.STROKE * 1.8),
                        progress=min(1.0, (p - 0.6) / 0.3))
    if lbl := v.get("machine"):
        sketch.text(ctx, lbl, mx, gy + 58, config.SZ_ANNOT, config.MUTED,
                    config.FONT_SANS, align="center",
                    progress=_rphase(t, dur, 0.6, delay=1.6))

    # The person, sweeping a lamp that has nothing behind it.
    fx = round(config.W * 0.30)
    fp = min(1.0, p * 1.4)
    if fp > 0:
        _shadow(ctx, fx, gy, 220, alpha=0.38 * fp)
        j = stickman.draw(ctx, fx, gy, scale=2.45,
                          pose=stickman.animate("look" if not fixed else "idle",
                                                secs * 0.8),
                          color=config.INK, progress=fp)
        if fp >= 1.0 and j:
            hx, hy = j.get("hand_r", (fx + 60, gy - 220))
            # A weak flicker that never catches, or a steady light once it is off its own
            # supply. Either way the beat has motion at second fourteen.
            if fixed:
                # A slow breath rather than a constant. Held for 20+ seconds a steady
                # glow plus an idle cycle is the closest thing in this episode to a
                # frozen frame, and this is the beat carrying the takeaway.
                lit = 0.46 + 0.10 * math.sin(secs * 0.9)
            else:
                lit = max(0.0, 0.16 * (0.5 + 0.5 * math.sin(secs * 7.3))
                          * (1.0 if (secs % 2.7) < 1.1 else 0.15))
            sketch.glow(ctx, hx, hy, 340, config.ACCENT, lit)
            sketch.ellipse(ctx, hx, hy, 34, 34,
                           sketch.Pen(color=config.ACCENT if fixed else config.MUTED,
                                      width=config.STROKE * 1.2),
                           fill=config.ACCENT, fill_alpha=0.10 + lit)
            # The cable: to the dead machine, or to its own supply on the far wall.
            if fixed:
                sketch.line(ctx, hx, hy + 34, hx - 150, gy,
                            sketch.Pen(color=config.OK, width=4.0, passes=1))
                sketch.line(ctx, hx - 150, gy, config.SAFE + 60, gy,
                            sketch.Pen(color=config.OK, width=4.0, passes=1))
                sketch.line(ctx, config.SAFE + 60, gy, config.SAFE + 60, gy - 120,
                            sketch.Pen(color=config.OK, width=4.0, passes=1))
            else:
                sketch.line(ctx, hx, hy + 34, hx + 120, gy,
                            sketch.Pen(color=config.MUTED, width=4.0, alpha=0.8,
                                       passes=1))
                sketch.line(ctx, hx + 120, gy, mx - mw / 2 + 40, gy,
                            sketch.Pen(color=config.MUTED, width=4.0, alpha=0.8,
                                       passes=1))
                sketch.line(ctx, mx - mw / 2 + 40, gy, mx - mw / 2 + 40, gy - 90,
                            sketch.Pen(color=config.MUTED, width=4.0, alpha=0.8,
                                       passes=1))
    _caption(ctx, v, t, dur, delay=2.6)
    ctx.restore()


# ----------------------------------------------------------------- schedule-time cues
# HOUSE_STYLE §12: a red cross (or any marked reveal) lands with its own quiet sound at
# its ACTUAL reveal moment. Those moments only exist once the beat's measured length is
# known, so scenes declare them here and schedule.py mixes them. Strictly opt-in via
# cue="on" — EP01-EP03 carry no cue params and render byte-identically.
def _invert_reveal(target: float, dur: float, secs: float, delay: float) -> float | None:
    """Wall-clock seconds at which _rphase(t, dur, secs, delay) first reaches `target`.

    Numeric, at 240 steps/second, so it can never drift from the drawing math — the exact
    failure hand-placed [SFX:] lines had whenever the audio re-paced.
    """
    steps = max(2, int(dur * 240))
    for k in range(steps + 1):
        tt = k / steps
        if _rphase(tt, dur, secs, delay=delay) >= target - 1e-9:
            return tt * dur
    return None


def _cues_checklist(v: Visual, dur: float) -> list[tuple[float, str, float]]:
    items = [s for s in v.get("items").split("|") if s.strip()]
    marks = [s.strip() for s in v.get("marks").split("|")] if v.get("marks") else []
    if not items:
        return []
    secs = v.num("reveal", 0.0) or max(1.6, min(3.4, dur * 0.75))
    per = 1.0 / len(items)
    out: list[tuple[float, str, float]] = []
    for i in range(len(items)):
        m = marks[i] if i < len(marks) else ""
        if not m:
            continue
        # The mark starts drawing when its row's local progress crosses 0.5 — see
        # illustrate.checklist. Solve the eased global progress back to wall time.
        target = i * per * 0.85 + 0.5 * per
        if target >= 1.0:
            target = 1.0 - 1e-6
        at = _invert_reveal(target, dur, secs, delay=0.3)
        if at is not None:
            out.append((at, "thud" if m == "cross" else "tick",
                        0.55 if m == "cross" else 0.8))
    return out


def _cues_coasts(v: Visual, dur: float) -> list[tuple[float, str, float]]:
    out: list[tuple[float, str, float]] = []
    if (cut := v.num("snap", -1.0)) > 0 and cut < dur:
        out.append((cut, "thud", 0.9))
    if (heal := v.num("heal", -1.0)) > 0 and heal < dur:
        out.append((heal, "pop", 0.8))
    if v.get("pen_to") and (pen_at := v.num("pen_at", -1.0)) > 0 and pen_at < dur:
        out.append((pen_at, "whoosh", 0.6))
    return out


def _cues_servers(v: Visual, dur: float) -> list[tuple[float, str, float]]:
    fall = v.num("fall", 0.0)
    order = [s for s in v.get("bad").replace(" ", "").split(",") if s.isdigit()]
    if fall <= 0 or not order:
        return []
    start = v.num("fall_at", 0.3 + max(1.4, min(3.0, dur * 0.7)))
    return [(min(dur - 0.05, start + fall * (i + 1) / len(order)), "tick", 0.6)
            for i in range(len(order))]


def _cues_switch(v: Visual, dur: float) -> list[tuple[float, str, float]]:
    if v.get("state", "off").lower() != "flip":
        return []
    at = v.num("at", max(1.4, min(3.0, dur * 0.45)))
    return [(min(dur - 0.05, at), "tick", 0.9)] if at < dur else []


def _cues_deadends(v: Visual, dur: float) -> list[tuple[float, str, float]]:
    """One quiet impact per door that turns out to be a wall — §12's "a red cross should
    land with a sound, every time", at the reveal's real moment rather than a beat edge."""
    labels = [s for s in (v.get("labels") or "").split("|") if s.strip()]
    n = max(1, len(labels) or int(v.num("n", 4)))
    per = max(1.2, v.num("every", dur * 0.86 / n))
    out = []
    for i in range(n):
        at = i * per + per * 0.42 + 0.55
        if at < dur - 0.05:
            out.append((at, "thud", 0.55))
    return out


def _cues_lockout(v: Visual, dur: float) -> list[tuple[float, str, float]]:
    """A tick per ten-percent notch as the shutter ratchets up. Closed emits nothing —
    the silence under the closed frontage is the point."""
    if v.get("state", "closed").lower() != "opening":
        return []
    steps = max(1, int(v.num("steps", 10)))
    per = max(0.5, v.num("every", max(0.9, dur * 0.78 / steps)))
    return [(1.0 + i * per, "tick", 0.7)
            for i in range(steps) if 1.0 + i * per < dur - 0.05]


def _cues_funnel(v: Visual, dur: float) -> list[tuple[float, str, float]]:
    """The moment the gate actually seizes, solved from the same ramp the drawing uses
    (rate_now crossing 0.25 at u = 0.825), so it can never drift off the picture."""
    if v.get("mode", "stream").lower() != "stream":
        return []
    at = max(1.0, v.num("span", dur * 0.55)) * 0.825
    return [(at, "thud", 0.85)] if at < dur - 0.05 else []


CUE_FNS = {
    "checklist": _cues_checklist,
    "coasts": _cues_coasts,
    "servers": _cues_servers,
    "switch": _cues_switch,
    "deadends": _cues_deadends,
    "lockout": _cues_lockout,
    "funnel": _cues_funnel,
}


def cues(v: Visual | None, dur: float) -> list[tuple[float, str, float]]:
    """(seconds-into-scene, effect, gain-multiplier) cues this visual declares.

    Empty unless the scene opts in with cue="on", which is the byte-identity guarantee
    for every episode authored before this existed.
    """
    if v is None or v.get("cue") != "on":
        return []
    fn = CUE_FNS.get(v.renderer)
    return fn(v, dur) if fn else []


RENDERERS = {
    "title_card": title_card,
    "metric_card": metric_card,
    "diagram": diagram_scene,
    "code": code,
    "timeline": timeline,
    "end_card": end_card,
    "quote": quote,
    # Pictorial — use these wherever a beat is emotional rather than structural.
    # Reach for one of these BEFORE reaching for title_card. See HOUSE_STYLE §8.
    "switch": switch_scene,
    "mail": mail_scene,
    "scale": scale_scene,
    "clock": clock_scene,
    "people": people_scene,
    "counter": counter_scene,
    "alarm": alarm_scene,
    "calendar": calendar_scene,
    "checklist": checklist_scene,
    "loop": loop_scene,
    "dashboard": dashboard_scene,
    "servers": servers_scene,
    "link": link_scene,
    "lock": lock_scene,
    "stick": stick_scene,
    # EP02 set — state changes rather than end states.
    "gauge": gauge_scene,
    "world": world_scene,
    "windows": windows_scene,
    "barrier": barrier_scene,
    "backtrack": backtrack_scene,
    "door": door_scene,
    # EP04 set — two sites, one pen, and the ledger that split.
    "coasts": coasts_scene,
    "ledgers": ledgers_scene,
    # EP04 rebuild — places and people that replace recycled icons. Every one of these
    # takes a photographic plate for its ground; see HOUSE_STYLE §13.
    "nightdesk": nightdesk_scene,
    "crossing": crossing_scene,
    "clockwall": clockwall_scene,
    "sunrise": sunrise_scene,
    "fork": fork_scene,
    "haul": haul_scene,
    "vault": vault_scene,
    # EP05 — a system throttled by its own bookkeeping. Built for this story, not
    # inherited: an enquiry desk whose queue stops draining, one doorway everything is
    # funnelled through, the warehouse that never gives space back, a shuttered frontage
    # with the crowd outside it, four doors onto a wall, and a torch on a dead supply.
    "registry": registry_scene,
    "funnel": funnel_scene,
    "freelist": freelist_scene,
    "lockout": lockout_scene,
    "deadends": deadends_scene,
    "blindroom": blindroom_scene,
}


def render(ctx: cairo.Context, v: Visual | None, t: float, dur: float = 6.0) -> None:
    if v is None:
        _chrome(ctx)
        return
    fn = RENDERERS.get(v.renderer)
    if fn is None:
        raise KeyError(f"unknown visual renderer {v.renderer!r}; "
                       f"known: {', '.join(sorted(RENDERERS))}")
    fn(ctx, v, t, dur)
