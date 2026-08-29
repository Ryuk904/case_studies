"""An articulated stick figure with keyframed poses.

Built in-house rather than pulled from an animation tool for three reasons: it inherits the
episode's palette so figures never look pasted on, poses are data so a beat can be described
in the script rather than drawn, and the whole thing stays byte-reproducible like the rest of
the render.

The rig is a skeleton, not a sprite. Every segment angle is a number in a pose dict, poses
interpolate, and a cycle is a list of (pose, seconds). That is what makes a walk a walk
instead of two alternating drawings.

Angles are DEGREES measured clockwise from straight down, because limbs hang. 0 is down,
+90 points to the figure's front (screen right), -90 to its back. `lean` is the torso,
measured from straight up on the same convention.

    draw(ctx, 900, 700, scale=2.0, pose="carry")
    draw(ctx, 900, 700, scale=2.0, pose=cycle(WALK, t))
"""

from __future__ import annotations

import math

import cairo

from . import config, sketch

Color = tuple[float, float, float]

# Proportions in rig units. One unit = one pixel at scale 1.0; a figure is ~224 tall.
HEAD_R, NECK, TORSO = 22.0, 10.0, 78.0
SHOULDER, HIP_W = 25.0, 18.0
UPPER_ARM, FOREARM = 46.0, 44.0
THIGH, SHIN = 52.0, 50.0

# Angles are absolute, not mirrored per side, because locomotion needs both limbs swinging
# in the SAME plane (fore/aft). The cost is that front-facing poses must spell out their own
# symmetry: the left side wants negative angles to open outward. Getting that backwards is
# what made the first pass stand with its legs crossed and its arms hidden behind its torso.
_ZERO = dict(lean=0.0, head=0.0,
             arm_l_up=-11.0, arm_l_lo=-5.0, arm_r_up=11.0, arm_r_lo=5.0,
             leg_l_up=-5.0, leg_l_lo=2.0, leg_r_up=5.0, leg_r_lo=-2.0)


def _pose(**kw: float) -> dict[str, float]:
    p = dict(_ZERO)
    p.update(kw)
    return p


