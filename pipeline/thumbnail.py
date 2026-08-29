"""Thumbnail generator.

Same primitives as the video, so the thumbnail is unmistakably from the same channel.
1280x720 is what YouTube wants; it is displayed as small as 210x118, which is the size that
actually decides the click. Hence the constraints below: three words maximum, one accent
colour, one subject.

    python -m pipeline.thumbnail episodes/ep01_knight_capital --text "7 of 8"

Three modes, because the art can come from here or from an image model:

    --fit art.png                     crop any image to 1280x720
    --compose art.png --top "..." --bottom "..."
                                      crop, then lay the channel's own type over it
    <episode> --text "..."            draw the whole thing from sketch primitives

`--compose` exists because image models still mangle small text, and the words are the part
that has to survive being 170px wide in a phone feed. Let the model make the picture, set
the type here.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import cairo

from . import config, sketch

TW, TH = 1280, 720


def _surface() -> tuple[cairo.ImageSurface, cairo.Context]:
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, TW, TH)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    ctx.set_source_rgb(*config.BG)
    ctx.paint()
    return surf, ctx


# --------------------------------------------------------------------- art
# The right third of the frame. At 210px wide in a sidebar the text carries the click,
# but the art is what makes the channel recognisable across a row of thumbnails.
ART_X, ART_W = TW * 0.63, TW * 0.31
ART_CY = TH / 2


def art_servers(ctx: cairo.Context, n: int = 8, bad: int = 8) -> None:
    """n server boxes in a grid; the `bad`-th one drawn in the failure accent."""
    cols, rows = 2, (n + 1) // 2
    bw, bh = ART_W / cols - 26, 62.0
    x0 = ART_X + (ART_W - (bw * cols + 26)) / 2
    y0 = ART_CY - (bh * rows + 18 * (rows - 1)) / 2
    for i in range(n):
        c, r = i % cols, i // cols
        x, y = x0 + c * (bw + 26), y0 + r * (bh + 18)
        hot = (i + 1) == bad
        pen = sketch.Pen(color=config.FAIL, width=5) if hot else sketch.Pen(
            color=config.MUTED, width=3.4)
        sketch.rect(ctx, x, y, bw, bh, pen,
                    fill=config.FAIL if hot else None, fill_alpha=0.13)
        for k in range(3):     # drive-bay lines, so it reads as a machine
            sketch.line(ctx, x + 16, y + 18 + k * 14, x + bw - 16, y + 18 + k * 14,
                        sketch.Pen(color=config.FAIL if hot else config.MUTED,
                                   width=2.2, alpha=0.55, passes=1))


def art_drives(ctx: cairo.Context, n: int = 4) -> None:
    """n storage icons, each struck through — for the backups-all-failed shape."""
    bh = 92.0
    y0 = ART_CY - (bh * n + 16 * (n - 1)) / 2
    x, w = ART_X + 20, ART_W - 40
    for i in range(n):
        y = y0 + i * (bh + 16)
        sketch.rect(ctx, x, y, w, bh, sketch.Pen(color=config.MUTED, width=3.4))
        pen = sketch.Pen(color=config.FAIL, width=6)
        sketch.line(ctx, x + 22, y + 20, x + w - 22, y + bh - 20, pen)
        sketch.line(ctx, x + w - 22, y + 20, x + 22, y + bh - 20, pen)


def art_gauge(ctx: cairo.Context) -> None:
    """A dial pegged at maximum — for CPU-saturation stories."""
    import math
    cx, cy, r = ART_X + ART_W / 2, ART_CY + 40, ART_W * 0.42
    for i in range(41):
        a = math.pi + i / 40 * math.pi
        hot = i > 32
        pen = sketch.Pen(color=config.FAIL if hot else config.MUTED,
                         width=6 if hot else 4, passes=1)
        sketch.line(ctx, cx + math.cos(a) * r, cy + math.sin(a) * r,
                    cx + math.cos(a) * (r - (26 if hot else 18)),
                    cy + math.sin(a) * (r - (26 if hot else 18)), pen)
    a = math.pi + 0.96 * math.pi
    sketch.line(ctx, cx, cy, cx + math.cos(a) * r * 0.86, cy + math.sin(a) * r * 0.86,
                sketch.Pen(color=config.FAIL, width=8))
    sketch.ellipse(ctx, cx, cy, 13, 13, sketch.Pen(color=config.INK), fill=config.INK)


def art_spike(ctx: cairo.Context) -> None:
    """A latency curve leaving the top of the frame — for degradation stories."""
    x0, x1 = ART_X, ART_X + ART_W
    base = ART_CY + 150
    sketch.line(ctx, x0, base, x1, base, sketch.Pen(color=config.MUTED, width=3))
    pts = []
    for i in range(41):
        t = i / 40
        y = base - (18 + 330 * (t ** 5))
        pts.append((x0 + (x1 - x0) * t, y))
    for i in range(len(pts) - 1):
        hot = i > 26
        sketch.line(ctx, *pts[i], *pts[i + 1],
                    sketch.Pen(color=config.FAIL if hot else config.INK,
                               width=7 if hot else 5, passes=1))


ART = {"servers": art_servers, "drives": art_drives, "gauge": art_gauge, "spike": art_spike}


def render(text: str, subject: str = "", art: str = "", accent: bool = True) -> cairo.ImageSurface:
    """text: max 3 words, huge. subject: small supporting line. art: key from ART."""
    surf, ctx = _surface()

    words = text.split()
    if len(words) > 3:
        print(f"  WARN thumbnail text is {len(words)} words; HOUSE_STYLE says max 3")

    if art:
        if art not in ART:
            raise KeyError(f"unknown art {art!r}; known: {', '.join(sorted(ART))}")
        ART[art](ctx)

    # Text block. Narrower when art occupies the right third.
    max_w = (TW * 0.55) if art else (TW * 0.78)
    size = 200.0
    lines = sketch.wrap_balanced(ctx, text.upper(), size, max_w, config.FONT_SANS, bold=True)
    while True:
        widest = max(sketch.text_size(ctx, ln, size, config.FONT_SANS, bold=True)[0]
                     for ln in lines)
        if widest <= max_w and size * 1.15 * len(lines) <= TH * 0.66:
            break
        size *= 0.94
        lines = sketch.wrap_balanced(ctx, text.upper(), size, max_w, config.FONT_SANS, bold=True)

    lh = size * 1.12
    y0 = TH / 2 - (len(lines) - 1) * lh / 2 + size * 0.34
    x = 70.0

    for i, ln in enumerate(lines):
        w, h = sketch.text_size(ctx, ln, size, config.FONT_SANS, bold=True)
        if accent and i == len(lines) - 1:
            # Sit the marker across the lower two-thirds of the glyphs, the way a real
            # highlighter lands. Anchored at the top it reads as a misaligned box.
            sketch.wash(ctx, x - 12, y0 + i * lh - h * 0.78, w + 24, h * 0.72)
        sketch.text(ctx, ln, x, y0 + i * lh, size, config.INK,
                    config.FONT_SANS, bold=True)

    if subject:
        sketch.text(ctx, subject.upper(), x, TH - 62, 34, config.MUTED, config.FONT_SANS)

    # Channel mark, and a single accent rule so the frame reads as a set.
    sketch.line(ctx, x, 58, x + 190, 58, sketch.Pen(color=config.FAIL, width=7))
    sketch.text(ctx, config.CHANNEL, x, 116, 34, config.MUTED, config.FONT_SANS)
    return surf


# ------------------------------------------------------- externally supplied art
def fit(src: Path) -> cairo.ImageSurface:
    """Any image, any format or aspect, scaled to cover 1280x720 and centre-cropped.

    Image models hand back 3:2 or square; YouTube wants 16:9. Cropping beats letterboxing
    because black bars read as an amateur upload at feed size.

    Pillow does the decoding, since it handles webp and jpg that cairo cannot, and the
    handover is via a temp PNG rather than a raw buffer: cairo's ARGB32 is premultiplied
    and native-endian, and getting that wrong fails as subtly wrong colours rather than a
    crash. A single extra file write on a one-off thumbnail is not worth that risk.
    """
    from PIL import Image

    with Image.open(src) as im:
        im = im.convert("RGB")
        scale = max(TW / im.width, TH / im.height)
        nw, nh = round(im.width * scale), round(im.height * scale)
        im = im.resize((nw, nh), Image.LANCZOS)
        im = im.crop(((nw - TW) // 2, (nh - TH) // 2,
                      (nw - TW) // 2 + TW, (nh - TH) // 2 + TH))
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as fh:
            tmp = Path(fh.name)
        im.save(tmp)
    try:
        return cairo.ImageSurface.create_from_png(str(tmp))
    finally:
        tmp.unlink(missing_ok=True)


def compose(src: Path, top: str, bottom: str = "", side: str = "right") -> cairo.ImageSurface:
    """Lay the channel's type over externally generated art."""
    surf = fit(src)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)

    left = side == "left"
    x0 = 64.0 if left else TW * 0.42
    x1 = TW * 0.58 if left else TW - 64.0
    col_w = x1 - x0

    # A scrim under the text only. Photographic art has no guaranteed dark area, and white
    # type over a bright patch is the one failure that is invisible at full size and fatal
    # at thumbnail size.
    grad = cairo.LinearGradient(x0 - col_w * 0.30 if not left else x1 + col_w * 0.30,
                                0, x1 if not left else x0, 0)
    grad.add_color_stop_rgba(0, 0, 0, 0, 0.0)
    grad.add_color_stop_rgba(1, 0, 0, 0, 0.62)
    ctx.set_source(grad)
    ctx.rectangle(0, 0, TW, TH)
    ctx.fill()

    # Each line sized to fill the column. Different lengths landing at different sizes is
    # the poster look, and it buys legibility that a single shared size throws away.
    rows = [(top.upper(), (1.0, 1.0, 1.0), 210.0),
            (bottom.upper(), config.FAIL, 150.0)] if bottom else \
           [(top.upper(), (1.0, 1.0, 1.0), 230.0)]
    sized = [(s, c, min(cap, sketch.fit_size(ctx, s, cap, col_w, config.FONT_SANS, bold=True)))
             for s, c, cap in rows if s]

    total = sum(sz * 1.06 for _, _, sz in sized)
    y = TH / 2 - total / 2
    for s, c, sz in sized:
        y += sz * 0.80
        sketch.text(ctx, s, x0, y, sz, c, config.FONT_SANS, bold=True)
        y += sz * 0.26

    sketch.line(ctx, x0, 62, x0 + 150, 62, sketch.Pen(color=config.FAIL, width=8, passes=1))
    sketch.text(ctx, config.CHANNEL, x0, 112, 30, (0.93, 0.93, 0.93), config.FONT_SANS)
    return surf


