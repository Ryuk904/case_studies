"""Pictorial illustrations, as opposed to boxes-and-arrows diagrams.

A flowchart tells you how a system is wired. It does not make anyone *feel* the thing.
Ninety-seven unread warnings should look like a stack of unread mail; a switch someone
reused should look like a switch. These are the shapes that carry a beat emotionally.

Everything here is drawn with sketch.py primitives, so illustrations inherit the same
hand-drawn line quality and the same draw-on animation as the diagrams.

Every function takes `progress` (0..1) so it can be traced on rather than popped in.
"""

from __future__ import annotations

import math

import cairo

from . import config, sketch

Color = tuple[float, float, float]


# ---------------------------------------------------------------- light switch
def switch(ctx: cairo.Context, cx: float, cy: float, scale: float = 1.0, *,
           on: bool = False, accent: Color = config.FAIL, throw: float | None = None,
           progress: float = 1.0) -> None:
    """A wall switch on its faceplate. The central metaphor of EP01.

    `throw` 0..1 overrides `on` with a continuous rocker position, so the switch can be
    seen to move. A switch that cuts from OFF to ON between two scenes is two pictures of
    a switch; a switch that throws is the event itself.
    """
    w, h = 190 * scale, 300 * scale
    x, y = cx - w / 2, cy - h / 2
    pen = sketch.Pen(color=config.INK, width=config.STROKE * 1.15)

    sketch.rect(ctx, x, y, w, h, pen, fill=config.BG_DEEP, fill_alpha=0.55,
                overshoot=6 * scale, progress=min(1.0, progress / 0.45))
    if progress < 0.45:
        return

    # Screw heads, top and bottom.
    p2 = min(1.0, (progress - 0.45) / 0.2)
    for sy in (y + 26 * scale, y + h - 26 * scale):
        sketch.ellipse(ctx, cx, sy, 9 * scale, 9 * scale,
                       sketch.Pen(color=config.MUTED, width=2.4), progress=p2)
    if progress < 0.65:
        return

    # The rocker itself: sits high when on, low when off.
    p3 = min(1.0, (progress - 0.65) / 0.35)
    rw, rh = w * 0.46, h * 0.40
    rx = cx - rw / 2
    u = (1.0 if on else 0.0) if throw is None else max(0.0, min(1.0, throw))
    # Travel is deliberately short of the faceplate ends: a full-height throw puts the
    # rocker on top of the screw heads.
    ry = cy - rh * (0.20 + 0.60 * u)
    lit = u > 0.5
    body = accent if lit else config.MUTED
    if 0.02 < u < 0.98:
        sketch.glow(ctx, cx, cy, w * 1.1, accent, 0.22 * (1 - abs(u - 0.5) * 2))
    sketch.rect(ctx, rx, ry, rw, rh, sketch.Pen(color=body, width=config.STROKE * 1.3),
                fill=body, fill_alpha=0.20 if lit else 0.10,
                overshoot=4 * scale, progress=p3)
    label = "ON" if lit else "OFF"
    tw, th = sketch.text_size(ctx, label, 26 * scale, config.FONT_SANS, bold=True)
    sketch.text(ctx, label, cx, ry + rh / 2 + th / 2, 34 * scale,
                body, config.FONT_SANS, align="center", bold=True, progress=p3)


# ------------------------------------------------------------------- envelopes
def envelope(ctx: cairo.Context, x: float, y: float, w: float, h: float,
             pen: sketch.Pen, *, fill: Color | None = None,
             progress: float = 1.0) -> None:
    sketch.rect(ctx, x, y, w, h, pen, fill=fill, fill_alpha=1.0, progress=progress,
                overshoot=2.5)
    if progress > 0.6:                       # the flap, a shallow V from the top corners
        p = min(1.0, (progress - 0.6) / 0.4)
        sketch.line(ctx, x, y, x + w / 2, y + h * 0.46, pen, progress=p)
        sketch.line(ctx, x + w, y, x + w / 2, y + h * 0.46, pen, progress=p)


def mail_pile(ctx: cairo.Context, cx: float, cy: float, n: int = 7,
              scale: float = 1.0, *, unread: bool = True,
              progress: float = 1.0) -> None:
    """A stack of unopened mail. Reads instantly as "nobody looked at these".

    The offset per envelope has to be a real fraction of the envelope's own height. A
    12px step on a 190px envelope stacks them all in the same place and the flap strokes
    tangle into scribble.
    """
    w, h = 250 * scale, 150 * scale
    dx, dy = 26 * scale, 30 * scale
    shown = max(0, min(n, int(round(progress * n + 0.001))))

    # Back to front, so the newest envelope sits on top of the pile.
    for i in range(shown):
        front = i == shown - 1 and shown == n
        jitter = sketch._noise(i * 977, 3) * 7 * scale
        x = cx - w / 2 - (n - 1 - i) * dx * 0.5 + jitter
        y = cy - h / 2 + (n - 1 - i) * dy * 0.5 - (n - 1) * dy * 0.25
        col = config.FAIL if (unread and front) else config.MUTED
        pen = sketch.Pen(color=col, width=config.STROKE * (1.15 if front else 0.9),
                         alpha=1.0 if front else 0.75)
        local = 1.0 if i < shown - 1 else max(0.35, min(1.0, (progress * n) % 1.0 or 1.0))
        # Opaque paper fill, so envelopes behind are occluded instead of showing through.
        envelope(ctx, x, y, w, h, pen, fill=config.BG, progress=local)
    if unread and shown:
        sketch.text(ctx, "all unread", cx, cy + (n - 1) * dy * 0.25 + h * 0.75 + 62 * scale,
                    26 * scale, config.FAIL, config.FONT_SANS, align="center",
                    progress=min(1.0, progress * 1.4))


# ------------------------------------------------------------------ unit chart
def dot_grid(ctx: cairo.Context, cx: float, cy: float, n: int, *,
             max_cols: int = 20, r: float = 9.0, gap: float = 26.0,
             color: Color = config.INK, progress: float = 1.0) -> tuple[float, float]:
    """n dots in a grid. Returns the block's (width, height)."""
    cols = min(max_cols, max(1, n))
    rows = math.ceil(n / cols)
    w, h = (cols - 1) * gap, (rows - 1) * gap
    x0, y0 = cx - w / 2, cy - h / 2
    shown = max(0, min(n, int(round(progress * n))))
    for i in range(shown):
        c, rw_ = i % cols, i // cols
        ctx.set_source_rgba(*color, 0.92)
        ctx.arc(x0 + c * gap, y0 + rw_ * gap, r, 0, math.tau)
        ctx.fill()
    return w, h