POSES: dict[str, dict[str, float]] = {
    "idle":   _pose(),
    "stand":  _pose(arm_l_up=-16, arm_l_lo=-9, arm_r_up=16, arm_r_lo=9),

    # Walk and run are two-frame cycles; cycle() eases between them and back.
    "walk_a": _pose(arm_l_up=-30, arm_l_lo=-18, arm_r_up=32, arm_r_lo=22,
                    leg_l_up=30, leg_l_lo=-24, leg_r_up=-26, leg_r_lo=8),
    "walk_b": _pose(arm_l_up=32, arm_l_lo=22, arm_r_up=-30, arm_r_lo=-18,
                    leg_l_up=-26, leg_l_lo=8, leg_r_up=30, leg_r_lo=-24),
    "run_a":  _pose(lean=14, arm_l_up=-64, arm_l_lo=-78, arm_r_up=58, arm_r_lo=-70,
                    leg_l_up=54, leg_l_lo=-58, leg_r_up=-42, leg_r_lo=44),
    "run_b":  _pose(lean=14, arm_l_up=58, arm_l_lo=-70, arm_r_up=-64, arm_r_lo=-78,
                    leg_l_up=-42, leg_l_lo=44, leg_r_up=54, leg_r_lo=-58),

    # Working postures.
    "type":   _pose(lean=8, head=10, arm_l_up=52, arm_l_lo=38, arm_r_up=58, arm_r_lo=34),
    "carry":  _pose(lean=-5, arm_l_up=58, arm_l_lo=30, arm_r_up=64, arm_r_lo=26),
    "reach":  _pose(arm_l_up=10, arm_l_lo=6, arm_r_up=96, arm_r_lo=8),
    "point":  _pose(arm_l_up=12, arm_l_lo=8, arm_r_up=78, arm_r_lo=0),

    # Reactions.
    "shrug":  _pose(arm_l_up=-52, arm_l_lo=-96, arm_r_up=52, arm_r_lo=96, head=-6),
    "panic":  _pose(arm_l_up=-150, arm_l_lo=-24, arm_r_up=150, arm_r_lo=24, head=-14),
    "slump":  _pose(lean=16, head=26, arm_l_up=-9, arm_l_lo=-14, arm_r_up=9, arm_r_lo=14),
    "sit":    _pose(leg_l_up=84, leg_l_lo=-86, leg_r_up=80, leg_r_lo=-84,
                    arm_l_up=44, arm_l_lo=30, arm_r_up=48, arm_r_lo=28),

    # Cycle keyframes. These exist only as endpoints for the cycles below and are not
    # meant to be used as a still pose — "type_a" alone is a person with one hand up.
    # Elbows down and forearms forward, not both arms straight out: the first pass had the
    # arms level and reading as a push. The two frames alternate the wrists by 20 degrees so
    # hands visibly take turns rather than both hovering.
    "type_a": _pose(lean=10, head=16, arm_l_up=34, arm_l_lo=64, arm_r_up=38, arm_r_lo=44),
    "type_b": _pose(lean=10, head=16, arm_l_up=34, arm_l_lo=44, arm_r_up=38, arm_r_lo=64),
    "panic_a": _pose(arm_l_up=-158, arm_l_lo=-16, arm_r_up=132, arm_r_lo=40, head=-16),
    "panic_b": _pose(arm_l_up=-132, arm_l_lo=-40, arm_r_up=158, arm_r_lo=16, head=-10),
    "wave_a": _pose(arm_l_up=-14, arm_l_lo=-8, arm_r_up=142, arm_r_lo=26),
    "wave_b": _pose(arm_l_up=-14, arm_l_lo=-8, arm_r_up=160, arm_r_lo=-14),
    "look_a": _pose(head=-16, arm_l_up=-20, arm_l_lo=-12, arm_r_up=20, arm_r_lo=12),
    "look_b": _pose(head=16, arm_l_up=-20, arm_l_lo=-12, arm_r_up=20, arm_r_lo=12),

    # Working a door / a panel: hand out at chest height, then pressed forward.
    "badge_a": _pose(arm_l_up=-12, arm_l_lo=-6, arm_r_up=74, arm_r_lo=18),
    "badge_b": _pose(arm_l_up=-12, arm_l_lo=-6, arm_r_up=92, arm_r_lo=2, lean=4),
}

WALK = [("walk_a", 0.34), ("walk_b", 0.34)]
RUN = [("run_a", 0.20), ("run_b", 0.20)]
IDLE_BREATH = [("idle", 1.6), ("stand", 1.6)]

# EP01 shipped four static poses and never called cycle() once, which is why every figure in
# it is a statue. These are the cycles a technical incident actually needs: someone working,
# someone reacting, someone looking around a room for an answer, someone trying a door.
TYPING = [("type_a", 0.22), ("type_b", 0.22)]
PANICKING = [("panic_a", 0.26), ("panic_b", 0.26)]
WAVING = [("wave_a", 0.34), ("wave_b", 0.34)]
LOOKING = [("look_a", 1.10), ("look_b", 1.10)]
BADGING = [("badge_a", 0.55), ("badge_b", 0.55)]

CYCLES: dict[str, list[tuple[str, float]]] = {
    "walk": WALK, "run": RUN, "idle": IDLE_BREATH, "type": TYPING,
    "panic": PANICKING, "wave": WAVING, "look": LOOKING, "badge": BADGING,
}


def animate(name: str, t: float) -> str | dict[str, float]:
    """Pose at time `t` for a cycle name, or the static pose if it is not a cycle.

    One lookup so a scene can take `pose="walk"` or `pose="slump"` from the script and not
    care which kind it got.
    """
    frames = CYCLES.get(name)
    return cycle(frames, t) if frames else name


def enter(name: str, t: float, *, from_pose: str = "idle", secs: float = 0.5
          ) -> dict[str, float]:
    """Ease into a cycle (or a pose) from another pose over `secs`.

    Cutting straight into a cycle mid-stride is the tell that a rig is being puppeted rather
    than acted. blend() exists for exactly this and EP01 never used it.
    """
    target = resolve(animate(name, t))
    if t >= secs or secs <= 0:
        return target
    return blend(resolve(from_pose), target, _ease(max(0.0, t) / secs))