def main() -> int:
    ap = argparse.ArgumentParser(description="generate an episode thumbnail")
    ap.add_argument("episode", type=Path, nargs="?",
                    help="episode dir (drawn mode); omit when using --fit/--compose")
    ap.add_argument("--text", help="overlay text, max 3 words (drawn mode)")
    ap.add_argument("--subject", default="", help="small supporting line")
    ap.add_argument("--art", default="", choices=["", *sorted(ART)], help="right-side subject")
    ap.add_argument("--fit", type=Path, metavar="IMG",
                    help="crop an external image to 1280x720")
    ap.add_argument("--compose", type=Path, metavar="IMG",
                    help="crop an external image and lay channel type over it")
    ap.add_argument("--top", default="", help="--compose: first line, white")
    ap.add_argument("--bottom", default="", help="--compose: second line, accent")
    ap.add_argument("--side", default="right", choices=["left", "right"],
                    help="--compose: which half the text sits in")
    ap.add_argument("--out", type=Path, help="output path (default <episode>/out/thumbnail.png)")
    args = ap.parse_args()

    if args.compose or args.fit:
        src = args.compose or args.fit
        if not src.exists():
            print(f"no such image: {src}", file=sys.stderr)
            return 1
        if args.compose and not args.top:
            print("--compose needs --top (and usually --bottom)", file=sys.stderr)
            return 1
        surf = compose(src, args.top, args.bottom, args.side) if args.compose else fit(src)
        out = args.out or src.with_name(f"{src.stem}_1280x720.png")
    else:
        if not args.episode or not args.text:
            print("drawn mode needs an episode and --text", file=sys.stderr)
            return 1
        ep = args.episode if args.episode.is_absolute() else config.ROOT / args.episode
        surf = render(args.text, args.subject, args.art)
        out = args.out or ep / "out" / "thumbnail.png"

    out.parent.mkdir(parents=True, exist_ok=True)
    surf.write_to_png(str(out))
    print(f"wrote {out}  ({TW}x{TH})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