def scale_compare(ctx: cairo.Context, cx: float, cy: float, *,
                  small_n: int, small_label: str,
                  big_n: int, big_label: str,
                  max_h: float = 380.0,
                  progress: float = 1.0) -> None:
    """Two quantities, drawn to the same dot size so the ratio is physical.

    "212 orders became 4 million trades" is a number people nod at. Seeing 212 dots beside
    a field of dots that runs off the frame is a number people feel.
    """
    left_x, right_x = config.W * 0.26, config.W * 0.68
    s_gap, s_r = 20.0, 7.0
    b_cols, b_gap, b_r = 46, 15.0, 4.4

    _, s_h = dot_grid(ctx, left_x, cy, small_n, max_cols=16, r=s_r, gap=s_gap,
                      color=config.INK, progress=min(1.0, progress * 2))

    # The big side is deliberately clipped by the frame: it cannot be counted, which is the
    # point. Density stands in for magnitude. Rows are capped by the height budget rather
    # than a constant, so the field cannot grow into its own caption.
    b_rows = max(1, min(math.ceil(big_n / b_cols), int(max_h // b_gap) + 1))
    b_h, b_w = (b_rows - 1) * b_gap, (b_cols - 1) * b_gap
    b_x0 = right_x - b_w / 2
    p2 = max(0.0, min(1.0, (progress - 0.35) / 0.65))

    ctx.save()
    ctx.rectangle(config.W * 0.44, 0, config.W, config.H)
    ctx.clip()
    for i in range(min(int(big_n * p2), b_cols * b_rows)):
        c, r_ = i % b_cols, i // b_cols
        ctx.set_source_rgba(*config.FAIL, 0.75)
        ctx.arc(b_x0 + c * b_gap, cy - b_h / 2 + r_ * b_gap, b_r, 0, math.tau)
        ctx.fill()
    ctx.restore()

    # One baseline for both captions, clear of whichever field is taller. Anchoring them to
    # a fixed offset put the red caption underneath the last row of its own dots.
    label_y = cy + max(s_h / 2 + s_r, b_h / 2 + b_r) + 62
    sketch.text(ctx, small_label, left_x, label_y, config.SZ_ANNOT,
                config.INK, config.FONT_SANS, align="center",
                progress=min(1.0, progress * 2))
    sketch.text(ctx, big_label, right_x, label_y, config.SZ_ANNOT,
                config.FAIL, config.FONT_SANS, align="center", progress=p2)


# ----------------------------------------------------------------------- clock
def clock(ctx: cairo.Context, cx: float, cy: float, radius: float = 180.0, *,
          fraction: float = 1.0, accent: Color = config.FAIL,
          progress: float = 1.0) -> None:
    """A clock face with an elapsed wedge. `fraction` is how much time has burned."""
    pen = sketch.Pen(color=config.INK, width=config.STROKE * 1.2)
    sketch.ellipse(ctx, cx, cy, radius, radius, pen, progress=min(1.0, progress / 0.5))
    if progress < 0.5:
        return

    p = min(1.0, (progress - 0.5) / 0.5)
    ctx.set_source_rgba(*accent, 0.20)
    ctx.move_to(cx, cy)
    ctx.arc(cx, cy, radius * 0.92, -math.pi / 2, -math.pi / 2 + math.tau * fraction * p)
    ctx.close_path()
    ctx.fill()

    for i in range(12):                       # hour ticks
        a = i / 12 * math.tau
        inner = radius * (0.80 if i % 3 else 0.72)
        sketch.line(ctx, cx + math.cos(a) * inner, cy + math.sin(a) * inner,
                    cx + math.cos(a) * radius * 0.93, cy + math.sin(a) * radius * 0.93,
                    sketch.Pen(color=config.MUTED, width=2.6, passes=1), progress=p)

    a = -math.pi / 2 + math.tau * fraction * p
    sketch.line(ctx, cx, cy, cx + math.cos(a) * radius * 0.78,
                cy + math.sin(a) * radius * 0.78,
                sketch.Pen(color=accent, width=config.STROKE * 1.6), progress=p)
    sketch.ellipse(ctx, cx, cy, 10, 10, pen, fill=config.INK, progress=p)


# ------------------------------------------------------------------- people bar
def people(ctx: cairo.Context, cx: float, cy: float, n: int = 10, *,
           highlight: int = 1, scale: float = 1.0,
           progress: float = 1.0) -> None:
    """n little figures, `highlight` of them accented. For "one in ten"."""
    step = 108 * scale
    x0 = cx - (n - 1) * step / 2
    shown = max(0, min(n, int(round(progress * n))))
    for i in range(shown):
        x = x0 + i * step
        hot = i < highlight
        col = config.FAIL if hot else config.MUTED
        pen = sketch.Pen(color=col, width=config.STROKE * (1.15 if hot else 0.85))
        sketch.ellipse(ctx, x, cy - 44 * scale, 20 * scale, 20 * scale, pen,
                       fill=col if hot else None, fill_alpha=0.22)
        # Shoulders and body as a simple rounded torso.
        sketch.line(ctx, x, cy - 20 * scale, x, cy + 34 * scale, pen)
        sketch.line(ctx, x - 26 * scale, cy + 4 * scale, x + 26 * scale, cy + 4 * scale, pen)
        sketch.line(ctx, x, cy + 34 * scale, x - 20 * scale, cy + 76 * scale, pen)
        sketch.line(ctx, x, cy + 34 * scale, x + 20 * scale, cy + 76 * scale, pen)


# ------------------------------------------------------------------- counter
def counter(ctx: cairo.Context, cx: float, cy: float, value: str, *,
            scale: float = 1.0, blank: bool = False, label: str = "",
            progress: float = 1.0) -> None:
    """A mechanical tally counter. `blank=True` shows empty windows.

    The tally is the hinge of EP01 — it is counted, then it is moved, then nothing is
    there. An odometer makes "there was nothing to read" a picture instead of a sentence.
    """
    digits = list(value) if not blank else ["-"] * max(3, len(value))
    dw, dh = 92 * scale, 132 * scale
    gap = 12 * scale
    total = len(digits) * dw + (len(digits) - 1) * gap
    x0 = cx - total / 2
    col = config.FAIL if blank else config.INK

    sketch.rect(ctx, x0 - 26 * scale, cy - dh / 2 - 26 * scale,
                total + 52 * scale, dh + 52 * scale,
                sketch.Pen(color=config.INK, width=config.STROKE * 1.2),
                fill=config.BG_DEEP, fill_alpha=0.5, overshoot=6 * scale,
                progress=min(1.0, progress / 0.4))
    if progress < 0.4:
        return

    p = min(1.0, (progress - 0.4) / 0.6)
    shown = max(0, min(len(digits), int(round(p * len(digits) + 0.001))))
    for i in range(shown):
        x = x0 + i * (dw + gap)
        sketch.rect(ctx, x, cy - dh / 2, dw, dh,
                    sketch.Pen(color=config.MUTED, width=2.6),
                    fill=config.BG, fill_alpha=1.0, overshoot=3 * scale)
        size = 84 * scale
        sketch.text(ctx, digits[i], x + dw / 2, cy + size * 0.36, size,
                    col, config.FONT_SANS, align="center", bold=True)
    if label:
        sketch.text(ctx, label, cx, cy + dh / 2 + 92 * scale, config.SZ_ANNOT,
                    col, config.FONT_SANS, align="center", progress=p)


# --------------------------------------------------------------------- alarm
def alarm(ctx: cairo.Context, cx: float, cy: float, *, scale: float = 1.0,
          ringing: bool = True, t: float = 0.0, progress: float = 1.0) -> None:
    """A ceiling smoke alarm, sounding. Sound arcs pulse so the frame never freezes."""
    r = 118 * scale
    pen = sketch.Pen(color=config.INK, width=config.STROKE * 1.2)
    sketch.ellipse(ctx, cx, cy, r, r, pen, fill=config.BG_DEEP, fill_alpha=0.55,
                   progress=min(1.0, progress / 0.4))
    if progress < 0.4:
        return
    p = min(1.0, (progress - 0.4) / 0.35)
    sketch.ellipse(ctx, cx, cy, r * 0.52, r * 0.52,
                   sketch.Pen(color=config.MUTED, width=2.6), progress=p)
    # Vent slots, so it reads as a device rather than a plain disc.
    for i in range(6):
        a = i / 6 * math.pi
        sketch.line(ctx, cx + math.cos(a) * r * 0.44, cy + math.sin(a) * r * 0.44,
                    cx - math.cos(a) * r * 0.44, cy - math.sin(a) * r * 0.44,
                    sketch.Pen(color=config.MUTED, width=2.2, passes=1), progress=p)
    if not ringing or progress < 0.75:
        return

    # The indicator and the sound arcs pulse together, on a cycle driven by wall time.
    pulse = 0.5 + 0.5 * math.sin(t * 5.2)
    sketch.ellipse(ctx, cx, cy, 15 * scale, 15 * scale,
                   sketch.Pen(color=config.FAIL, width=2.4),
                   fill=config.FAIL, fill_alpha=0.35 + 0.6 * pulse)
    for side in (-1, 1):
        for k in range(3):
            rr = r * (1.28 + k * 0.30)
            a0 = -0.55 if side > 0 else math.pi - 0.55
            a1 = 0.55 if side > 0 else math.pi + 0.55
            ctx.set_source_rgba(*config.FAIL, (0.55 - k * 0.14) * (0.35 + 0.65 * pulse))
            ctx.set_line_width(config.STROKE * 1.3)
            ctx.new_path()
            ctx.arc(cx, cy, rr, min(a0, a1), max(a0, a1))
            ctx.stroke()


# ------------------------------------------------------------------ calendar
def calendar(ctx: cairo.Context, cx: float, cy: float, years: list[str], *,
             mark: int = -1, scale: float = 1.0, caption: str = "",
             progress: float = 1.0) -> None:
    """A row of year chips, one of them marked. For spans of dormant time."""
    if not years:
        return
    w, h = 148 * scale, 168 * scale
    gap = 22 * scale
    total = len(years) * w + (len(years) - 1) * gap
    if total > config.W - config.SAFE * 2:              # squeeze rather than overflow
        k = (config.W - config.SAFE * 2) / total
        w, gap, total = w * k, gap * k, total * k
    x0 = cx - total / 2
    shown = max(0, min(len(years), int(round(progress * len(years) + 0.001))))

    for i in range(shown):
        x = x0 + i * (w + gap)
        hot = i == mark
        col = config.FAIL if hot else config.MUTED
        pen = sketch.Pen(color=col, width=config.STROKE * (1.25 if hot else 0.85))
        sketch.rect(ctx, x, cy - h / 2, w, h, pen,
                    fill=config.FAIL if hot else config.BG_DEEP,
                    fill_alpha=0.14 if hot else 0.45, overshoot=4 * scale)
        # Two binder rings along the top edge.
        for fx in (0.30, 0.70):
            sketch.line(ctx, x + w * fx, cy - h / 2 - 12 * scale, x + w * fx, cy - h / 2 + 14 * scale,
                        sketch.Pen(color=col, width=2.4, passes=1))
        sketch.line(ctx, x, cy - h / 2 + 40 * scale, x + w, cy - h / 2 + 40 * scale,
                    sketch.Pen(color=col, width=2.2, passes=1))
        size = sketch.fit_size(ctx, years[i], 52 * scale, w * 0.80, config.FONT_SANS, bold=True)
        sketch.text(ctx, years[i], x + w / 2, cy + size * 0.34, size,
                    config.FAIL if hot else config.INK, config.FONT_SANS,
                    align="center", bold=True)
    if caption:
        sketch.text(ctx, caption, cx, cy + h / 2 + 78 * scale, config.SZ_ANNOT,
                    config.MUTED, config.FONT_SANS, align="center",
                    progress=min(1.0, progress * 1.3))


# ----------------------------------------------------------------- checklist
def checklist(ctx: cairo.Context, cx: float, cy: float, items: list[str], *,
              marks: list[str] | None = None, scale: float = 1.0,
              progress: float = 1.0) -> None:
    """Rows with a box each: "tick", "cross", or "" for an empty box.

    Empty boxes are the point in EP01 — nobody checked, so nothing is ticked.
    """
    if not items:
        return
    marks = marks or [""] * len(items)
    box = 52 * scale
    lh = 104 * scale
    size = 46 * scale
    widest = max(sketch.text_size(ctx, s, size, config.FONT_SANS)[0] for s in items)
    block_w = box + 34 * scale + widest
    x0 = cx - block_w / 2
    y0 = cy - (len(items) - 1) * lh / 2

    per = 1.0 / len(items)
    for i, label in enumerate(items):
        p = max(0.0, min(1.0, (progress - i * per * 0.85) / max(per, 1e-6)))
        if p <= 0.0:
            break
        y = y0 + i * lh
        m = marks[i] if i < len(marks) else ""
        col = config.FAIL if m == "cross" else (config.OK if m == "tick" else config.MUTED)
        sketch.rect(ctx, x0, y - box / 2, box, box,
                    sketch.Pen(color=col, width=config.STROKE * 1.1),
                    overshoot=3 * scale, progress=min(1.0, p / 0.5))
        if p > 0.5:
            q = min(1.0, (p - 0.5) / 0.5)
            mp = sketch.Pen(color=col, width=config.STROKE * 1.5)
            if m == "tick":
                sketch.line(ctx, x0 + box * 0.20, y, x0 + box * 0.44, y + box * 0.26, mp,
                            progress=q)
                sketch.line(ctx, x0 + box * 0.44, y + box * 0.26, x0 + box * 0.84,
                            y - box * 0.30, mp, progress=q)
            elif m == "cross":
                sketch.line(ctx, x0 + box * 0.20, y - box * 0.28,
                            x0 + box * 0.80, y + box * 0.28, mp, progress=q)
                sketch.line(ctx, x0 + box * 0.80, y - box * 0.28,
                            x0 + box * 0.20, y + box * 0.28, mp, progress=q)
            sketch.text(ctx, label, x0 + box + 34 * scale, y + size * 0.34, size,
                        config.INK, config.FONT_SANS, progress=q)


# ---------------------------------------------------------------------- loop
def loop(ctx: cairo.Context, cx: float, cy: float, *, radius: float = 190.0,
         t: float = 0.0, label: str = "", progress: float = 1.0) -> None:
    """A cycle with no exit: a closed ring turning, and a barred way out.

    The ring has to read as CLOSED — that is the whole point of the beat. An open arc
    reads as an arrow that simply has not finished, which is the opposite meaning.
    """
    p = min(1.0, progress / 0.55)
    steps = 60
    pen = sketch.Pen(color=config.INK, width=config.STROKE * 1.6)
    span = math.tau * 0.97          # all but a hair, so it is unmistakably a cycle
    start = -math.pi / 2 + 0.16
    pts = [(cx + math.cos(start + span * i / steps) * radius,
            cy + math.sin(start + span * i / steps) * radius) for i in range(steps + 1)]
    upto = max(2, int(len(pts) * p))
    for i in range(1, upto):
        sketch.line(ctx, *pts[i - 1], *pts[i], pen)

    # Arrow head at the ring's leading end, so the direction of travel is explicit.
    if p >= 1.0:
        hx, hy = pts[-1]
        ang = start + span + math.pi / 2
        for side in (+1, -1):
            a = ang + math.pi + side * 0.45
            sketch.line(ctx, hx, hy, hx + math.cos(a) * 26, hy + math.sin(a) * 26, pen)
    if progress < 0.55:
        return

    q = min(1.0, (progress - 0.55) / 0.45)
    # The exit that exists and cannot be taken. Placed out to the side rather than above
    # the ring: there is simply more room there, and the strike-through needs to sit on the
    # arrow without landing on the ring or its label.
    ax0, ax1 = cx + radius + 16, cx + radius + 264
    sketch.arrow(ctx, ax0, cy, ax1, cy,
                 sketch.Pen(color=config.MUTED, width=config.STROKE), progress=q)
    if q > 0.45:
        r2 = min(1.0, (q - 0.45) / 0.55)
        bp = sketch.Pen(color=config.FAIL, width=config.STROKE * 2.0)
        mx = (ax0 + ax1) / 2
        sketch.line(ctx, mx - 36, cy - 38, mx + 36, cy + 38, bp, progress=r2)
        sketch.line(ctx, mx + 36, cy - 38, mx - 36, cy + 38, bp, progress=r2)
        sketch.text(ctx, "no way out", mx, cy + 104, config.SZ_ANNOT, config.FAIL,
                    config.FONT_SANS, align="center", progress=r2)

    # Orbiting dot — the thing going round forever. Driven by wall time, not progress.
    a = start + (t * 0.55 % 1.0) * math.tau
    ctx.set_source_rgba(*config.FAIL, 0.95)
    ctx.arc(cx + math.cos(a) * radius, cy + math.sin(a) * radius, 14, 0, math.tau)
    ctx.fill()
    if label:
        sketch.text(ctx, label, cx, cy + config.SZ_HEAD * 0.34, config.SZ_HEAD,
                    config.MUTED, config.FONT_SANS, align="center", progress=q)


# ----------------------------------------------------------------- dashboard
def dashboard(ctx: cairo.Context, cx: float, cy: float, *, cols: int = 4, rows: int = 3,
              bad: int = -1, t: float = 0.0, progress: float = 1.0) -> None:
    """A wall of panels, all reporting healthy. `bad` marks one that is not.

    The point of the beat is that everything looked fine, so the default really is all
    green. The little bars keep moving, because a dashboard that is frozen looks broken
    and this one very much did not.
    """
    pw, ph = 268.0, 148.0
    gx, gy = 34.0, 30.0
    total_w = cols * pw + (cols - 1) * gx
    total_h = rows * ph + (rows - 1) * gy
    x0, y0 = cx - total_w / 2, cy - total_h / 2
    n = cols * rows
    shown = max(0, min(n, int(round(progress * n + 0.001))))

    for i in range(shown):
        c, r = i % cols, i // cols
        x, y = x0 + c * (pw + gx), y0 + r * (ph + gy)
        hot = i == bad
        col = config.FAIL if hot else config.OK
        sketch.rect(ctx, x, y, pw, ph, sketch.Pen(color=config.MUTED, width=2.4),
                    fill=col, fill_alpha=0.10, overshoot=4)
        # A small live bar chart per panel, phase-offset so the wall is not in lockstep.
        bars = 7
        bw = (pw - 44) / bars
        for b in range(bars):
            h = (0.30 + 0.55 * (0.5 + 0.5 * math.sin(t * 1.6 + i * 0.7 + b * 0.9))) * (ph - 52)
            ctx.set_source_rgba(*col, 0.72)
            ctx.rectangle(x + 22 + b * bw, y + ph - 22 - h, bw * 0.62, h)
            ctx.fill()
        sketch.ellipse(ctx, x + pw - 24, y + 22, 8, 8,
                       sketch.Pen(color=col, width=2.0), fill=col, fill_alpha=0.85)


# ------------------------------------------------------------------- servers
def servers(ctx: cairo.Context, cx: float, cy: float, n: int = 8, *,
            bad: set[int] | None = None, scale: float = 1.0, label: str = "",
            progress: float = 1.0) -> None:
    """n machines in a row. `bad` is a set of 0-based indices drawn in the failure accent."""
    bad = bad or set()
    w, h = 132 * scale, 232 * scale
    gap = 26 * scale
    total = n * w + (n - 1) * gap
    if total > config.W - config.SAFE * 2:
        # Squeeze height by the same factor, or eight machines forced into the safe width
        # come out as tall thin slivers instead of computers.
        k = (config.W - config.SAFE * 2) / total
        w, h, gap, total = w * k, h * k, gap * k, total * k
    x0 = cx - total / 2
    shown = max(0, min(n, int(round(progress * n + 0.001))))

    for i in range(shown):
        x = x0 + i * (w + gap)
        hot = i in bad
        col = config.FAIL if hot else config.MUTED
        pen = sketch.Pen(color=col, width=config.STROKE * (1.3 if hot else 0.9))
        sketch.rect(ctx, x, cy - h / 2, w, h, pen,
                    fill=config.FAIL if hot else config.BG_DEEP,
                    fill_alpha=0.13 if hot else 0.45, overshoot=4 * scale)
        for k in range(4):                       # drive bays
            yy = cy - h / 2 + (28 + k * 30) * scale
            sketch.line(ctx, x + 18 * scale, yy, x + w - 18 * scale, yy,
                        sketch.Pen(color=col, width=2.2, alpha=0.7, passes=1))
        sketch.ellipse(ctx, x + w / 2, cy + h / 2 - 34 * scale, 7 * scale, 7 * scale,
                       sketch.Pen(color=col, width=2.0),
                       fill=col, fill_alpha=0.9 if hot else 0.4)
    if label:
        sketch.text(ctx, label, cx, cy + h / 2 + 74 * scale, config.SZ_ANNOT,
                    config.MUTED, config.FONT_SANS, align="center",
                    progress=min(1.0, progress * 1.3))


# --------------------------------------------------------------- broken link
def broken_link(ctx: cairo.Context, cx: float, cy: float, *, scale: float = 1.0,
                gap: float = 96.0, left: str = "", right: str = "",
                progress: float = 1.0) -> None:
    """Two chain links that no longer meet. For a reference that was never reconnected.

    A link is an annulus, not an outline: the inner opening has to be close to the outer
    edge or it reads as an eye rather than a ring of metal. Each one also carries a stub of
    the link it used to be joined to, so the break is visibly a break and not just a space.
    """
    rx, ry = 104 * scale, 76 * scale
    off = gap * scale / 2 + rx
    p1 = min(1.0, progress / 0.5)
    pen = sketch.Pen(color=config.INK, width=config.STROKE * 1.7)
    inner = sketch.Pen(color=config.INK, width=config.STROKE * 1.4)

    for sign, lbl in ((-1, left), (1, right)):
        lx = cx + sign * off
        sketch.ellipse(ctx, lx, cy, rx, ry, pen, progress=p1)
        sketch.ellipse(ctx, lx, cy, rx * 0.66, ry * 0.52, inner, progress=p1)
        if lbl:
            sketch.text(ctx, lbl, lx, cy + ry + 92 * scale, config.SZ_ANNOT,
                        config.MUTED, config.FONT_SANS, align="center", progress=p1)
    if progress < 0.5:
        return

    # The break itself, in the gap between the two links: a torn seam. Drawn as a zigzag
    # rather than a cross, because a cross over a gap reads as "forbidden" while a tear
    # reads as "this used to be joined and came apart" — which is the actual history.
    q = min(1.0, (progress - 0.5) / 0.5)
    tp = sketch.Pen(color=config.FAIL, width=config.STROKE * 2.2)
    zig = [(cx - 30 * scale, cy - ry * 1.10), (cx + 28 * scale, cy - ry * 0.52),
           (cx - 28 * scale, cy + ry * 0.06), (cx + 30 * scale, cy + ry * 0.64),
           (cx - 22 * scale, cy + ry * 1.10)]
    for i in range(1, len(zig)):
        seg = max(0.0, min(1.0, q * (len(zig) - 1) - (i - 1)))
        if seg <= 0:
            break
        sketch.line(ctx, *zig[i - 1], *zig[i], tp, progress=seg)
    if q > 0.7:
        r2 = min(1.0, (q - 0.7) / 0.3)
        sketch.text(ctx, "not connected", cx, cy + ry + 92 * scale, config.SZ_ANNOT,
                    config.FAIL, config.FONT_SANS, align="center", progress=r2)


# ------------------------------------------------------------------- padlock
def padlock(ctx: cairo.Context, cx: float, cy: float, *, scale: float = 1.0,
            intact: bool = True, caption: str = "", progress: float = 1.0) -> None:
    """A padlock, closed. For "nobody broke in" — the absence of an attack, shown."""
    # A padlock body is close to square. Made much wider than tall, with a wide arch over
    # it, the silhouette is a handbag — which is exactly what the first attempt looked like.
    bw, bh = 258 * scale, 236 * scale
    by = cy + 56 * scale                      # body sits low; the shackle needs headroom
    col = config.INK if intact else config.FAIL
    pen = sketch.Pen(color=col, width=config.STROKE * 1.6)

    # Shackle first: a lock reads as a lock from the arch, not the body. Drawn as a BAND,
    # two parallel arcs with legs, not a single stroke. A one-line arch over a rectangle is
    # a handbag handle, which is exactly what the first two attempts looked like.
    p1 = min(1.0, progress / 0.45)
    sr = bw * 0.30
    band = 26 * scale
    top = by - bh / 2 - 52 * scale
    steps = 34
    leg_end = by - bh / 2 + 8 * scale
    for radius in (sr, sr - band):
        pts = [(cx + math.cos(math.pi + math.pi * i / steps) * radius,
                top + math.sin(math.pi + math.pi * i / steps) * radius)
               for i in range(steps + 1)]
        upto = max(2, int(len(pts) * p1))
        for i in range(1, upto):
            sketch.line(ctx, *pts[i - 1], *pts[i], pen)
    if p1 >= 1.0:
        for sign in (-1, 1):
            for radius in (sr, sr - band):
                sketch.line(ctx, cx + sign * radius, top,
                            cx + sign * radius, leg_end, pen)
    if progress < 0.45:
        return

    p2 = min(1.0, (progress - 0.45) / 0.4)
    sketch.rect(ctx, cx - bw / 2, by - bh / 2, bw, bh, pen,
                fill=config.BG_DEEP, fill_alpha=0.6, overshoot=6 * scale, progress=p2)
    if p2 >= 1.0:
        # Keyhole: round bore plus a tapered slot. It is what turns a rounded box into a
        # lock at a glance, so it has to be big enough to see at thumbnail size.
        kp = sketch.Pen(color=col, width=config.STROKE * 1.4)
        sketch.ellipse(ctx, cx, by - 26 * scale, 34 * scale, 34 * scale, kp,
                       fill=col, fill_alpha=0.16)
        for sign in (-1, 1):
            sketch.line(ctx, cx + sign * 14 * scale, by - 2 * scale,
                        cx + sign * 26 * scale, by + 68 * scale, kp)
        sketch.line(ctx, cx - 26 * scale, by + 68 * scale,
                    cx + 26 * scale, by + 68 * scale, kp)
    if caption:
        sketch.text(ctx, caption, cx, by + bh / 2 + 82 * scale, config.SZ_ANNOT,
                    config.MUTED, config.FONT_SANS, align="center",
                    progress=min(1.0, max(0.0, (progress - 0.7) / 0.3)))


# ==================================================================== EP02 set
# Everything below animates a STATE CHANGE rather than drawing a finished picture. The note
# back on EP01 was that its illustrations appear and then hold, and the frames that survived
# that criticism were the two with an ongoing motion in them (the alarm's arcs, the
# dashboard's bars). So each of these takes wall-clock `t` as well as `progress`, and each
# has something still moving at second fourteen.


# ---------------------------------------------------------------------- gauge
def gauge(ctx: cairo.Context, cx: float, cy: float, *, value: float = 1.0,
          scale: float = 1.0, t: float = 0.0, label: str = "",
          progress: float = 1.0) -> None:
    """A dial whose needle sweeps up and then pins against the stop, trembling.

    `value` is 0..1 of full scale. The tremble is the whole point: a needle parked at 100%
    reads as a picture of a broken gauge, while a needle fighting the stop reads as a
    machine being held down. It is also what keeps the frame alive fifteen seconds in.

    The dial is an ELLIPSE, not a circle, and that is a layout decision rather than a
    stylistic one. A half-circle big enough to own the frame horizontally is also 480px
    tall above its pivot, which puts its crown through the headline. Widening it and
    flattening it buys the width the subject needs without spending the height there is
    none of.
    """
    rx, ry = 620 * scale, 330 * scale
    pen = sketch.Pen(color=config.INK, width=config.STROKE * 1.25)
    a0, a1 = math.pi * 1.02, math.pi * 1.98        # a wide, nearly-flat dial

    def on(f: float, k: float = 1.0) -> tuple[float, float]:
        a = a0 + (a1 - a0) * f
        return cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k

    # Face.
    p1 = min(1.0, progress / 0.35)
    steps = 56
    pts = [on(i / steps) for i in range(steps + 1)]
    upto = max(2, int(len(pts) * p1))
    for i in range(1, upto):
        sketch.line(ctx, *pts[i - 1], *pts[i], pen)
    if progress < 0.35:
        return

    p2 = min(1.0, (progress - 0.35) / 0.25)
    # Red zone across the top of the scale, so "pinned" has somewhere to mean something.
    for i in range(20):
        f0, f1 = 0.80 + 0.20 * i / 20, 0.80 + 0.20 * (i + 1) / 20
        ctx.set_source_rgba(*config.FAIL, 0.30 * p2)
        ctx.set_line_width(26 * scale)
        ctx.new_path()
        ctx.move_to(*on(f0, 0.94))
        ctx.line_to(*on(f1, 0.94))
        ctx.stroke()

    for i in range(11):                              # ticks, longer every fifth
        f = i / 10
        inner = 0.78 if i % 5 else 0.68
        sketch.line(ctx, *on(f, inner), *on(f, 0.99),
                    sketch.Pen(color=config.MUTED, width=2.8, passes=1), progress=p2)
    if progress < 0.60:
        return

    # Sweep, then hold against the stop with a small unsteady overshoot.
    p3 = min(1.0, (progress - 0.60) / 0.40)
    swept = value * (1 - (1 - p3) ** 2)
    if p3 >= 1.0 and value > 0.9:
        swept = min(1.0, value + 0.012 * math.sin(t * 17.0) + 0.006 * math.sin(t * 6.3))
    hot = swept > 0.80
    col = config.FAIL if hot else config.ACCENT
    nx, ny = on(swept, 0.88)
    if hot:
        # Small and dim. At 190px and 0.34 the bloom was wider than the needle was long and
        # the dial read as a red smudge with no pointer in it.
        sketch.glow(ctx, nx, ny, 110 * scale, config.FAIL,
                    0.13 + 0.07 * (0.5 + 0.5 * math.sin(t * 5.0)))
    sketch.line(ctx, cx, cy, nx, ny, sketch.Pen(color=col, width=config.STROKE * 2.1))
    sketch.ellipse(ctx, cx, cy, 19 * scale, 19 * scale, pen,
                   fill=config.INK, fill_alpha=1.0)

    read = f"{int(round(swept * 100))}%"
    size = 150 * scale
    sketch.text(ctx, read, cx, cy + size * 1.02, size, col, config.FONT_SANS,
                align="center", bold=True)
    if label:
        sketch.text(ctx, label, cx, cy + size * 1.02 + 66 * scale, config.SZ_ANNOT,
                    config.MUTED, config.FONT_SANS, align="center", progress=p3)


# ---------------------------------------------------------------------- world
_CITIES = [
    # A stylised scatter, not a real map: enough landmass rhythm to read as "everywhere"
    # without pretending to be geography we would then have to source.
    (-0.78, -0.30), (-0.66, -0.12), (-0.71, 0.10), (-0.55, -0.34), (-0.52, 0.06),
    (-0.44, 0.30), (-0.35, -0.22), (-0.30, 0.44), (-0.20, -0.42), (-0.14, -0.05),
    (-0.08, 0.22), (-0.02, -0.30), (0.05, 0.05), (0.10, -0.48), (0.14, 0.36),
    (0.22, -0.16), (0.28, 0.14), (0.33, -0.38), (0.40, 0.42), (0.46, -0.04),
    (0.52, 0.24), (0.58, -0.30), (0.64, 0.08), (0.70, -0.44), (0.74, 0.32),
    (0.80, -0.14), (-0.62, 0.38), (0.18, 0.50), (-0.26, 0.14), (0.62, 0.46),
]


def world(ctx: cairo.Context, cx: float, cy: float, *, scale: float = 1.0,
          spread: float = 1.0, bad: bool = True, t: float = 0.0,
          origin: int = 12, progress: float = 1.0) -> None:
    """Cities lighting up outward from one origin, as a change propagates.

    `spread` 0..1 is how far the wave has travelled. This is the picture of a global
    key-value store: one write here, every machine on earth two seconds later. The ripple
    re-fires on a slow loop afterwards so the frame keeps saying "and it is still doing
    this" long after the wave has landed.
    """
    rx, ry = 640 * scale, 268 * scale
    pen = sketch.Pen(color=config.MUTED, width=config.STROKE * 0.8, alpha=0.8)
    p1 = min(1.0, progress / 0.4)
    sketch.ellipse(ctx, cx, cy, rx, ry, pen, progress=p1)
    for k in (-0.55, 0.0, 0.55):                     # latitude arcs
        sketch.ellipse(ctx, cx, cy + ry * k, rx * math.sqrt(max(0.02, 1 - k * k)),
                       ry * 0.16, sketch.Pen(color=config.MUTED, width=2.0,
                                             alpha=0.45, passes=1), progress=p1)
    if progress < 0.4:
        return

    ox, oy = _CITIES[origin % len(_CITIES)]
    reach = max(math.hypot(a - ox, b - oy) for a, b in _CITIES) or 1.0
    front = spread * reach * 1.02

    # The repeating pulse: once the wave has landed, send another one every four seconds.
    echo = (t % 4.0) / 4.0 * reach * 1.15 if spread >= 0.999 else -1.0

    for i, (a, b) in enumerate(_CITIES):
        x, y = cx + a * rx * 0.92, cy + b * ry * 1.55
        d = math.hypot(a - ox, b - oy)
        lit = d <= front
        col = (config.FAIL if bad else config.ACCENT) if lit else config.MUTED
        # Pop as the front passes: a dot that grows and settles reads as arrival.
        age = max(0.0, front - d)
        r = 8.5 * scale * (1.0 + 1.5 * max(0.0, 1 - age / 0.18)) if lit else 6.0 * scale
        ctx.set_source_rgba(*col, 0.95 if lit else 0.45)
        ctx.arc(x, y, r, 0, math.tau)
        ctx.fill()
        if lit and abs(echo - d) < 0.10:
            ctx.set_source_rgba(*col, 0.55 * (1 - abs(echo - d) / 0.10))
            ctx.arc(x, y, r * 2.6, 0, math.tau)
            ctx.fill()
        if i == origin % len(_CITIES):
            sketch.ellipse(ctx, x, y, 20 * scale, 20 * scale,
                           sketch.Pen(color=config.ACCENT, width=2.6))

    # The wavefront itself, as an expanding ring on the origin.
    for f, alpha in ((front, 0.5), (echo, 0.32)):
        if 0.0 < f < reach * 1.2:
            ctx.set_source_rgba(*config.ACCENT, alpha)
            ctx.set_line_width(3.4)
            ctx.new_path()
            ctx.save()
            ctx.translate(cx + ox * rx * 0.92, cy + oy * ry * 1.55)
            ctx.scale(rx * 0.92, ry * 1.55)
            ctx.arc(0, 0, f, 0, math.tau)
            ctx.restore()
            ctx.stroke()


# -------------------------------------------------------------------- windows
def windows(ctx: cairo.Context, cx: float, cy: float, *, cols: int = 4, rows: int = 3,
            bad: float = 0.0, t: float = 0.0, code: str = "502",
            scale: float = 1.0, progress: float = 1.0) -> None:
    """A wall of browser windows. `bad` 0..1 is the fraction that have fallen over.

    They fail one at a time in a fixed scatter order rather than row by row, because a
    left-to-right sweep reads as a wipe effect and a scatter reads as an outage.
    """
    pw, ph = 268.0 * scale, 176.0 * scale
    gx, gy = 30.0 * scale, 28.0 * scale
    n = cols * rows
    x0 = cx - (cols * pw + (cols - 1) * gx) / 2
    y0 = cy - (rows * ph + (rows - 1) * gy) / 2
    shown = max(0, min(n, int(round(progress * n + 0.001))))
    # Deterministic scatter order, stable across frames.
    order = sorted(range(n), key=lambda i: sketch._noise(i * 131, 5))
    failed = set(order[:int(round(bad * n))])

    for i in range(shown):
        c, r = i % cols, i // cols
        x, y = x0 + c * (pw + gx), y0 + r * (ph + gy)
        down = i in failed
        col = config.FAIL if down else config.MUTED
        sketch.rect(ctx, x, y, pw, ph, sketch.Pen(color=col, width=2.6),
                    fill=config.FAIL if down else config.BG_DEEP,
                    fill_alpha=0.13 if down else 0.6, overshoot=3)
        bar = 34 * scale
        sketch.line(ctx, x, y + bar, x + pw, y + bar,
                    sketch.Pen(color=col, width=2.0, alpha=0.7, passes=1))
        for k in range(3):                           # traffic-light dots
            sketch.ellipse(ctx, x + 18 * scale + k * 20 * scale, y + bar / 2,
                           5 * scale, 5 * scale,
                           sketch.Pen(color=col, width=1.6, alpha=0.8),
                           fill=col, fill_alpha=0.5)
        if down:
            sketch.text(ctx, code, x + pw / 2, y + ph / 2 + 26 * scale, 74 * scale,
                        config.FAIL, config.FONT_SANS, align="center", bold=True)
        else:
            # Content lines that breathe, so the healthy half of the wall is not a still.
            for k in range(3):
                w = pw * (0.35 + 0.42 * (0.5 + 0.5 * math.sin(t * 1.3 + i * 0.8 + k)))
                ctx.set_source_rgba(*config.MUTED, 0.55)
                ctx.rectangle(x + 20 * scale, y + bar + 26 * scale + k * 26 * scale,
                              w, 9 * scale)
                ctx.fill()


# ------------------------------------------------------------------- barrier
def barrier(ctx: cairo.Context, cx: float, cy: float, *, scale: float = 1.0,
            gap: bool = True, t: float = 0.0, label: str = "",
            progress: float = 1.0) -> None:
    """A grate of vertical bars with one bar missing, and something going through the hole.

    For a protection that was removed. A crossed-out box says "this is missing"; a barrier
    with a hole in it and something sailing through says what missing *costs*.

    The first attempt drew a horizontal guard rail with the runaway rolling along the
    ground underneath it, which is a picture of something that was never going to be
    stopped by that barrier in the first place. The topology has to match the claim: bars
    across the direction of travel, spaced closer than the thing they stop, and one bar
    short is the only way through.
    """
    n = 15
    span = 1080 * scale
    top, bottom = cy - 260 * scale, cy + 260 * scale
    x0 = cx - span / 2
    step = span / (n - 1)
    missing = 5 if gap else -1
    ball_r = 46 * scale

    p1 = min(1.0, progress / 0.55)
    q = min(1.0, max(0.0, (progress - 0.55) / 0.45))

    # The runaway is drawn BEFORE the bars, so it passes behind them and only comes clear
    # where one is missing. Drawn on top it floats over the barrier everywhere and the
    # picture says the opposite of what the beat says.
    if q > 0.35:
        period = 3.6
        u = (t % period) / period
        bx = x0 - 220 * scale + (span + 460 * scale) * u
        by = cy
        if not gap:
            # An intact barrier has to actually stop it, or the bookend frame says the same
            # thing as the broken one. It runs up, hits the bars, and is thrown back.
            hit = x0 - ball_r - 6 * scale
            if bx > hit:
                over = min(1.0, (bx - hit) / (140 * scale))
                bx = hit - 150 * scale * math.sin(over * math.pi) ** 0.7
        for k in range(5, 0, -1):                     # trail
            ctx.set_source_rgba(*config.FAIL, 0.06 * k)
            ctx.arc(bx - k * 30 * scale, by, ball_r - k * 5.0 * scale, 0, math.tau)
            ctx.fill()
        # It only glows where it is getting through, which is the whole point of the frame.
        through = gap and abs(bx - (x0 + missing * step)) < step * 1.2
        sketch.glow(ctx, bx, by, 165 * scale, config.FAIL, 0.34 if through else 0.14)
        ctx.set_source_rgba(*config.FAIL, 0.96)
        ctx.arc(bx, by, ball_r, 0, math.tau)
        ctx.fill()

    for yy in (top, bottom):                          # frame
        sketch.line(ctx, x0 - 30 * scale, yy, x0 + span + 30 * scale, yy,
                    sketch.Pen(color=config.INK, width=config.STROKE * 1.6),
                    progress=min(1.0, p1 * 1.6))
    for i in range(n):
        if i == missing:
            continue
        local = max(0.0, min(1.0, p1 * n - i))
        if local <= 0:
            continue
        sketch.line(ctx, x0 + i * step, top, x0 + i * step, bottom,
                    sketch.Pen(color=config.INK, width=config.STROKE * 1.35),
                    progress=local)
    if progress < 0.55:
        return

    gx = x0 + missing * step if gap else cx
    if gap:
        # Stubs where the bar was snapped off, so the hole reads as damage not design.
        for yy, sign in ((top, 1), (bottom, -1)):
            sketch.line(ctx, gx, yy, gx + 9 * scale, yy + sign * 34 * scale,
                        sketch.Pen(color=config.FAIL, width=config.STROKE * 1.35),
                        progress=q)
        sketch.text(ctx, "removed", gx, top - 34 * scale, config.SZ_ANNOT,
                    config.FAIL, config.FONT_SANS, align="center", progress=q)
    if label:
        sketch.text(ctx, label, cx, bottom + 84 * scale, config.SZ_ANNOT,
                    config.MUTED, config.FONT_SANS, align="center", progress=q)


# ------------------------------------------------------------------ backtrack
def backtrack(ctx: cairo.Context, cx: float, cy: float, text: str, *,
              scale: float = 1.0, t: float = 0.0, rate: float = 7.0,
              target: int = 0, progress: float = 1.0) -> int:
    """The hero animation: an engine trying every way to split a string, and failing.

    The pattern is `.*.*=.*` — "anything, then anything, then an equals sign, then
    anything". Two adjacent wildcards means there is no single way to do it, so the engine
    enumerates every division of the string and backtracks out of each one that fails. Each
    frame here draws ONE attempt: the span the first wildcard has claimed, the span the
    second has claimed, and the character it is testing for an equals sign.

    Returns the attempt number currently displayed, so the caller can label it.

    This is the scene that has to survive being on screen for fifteen seconds, and it does,
    because it is still enumerating at second fifteen.
    """
    chars = list(text)
    L = len(chars)
    # Sized to fill the measure rather than to a fixed cell: a nine-character string at 76px
    # a cell owns 36% of the frame, which is the "small object floating in a dark frame"
    # failure HOUSE_STYLE §8 names.
    cw = min(212.0 * scale, (config.W - config.SAFE * 2) * 0.86 / max(1, L))
    ch = cw * 1.18
    total = L * cw
    x0 = round(cx - total / 2)

    # Cells first, drawn on.
    p1 = min(1.0, progress / 0.4)
    shown = max(0, min(L, int(round(p1 * L + 0.001))))
    for i in range(shown):
        x = x0 + i * cw
        sketch.rect(ctx, x + 5, cy - ch / 2, cw - 10, ch,
                    sketch.Pen(color=config.MUTED, width=2.6),
                    fill=config.BG_DEEP, fill_alpha=0.55, overshoot=3)
        sketch.text(ctx, chars[i], x + cw / 2, cy + ch * 0.26, ch * 0.62,
                    config.INK, config.FONT_MONO, align="center", bold=True)
    if progress < 0.4:
        return 0

    # Greedy enumeration, in the order PCRE actually walks it: first wildcard takes as much
    # as it can, then gives a character back, and the second wildcard sweeps under it.
    attempts: list[tuple[int, int]] = []
    for a in range(L, -1, -1):
        for b in range(L - a, -1, -1):
            attempts.append((a, b))
    n = len(attempts)

    # The counter and the picture run on separate clocks, deliberately. Above about nine
    # attempts a second the spans are a blur and the viewer learns nothing from them, but
    # the whole point of the beat is that the count is running away. So the count races at
    # `rate` and the illustration walks the same enumeration at a speed a person can
    # follow. It is a diagram of the process, not a simulator of it.
    # A counter that climbs must accelerate (HOUSE_STYLE §10). The subject of the beat is
    # that the cost EXPLODES, and EP02's constant-rate count argued against its own point
    # for two minutes. Pace the count off the value, not the clock: readable while the
    # numbers are small, racing once they pass a few hundred. The landing time is unchanged
    # — `rate` still encodes where the old linear count would have finished, so the scene
    # caps at the same moment and the caption logic downstream is untouched.
    elapsed = max(0.0, t - 0.4)
    if target > 0:
        span = target / max(rate, 1e-6)
        s = min(1.0, elapsed / max(span, 1e-6))
        # Curvature scales with the size of the number: a 23-step count stays close to
        # linear and every step is legible, while a four-thousand-step count spends half
        # its beat in the readable hundreds and then runs away.
        K = 2.2 * max(0.0, math.log10(target) - 1.0)
        if K < 0.3:
            step = int(round(target * s))
        else:
            step = int(round(target * math.expm1(K * s) / math.expm1(K)))
    else:
        step = int(elapsed * rate)
    capped = target > 0 and step >= target
    shown_n = min(step, target) if target > 0 else step
    walk = int(elapsed * min(rate, 9.0))
    if capped:
        # Settle on the attempt that actually succeeds, if there is one. Freezing on
        # whatever state the walk happened to reach left the frame parked on two empty
        # spans for the rest of a thirty-second beat, which reads as the animation having
        # crashed rather than as the search having finished.
        win = next((i for i, (aa, bb) in enumerate(attempts)
                    if aa + bb < L and chars[aa + bb] == "="), n - 1)
        idx = win
    else:
        idx = walk % n            # loop rather than stall while the count is still running
    a, b = attempts[idx]

    # The two claimed spans, as bars under the cells, each labelled with what it is
    # claiming. The labels are what make this legible to someone who has never seen a
    # pattern language: two things both allowed to take "anything" is the entire bug.
    for (start, length, col, dy, name) in ((0, a, config.ACCENT, 42.0, "anything"),
                                           (a, b, config.INK, 118.0, "anything")):
        y = cy + ch / 2 + dy
        if length <= 0:
            # A wildcard matching zero characters still has to be visible or the animation
            # looks like it skipped a step.
            xm = x0 + start * cw
            sketch.line(ctx, xm - 9, y, xm + 9, y,
                        sketch.Pen(color=col, width=config.STROKE * 1.4, passes=1))
            sketch.text(ctx, "nothing", xm, y + 46, config.SZ_ANNOT * 0.8, col,
                        config.FONT_SANS, align="center")
            continue
        sketch.line(ctx, x0 + start * cw + 7, y, x0 + (start + length) * cw - 7, y,
                    sketch.Pen(color=col, width=config.STROKE * 2.2, passes=1))
        for e in (start, start + length):             # end caps, so a span has edges
            ex = x0 + e * cw + (7 if e == start else -7)
            sketch.line(ctx, ex, y - 14, ex, y + 14,
                        sketch.Pen(color=col, width=config.STROKE * 1.3, passes=1))
        sketch.text(ctx, name, x0 + (start + length / 2) * cw, y + 46,
                    config.SZ_ANNOT * 0.8, col, config.FONT_SANS, align="center")

    # The character being tested for the literal '=' — the whole reason for the backtrack.
    probe = a + b
    hit = probe < L and chars[probe] == "="
    if probe <= L:
        col = config.OK if hit else config.FAIL
        px = x0 + min(probe, L - 1) * cw + cw / 2 + (cw if probe >= L else 0)
        px = min(px, x0 + total + cw * 0.45)
        sketch.rect(ctx, px - cw / 2 + 5, cy - ch / 2 - 9, cw - 10, ch + 18,
                    sketch.Pen(color=col, width=config.STROKE * 1.4), overshoot=2)
        sketch.text(ctx, "=" if hit else "= ?", px, cy - ch / 2 - 34,
                    46 * scale, col, config.FONT_MONO, align="center", bold=True)

    # The counter. It does not move, so there is no pixel-grid question here — but its
    # digits change every frame, which is the whole reason this scene can hold for fifteen
    # seconds without going stale.
    sketch.text(ctx, f"{shown_n:,}", cx, cy - ch / 2 - 168, 118 * scale,
                config.FAIL if capped else config.INK, config.FONT_SANS,
                align="center", bold=True)
    # The settled label has to agree with the settled picture. Saying "it has not found an
    # answer yet" under a green matched cell is a frame arguing with itself, and x=x does
    # find its answer — at the twenty-third attempt, which is the point of the beat.
    if capped:
        note = ("attempts, to match one short string" if "=" in chars
                else "attempts, to find out that nothing matched")
    else:
        note = "attempts so far"
    sketch.text(ctx, note, cx, cy - ch / 2 - 112, config.SZ_ANNOT, config.MUTED,
                config.FONT_SANS, align="center")
    return shown_n


# ---------------------------------------------------------------------- door
def door(ctx: cairo.Context, cx: float, cy: float, *, scale: float = 1.0,
         locked: bool = True, t: float = 0.0, label: str = "",
         progress: float = 1.0) -> tuple[float, float]:
    """A door with a badge reader that will not open. Returns the floor point to stand on.

    For "we could not get into our own systems". The reader's LED is on a cycle so the
    refusal keeps happening, rather than happening once and then being a still life.
    """
    w, h = 350 * scale, 700 * scale
    x, y = cx - w / 2, cy - h / 2
    pen = sketch.Pen(color=config.INK, width=config.STROKE * 1.4)
    # Reader panel goes on the APPROACH side, i.e. the side the figure walks in from. The
    # first cut put it on the far side of the door, so the person was reaching for a door
    # while the thing refusing them sat behind it, out of the story.
    rw, rh = 104 * scale, 168 * scale
    rx, ry = x - rw - 54 * scale, cy - 110 * scale
    stand = (rx - 190 * scale, y + h)

    sketch.rect(ctx, x, y, w, h, pen, fill=config.BG_DEEP, fill_alpha=0.55,
                overshoot=5, progress=min(1.0, progress / 0.45))
    if progress < 0.45:
        return stand

    p2 = min(1.0, (progress - 0.45) / 0.3)
    sketch.rect(ctx, x + 30 * scale, y + 46 * scale, w - 60 * scale, h * 0.34,
                sketch.Pen(color=config.MUTED, width=2.4), overshoot=3, progress=p2)
    sketch.ellipse(ctx, x + w - 48 * scale, cy + 46 * scale, 14 * scale, 14 * scale,
                   sketch.Pen(color=config.MUTED, width=2.8), progress=p2)

    sketch.rect(ctx, rx, ry, rw, rh, sketch.Pen(color=config.MUTED, width=2.8),
                fill=config.BG_DEEP, fill_alpha=0.8, overshoot=3, progress=p2)
    if progress < 0.75:
        return stand

    beat = (t % 2.2) / 2.2
    on = locked and beat > 0.55 and (int(t * 8) % 2 == 0 or beat > 0.72)
    col = config.FAIL if locked else config.OK
    sketch.ellipse(ctx, rx + rw / 2, ry + rh * 0.30, 22 * scale, 22 * scale,
                   sketch.Pen(color=col, width=2.6), fill=col,
                   fill_alpha=0.95 if on else 0.18)
    if on:
        sketch.glow(ctx, rx + rw / 2, ry + rh * 0.30, 150 * scale, config.FAIL, 0.34)
        sketch.text(ctx, "DENIED", rx + rw / 2, ry + rh + 56 * scale, 36 * scale,
                    config.FAIL, config.FONT_SANS, align="center", bold=True)
    if label:
        sketch.text(ctx, label, cx, y + h + 74 * scale, config.SZ_ANNOT,
                    config.MUTED, config.FONT_SANS, align="center",
                    progress=min(1.0, max(0.0, (progress - 0.75) / 0.25)))
    return stand


# ==================================================================== EP04 set
# Two sites and one pen: the pictures that carry a split-brain story. Both DEPICT — a
# building you could point at, a book being written in — never a boxes-and-arrows
# abstraction of one. (The abstraction-only medium is what killed a sister channel; see
# the memory note "depicted subjects, not diagrams of them".)


def ladder(ctx: cairo.Context, x: float, gy: float, *, h: float = 320.0,
           lean: float = -160.0, color: Color = config.MUTED,
           progress: float = 1.0) -> None:
    """A ladder leaning against something, feet at (x, gy). `lean` is the top's x offset."""
    pen = sketch.Pen(color=color, width=config.STROKE * 0.95)
    gap = 58.0
    for dx in (0.0, gap):
        sketch.line(ctx, x + dx, gy, x + dx + lean, gy - h, pen, progress=progress)
    rungs = 6
    for i in range(1, rungs + 1):
        u = i / (rungs + 1)
        if progress < u:
            break
        sketch.line(ctx, x + lean * u, gy - h * u, x + gap + lean * u, gy - h * u, pen)


def toolbox(ctx: cairo.Context, cx: float, gy: float, *, scale: float = 1.0,
            progress: float = 1.0) -> None:
    """A workman's toolbox sitting on the ground."""
    w, h = 96 * scale, 52 * scale
    pen = sketch.Pen(color=config.MUTED, width=config.STROKE * 0.9)
    sketch.rect(ctx, cx - w / 2, gy - h, w, h, pen, fill=config.BG_DEEP, fill_alpha=0.75,
                overshoot=2.5, progress=progress)
    if progress > 0.6:
        ctx.save()
        ctx.set_source_rgba(*config.MUTED, 0.9)
        ctx.set_line_width(config.STROKE * 0.9)
        ctx.arc(cx, gy - h, w * 0.22, math.pi, math.tau)
        ctx.stroke()
        ctx.restore()
        sketch.line(ctx, cx - w / 2, gy - h * 0.55, cx + w / 2, gy - h * 0.55,
                    sketch.Pen(color=config.MUTED, width=2.0, alpha=0.7, passes=1))


def quill(ctx: cairo.Context, x: float, y: float, scale: float = 1.0, *,
          alpha: float = 1.0) -> None:
    """A pen drawn for the dark ground. sketch.pen_nib fills in near-blacks that belonged
    to the paper direction — on #0E1013 it disappears, and the pen is the story here."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(scale, scale)
    ctx.rotate(-0.62)
    ctx.set_source_rgba(*config.INK, 0.95 * alpha)
    ctx.move_to(0, 0)                 # nib
    ctx.line_to(-8, -20)
    ctx.line_to(8, -20)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgba(*config.INK, 0.85 * alpha)
    ctx.rectangle(-8, -20, 16, 70)    # barrel
    ctx.fill()
    ctx.set_source_rgba(*config.ACCENT, 0.95 * alpha)
    ctx.rectangle(-8, -20, 16, 11)    # band
    ctx.fill()
    ctx.restore()


def datacenter(ctx: cairo.Context, cx: float, cy: float, *, scale: float = 1.0,
               label: str = "", dead: bool = False, t: float = 0.0,
               progress: float = 1.0) -> tuple[float, float]:
    """A data centre drawn as a building: antenna mast, window grid, door.

    Alive, its windows flicker gently and the beacon breathes — so a long hold still has
    life in it. `dead` turns the windows dark and the beacon red: unreachable, at a glance.
    Returns (roof_x, roof_y) of the mast tip, so a scene can hang things above it.
    """
    w, h = 350 * scale, 460 * scale
    x, y = cx - w / 2, cy - h / 2
    col = config.FAIL if dead else config.INK
    pen = sketch.Pen(color=col, width=config.STROKE * (1.5 if dead else 1.25))

    sketch.rect(ctx, x, y, w, h, pen, fill=config.BG_DEEP, fill_alpha=0.55,
                overshoot=6 * scale, progress=min(1.0, progress / 0.4))
    mast_x, mast_top = cx, y - 84 * scale
    if progress < 0.4:
        return mast_x, mast_top

    # Window grid, landing floor by floor. Lit windows flicker on a slow deterministic
    # clock, an entire floor never blinks in unison, and a dead building goes dark.
    p2 = min(1.0, (progress - 0.4) / 0.4)
    cols_n, rows_n = 3, 5
    ww, wh = w * 0.180, h * 0.104
    gx, gy = (w - cols_n * ww) / (cols_n + 1), (h * 0.78 - rows_n * wh) / (rows_n + 1)
    shown = int(round(p2 * rows_n * cols_n + 0.001))
    for i in range(shown):
        r, c = i // cols_n, i % cols_n
        wx = x + gx + c * (ww + gx)
        wy = y + gy + r * (wh + gy)
        tick = int(t * 2.1)
        lit = (not dead) and sketch._noise(i * 131 + tick * 17, 5) > -0.25
        sketch.rect(ctx, wx, wy, ww, wh,
                    sketch.Pen(color=config.MUTED, width=2.2, alpha=0.8),
                    fill=config.ACCENT if lit else config.BG,
                    fill_alpha=0.34 + 0.10 * sketch._noise(i * 7 + tick * 3, 9)
                    if lit else 0.85)
    if progress < 0.8:
        return mast_x, mast_top

    # Door, mast and beacon last: the roofline is what makes it a building.
    p3 = min(1.0, (progress - 0.8) / 0.2)
    dw, dh = w * 0.16, h * 0.13
    sketch.rect(ctx, cx - dw / 2, y + h - dh, dw, dh,
                sketch.Pen(color=config.MUTED, width=2.6), progress=p3)
    sketch.line(ctx, mast_x, y, mast_x, mast_top + 26 * scale, pen, progress=p3)
    if p3 >= 1.0:
        beat = 0.30 + 0.55 * abs(math.sin(t * 2.3))
        bcol = config.FAIL if dead else config.OK
        sketch.ellipse(ctx, mast_x, mast_top + 14 * scale, 11 * scale, 11 * scale,
                       sketch.Pen(color=bcol, width=2.6), fill=bcol,
                       fill_alpha=0.9 if dead else beat)
        if dead:
            sketch.glow(ctx, mast_x, mast_top + 14 * scale, 120 * scale,
                        config.FAIL, 0.28)
    if label:
        sketch.text(ctx, label, cx, y + h + 72 * scale, config.SZ_ANNOT,
                    config.MUTED, config.FONT_SANS, align="center", progress=p3)
    return mast_x, mast_top


def ledger(ctx: cairo.Context, cx: float, cy: float, *, scale: float = 1.0,
           written: float = 0.0, color: Color = config.INK, label: str = "",
           nib: bool = True, t: float = 0.0, progress: float = 1.0) -> None:
    """An open ledger page taking handwriting, one entry at a time.

    `written` is how many entry strokes have landed; a fractional part draws the current
    stroke mid-write, with the pen nib riding its tip. Once writing stops (written frozen),
    the nib is gone — a page nobody is allowed to write in any more. Capacity is two
    columns of 13; feed it counts below that.
    """
    w, h = 560 * scale, 620 * scale
    x, y = cx - w / 2, cy - h / 2
    pen = sketch.Pen(color=config.INK, width=config.STROKE * 1.2)
    sketch.rect(ctx, x, y, w, h, pen, fill=config.BG_DEEP, fill_alpha=0.45,
                overshoot=5 * scale, progress=min(1.0, progress / 0.45))
    if progress < 0.45:
        return

    p2 = min(1.0, (progress - 0.45) / 0.35)
    # Ledger dressing: a red margin rule per column and feint lines to write on.
    rows_n, cols_n = 13, 2
    pad = 46 * scale
    col_w = (w - pad * 2) / cols_n
    lh = (h - pad * 2.4) / rows_n
    for c in range(cols_n):
        mx = x + pad + c * col_w
        sketch.line(ctx, mx - 14 * scale, y + pad * 0.7, mx - 14 * scale, y + h - pad * 0.7,
                    sketch.Pen(color=config.FAIL, width=2.2, alpha=0.35, passes=1),
                    progress=p2)
        for r in range(rows_n):
            ly = y + pad * 1.2 + (r + 1) * lh
            sketch.line(ctx, mx, ly, mx + col_w - 30 * scale, ly,
                        sketch.Pen(color=config.MUTED, width=1.6, alpha=0.22, passes=1),
                        progress=p2)
    if progress < 0.8 or written <= 0:
        if label:
            sketch.text(ctx, label, cx, y + h + 70 * scale, config.SZ_ANNOT,
                        config.MUTED, config.FONT_SANS, align="center", progress=p2)
        return

    # The entries. Each is a wavering stroke sitting on its feint line, length varied so
    # the page reads as handwriting rather than a bar chart.
    total = min(written, float(rows_n * cols_n))
    full = int(total)
    frac = total - full
    tip_x = tip_y = None
    for i in range(full + (1 if frac > 0 else 0)):
        c, r = i // rows_n, i % rows_n
        mx = x + pad + c * col_w
        ly = y + pad * 1.2 + (r + 1) * lh - lh * 0.22
        ln = col_w * (0.52 + 0.38 * abs(sketch._noise(i * 379, 4)))
        seg = 1.0 if i < full else frac
        sketch.line(ctx, mx + 6 * scale, ly, mx + 6 * scale + ln * seg, ly,
                    sketch.Pen(color=color, width=config.STROKE * 0.9, alpha=0.9),
                    progress=1.0)
        tip_x, tip_y = mx + 6 * scale + ln * seg, ly
    if nib and tip_x is not None:
        bob = 3.0 * math.sin(t * 2.9) if frac == 0 else 0.0
        quill(ctx, tip_x + 4 * scale, tip_y + bob, scale=1.15 * scale)
    if label:
        sketch.text(ctx, label, cx, y + h + 70 * scale, config.SZ_ANNOT,
                    config.MUTED, config.FONT_SANS, align="center", progress=p2)