def blend(a: dict[str, float], b: dict[str, float], t: float) -> dict[str, float]:
    t = max(0.0, min(1.0, t))
    return {k: a[k] + (b[k] - a[k]) * t for k in a}


def _ease(t: float) -> float:
    return t * t * (3 - 2 * t)          # smoothstep, so cycles do not tick


def cycle(frames: list[tuple[str, float]], t: float) -> dict[str, float]:
    """Pose at time `t` seconds through a looping list of (pose name, seconds)."""
    total = sum(d for _, d in frames)
    if total <= 0:
        return POSES[frames[0][0]]
    u = t % total
    for i, (name, dur) in enumerate(frames):
        if u < dur:
            nxt = frames[(i + 1) % len(frames)][0]
            return blend(POSES[name], POSES[nxt], _ease(u / dur))
        u -= dur
    return POSES[frames[-1][0]]


def resolve(pose: str | dict[str, float]) -> dict[str, float]:
    return POSES.get(pose, POSES["idle"]) if isinstance(pose, str) else pose


def _tip(x: float, y: float, ang_deg: float, length: float,
         flip: bool) -> tuple[float, float]:
    """End of a segment starting at (x, y). 0deg is straight down."""
    a = math.radians(ang_deg if not flip else -ang_deg)
    return x + math.sin(a) * length, y + math.cos(a) * length


def joints(x: float, y: float, scale: float, pose: dict[str, float],
           flip: bool = False) -> dict[str, tuple[float, float]]:
    """Every joint position for a figure whose FEET are at (x, y).

    Exposed because scenes need to attach things to hands — a box, a cable, a switch — and
    guessing where a hand is defeats the point of having a skeleton.
    """
    s = scale
    foot_y = y
    hip = (x, foot_y - (THIGH + SHIN) * s)
    lean = pose["lean"]
    neck = _tip(hip[0], hip[1], 180 - lean, TORSO * s, flip)
    head_c = _tip(neck[0], neck[1], 180 - lean - pose["head"], (NECK + HEAD_R) * s, flip)

    out = {"hip": hip, "neck": neck, "head": head_c}
    for side, sign in (("l", -1), ("r", 1)):
        sh = (neck[0] + sign * SHOULDER * s * (-1 if flip else 1), neck[1] + 6 * s)
        el = _tip(*sh, pose[f"arm_{side}_up"], UPPER_ARM * s, flip)
        hd = _tip(*el, pose[f"arm_{side}_up"] + pose[f"arm_{side}_lo"], FOREARM * s, flip)
        out[f"sh_{side}"], out[f"el_{side}"], out[f"hand_{side}"] = sh, el, hd

        hp = (hip[0] + sign * HIP_W * s * (-1 if flip else 1), hip[1])
        kn = _tip(*hp, pose[f"leg_{side}_up"], THIGH * s, flip)
        ft = _tip(*kn, pose[f"leg_{side}_up"] + pose[f"leg_{side}_lo"], SHIN * s, flip)
        out[f"hip_{side}"], out[f"knee_{side}"], out[f"foot_{side}"] = hp, kn, ft
    return out


def draw(ctx: cairo.Context, x: float, y: float, *, scale: float = 1.0,
         pose: str | dict[str, float] = "idle", color: Color = config.INK,
         width: float | None = None, flip: bool = False, alpha: float = 1.0,
         progress: float = 1.0) -> dict[str, tuple[float, float]]:
    """Draw a figure standing with its feet at (x, y). Returns its joint positions."""
    if progress <= 0.0:
        return {}
    p = resolve(pose)
    j = joints(x, y, scale, p, flip)
    lw = width if width is not None else max(3.0, 7.0 * scale)

    ctx.save()
    ctx.set_source_rgba(*color, alpha)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    # Back limbs first so the figure has a front and a back.
    order = [("sh_l", "el_l", "hand_l"), ("hip_l", "knee_l", "foot_l"),
             ("hip", "neck", None),
             ("sh_r", "el_r", "hand_r"), ("hip_r", "knee_r", "foot_r")]
    limbs = [seg for seg in order]
    shown = max(1, int(len(limbs) * progress + 0.001))
    for a, b, c in limbs[:shown]:
        ctx.move_to(*j[a])
        ctx.line_to(*j[b])
        if c:
            ctx.line_to(*j[c])
        ctx.stroke()
    # Shoulders and pelvis, so the torso reads as a body rather than a pole.
    ctx.move_to(*j["sh_l"]); ctx.line_to(*j["sh_r"]); ctx.stroke()
    ctx.move_to(*j["hip_l"]); ctx.line_to(*j["hip_r"]); ctx.stroke()

    ctx.arc(j["head"][0], j["head"][1], HEAD_R * scale, 0, math.tau)
    ctx.fill()
    ctx.restore()
    return j


def box(ctx: cairo.Context, j: dict[str, tuple[float, float]], scale: float = 1.0,
        color: Color = config.ACCENT, label: str = "") -> None:
    """A carried crate, placed between the figure's hands. For the deploy beats."""
    if "hand_l" not in j:
        return
    (lx, ly), (rx, ry) = j["hand_l"], j["hand_r"]
    cx, cy = (lx + rx) / 2, (ly + ry) / 2
    w, h = 84 * scale, 62 * scale
    # Push the crate out along the arms, away from the torso. Centred on the hands alone it
    # sits inside the figure's chest and the label lands across its head.
    hip = j.get("hip", (cx, cy))
    dx, dy = cx - hip[0], cy - hip[1]
    norm = max(1e-6, math.hypot(dx, dy))
    cx += dx / norm * w * 0.55
    cy += dy / norm * h * 0.30
    ctx.save()
    ctx.set_source_rgba(*color, 0.22)
    ctx.rectangle(cx - w / 2, cy - h / 2, w, h)
    ctx.fill()
    ctx.set_source_rgb(*color)
    ctx.set_line_width(max(2.5, 4.0 * scale))
    ctx.rectangle(cx - w / 2, cy - h / 2, w, h)
    ctx.stroke()
    ctx.restore()
    if label:
        sketch.text(ctx, label, cx, cy + h / 2 + 34 * scale, 26 * scale,
                    color, config.FONT_SANS, align="center")


def desk(ctx: cairo.Context, j: dict[str, tuple[float, float]], scale: float = 1.0,
         color: Color = config.MUTED, label: str = "") -> None:
    """A desk and a screen under the figure's hands, for the typing cycle.

    A rig typing on nothing reads as a rig pushing something invisible, which is what the
    first render of this pose looked like. Giving the hands a surface is the whole fix.
    """
    if "hand_l" not in j:
        return
    (lx, ly), (rx, ry) = j["hand_l"], j["hand_r"]
    hy = (ly + ry) / 2 + 14 * scale
    hip = j.get("hip", (lx, ly))
    front = max(lx, rx) + 30 * scale
    top = min(lx, rx) - 10 * scale
    w = 210 * scale
    pen = sketch.Pen(color=color, width=max(2.5, 3.6 * scale))

    sketch.line(ctx, top - 40 * scale, hy, front + w * 0.30, hy, pen)   # desk edge
    # Keyboard: a shallow parallelogram under the hands.
    sketch.line(ctx, top - 10 * scale, hy - 4 * scale,
                front + 10 * scale, hy - 4 * scale,
                sketch.Pen(color=config.INK, width=max(3.0, 5.0 * scale)))
    # Screen, standing ON the desk edge — floating it 16px above read as a monitor hovering.
    sx = front + w * 0.06
    sw, sh = 122 * scale, 104 * scale
    sketch.rect(ctx, sx, hy - sh - 12 * scale, sw, sh,
                sketch.Pen(color=color, width=max(2.5, 3.4 * scale)),
                fill=config.BG_DEEP, fill_alpha=0.7, overshoot=3)
    sketch.line(ctx, sx + sw / 2, hy - 12 * scale, sx + sw / 2, hy, pen)   # stalk
    sketch.line(ctx, sx + sw * 0.28, hy, sx + sw * 0.72, hy, pen)          # foot
    if label:
        sketch.text(ctx, label, (top + front) / 2, hy + 58 * scale, 26 * scale,
                    color, config.FONT_SANS, align="center")
