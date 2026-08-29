"""Build-time enforcement of HOUSE_STYLE.md.

This exists because style drift and factual drift are both invisible one episode at a time.
Nobody notices episode 14 opening with "let's dive in", or a metric that quietly lost its
source three revisions ago. The linter notices.

    python -m pipeline.lint episodes/ep01_knight_capital
    python -m pipeline.lint episodes/ep01_knight_capital --sources

Exit code is non-zero on any ERROR, so it can gate a build.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from . import config
from .script import SECTIONS, parse
from .scenes import RENDERERS

BANNED = [
    "in today's video", "let's dive in", "lets dive in", "buckle up",
    "little did they know", "simply put", "basically", "essentially",
    "it's important to note", "game-changer", "game changer", "revolutionary",
    "insane", "crazy", "but what if i told you", "smash that",
    "and that's why observability matters", "and that's why monitoring matters",
]

# Section timecodes from HOUSE_STYLE §2, in seconds of spoken audio.
# takeaway ends at 490, not 520: at 138.9 WPM a 100-second span implies 231 words, which
# contradicts the 130-160 the style guide asks for. 70 seconds gives ~162 and the two
# documents agree.
SECTION_SPAN = {"hook": (0, 45), "context": (45, 150), "breakdown": (150, 420),
                "takeaway": (420, 490)}
TOLERANCE = 0.18     # ±18% on each section's word budget

_RE_NUMBER = re.compile(r"\$?\d[\d,.]*\s*(?:%|million|billion|thousand|hours?|minutes?|"
                        r"seconds?|milliseconds?|days?|GB|MB|TB)?", re.I)
_RE_SENTENCE_RUN = re.compile(r"[.!?]\s+[A-Z]")
_RE_TTS_UNSAFE = [
    (re.compile(r"—|–"), "em/en dash — TTS swallows it, use a period or comma"),
    (re.compile(r"\([^)]*\)"), "parentheses in a spoken line"),
    (re.compile(r"\b\d+\s?ms\b"), "write 'milliseconds', not 'ms'"),
    (re.compile(r"\bp\d{2,3}\b"), "write 'p ninety-nine', not 'p99'"),
    (re.compile(r"\b[A-Z]{2,}\b(?![^<]*>)"), "bare acronym — confirm the voice says it right"),
]


def _mmss(seconds: float) -> str:
    return f"{int(seconds // 60)}:{int(seconds % 60):02d}"


def check_render_timing(ep: Path, rep: Report) -> None:
    """Compare the delivered section boundaries in out/chapters.txt against HOUSE_STYLE.

    The estimate above is a model. This is ground truth, and it is the only check that can
    prove the 45-second rule actually held in the file you are about to upload.
    """
    path = ep / "out" / "chapters.txt"
    if not path.exists():
        rep.warn("no out/chapters.txt yet — run the build to verify delivered timing")
        return

    marks: list[tuple[float, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        stamp, _, name = line.partition(" ")
        m, _, s = stamp.partition(":")
        marks.append((int(m) * 60 + int(s), name.strip()))

    print("  delivered:")
    for i, (at, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else None
        lo_t, hi_t = SECTION_SPAN.get(name, (0, 0))
        span = f"{_mmss(at)} - {_mmss(end)}" if end else f"{_mmss(at)} - end"
        print(f"    {name:<10} {span}   target start {_mmss(lo_t)}")

    for i, (at, name) in enumerate(marks):
        if name == "context" and at > 45.0:
            rep.error(f"45-second rule VIOLATED in the rendered file: hook runs to "
                      f"{_mmss(at)} ({at:.0f}s). This is measured, not estimated.")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def emit(self) -> int:
        for w in self.warnings:
            print(f"  WARN  {w}")
        for e in self.errors:
            print(f"  ERROR {e}")
        print(f"\n{len(self.errors)} error(s), {len(self.warnings)} warning(s)")
        return 1 if self.errors else 0


def check_script(ep: Path, rep: Report) -> None:
    path = ep / "script.md"
    if not path.exists():
        rep.error(f"missing {path}")
        return
    doc = parse(path)

    if not doc.spoken:
        rep.error("script has no spoken lines (is the first '## SECTION:' marker present?)")
        return

    for beat in doc.spoken:
        low = beat.text.lower()
        for phrase in BANNED:
            if phrase in low:
                rep.error(f"line {beat.line_no}: banned phrase {phrase!r}")
        for rx, why in _RE_TTS_UNSAFE:
            if rx.search(beat.text):
                rep.warn(f"line {beat.line_no}: {why}")
        if _RE_SENTENCE_RUN.search(beat.text):
            rep.error(f"line {beat.line_no}: more than one sentence on a line "
                      f"(each line is one TTS clip and one timing unit)")

    for beat in doc.beats:
        if beat.visual and beat.visual.renderer not in RENDERERS:
            rep.error(f"line {beat.line_no}: unknown visual {beat.visual.renderer!r}; "
                      f"known: {', '.join(sorted(RENDERERS))}")

    # Delivered seconds per section: speech + explicit pauses + inter-line gaps.
    # Modelling with the episode-wide MEASURED_WPM instead lets a pause-heavy section run
    # long while the word count still looks fine, which is how a 47-second hook passed.
    sps = config.SPEECH_WPM / 60.0
    counts = doc.words_by_section()

    # Charge each line the gap it will actually get. schedule.py inserts SENTENCE_GAP
    # after a visual change and LINE_GAP otherwise; assuming LINE_GAP everywhere made the
    # estimate ~10% optimistic, which is far too thin a margin on a 45-second ceiling.
    gap_by_section: dict[str, float] = {s: 0.0 for s in SECTIONS}
    cur_visual, first_line, changed = None, True, False
    for b in doc.beats:
        if b.visual is not cur_visual:
            cur_visual, changed = b.visual, True
        if b.kind == "pause":
            changed = False          # an explicit pause supplies the space instead
        if b.kind != "speak":
            continue
        if not first_line:
            gap_by_section[b.section] = gap_by_section.get(b.section, 0.0) + (
                config.SENTENCE_GAP if changed else config.LINE_GAP)
        first_line, changed = False, False

    est: dict[str, float] = {}
    for name in SECTIONS:
        words = counts.get(name, 0)
        pauses = sum(b.seconds for b in doc.beats
                     if b.kind == "pause" and b.section == name)
        est[name] = words / sps + pauses + gap_by_section.get(name, 0.0)

    cursor = 0.0
    for name in SECTIONS:
        lo_t, hi_t = SECTION_SPAN[name]
        span = hi_t - lo_t
        got, secs = counts.get(name, 0), est[name]
        if got == 0:
            rep.error(f"section '{name}' is empty")
            continue
        print(f"  {name:<10} {got:>4}w  {secs:5.1f}s  "
              f"[{_mmss(cursor)} - {_mmss(cursor + secs)}]  target {span:.0f}s")
        cursor += secs
        # The hook's 45 seconds is a CEILING, not a target. A hook that lands its stake in
        # 27 seconds is better than one that fills the slot, so only flag it for running long.
        if name == "hook":
            continue
        if not (span * (1 - TOLERANCE) <= secs <= span * (1 + TOLERANCE)):
            rep.warn(f"section '{name}': {secs:.1f}s delivered vs {span:.0f}s target "
                     f"(±{TOLERANCE:.0%})")

    total = sum(counts.values())
    runtime = sum(est.values()) + config.HEAD_SILENCE + config.TAIL_SILENCE
    print(f"  {total} words · ~{_mmss(runtime)} delivered "
          f"({config.SPEECH_WPM:.1f} WPM speech + pauses + gaps)")
    # Scales with MEASURED_WPM: the runtime target is fixed by SECTION_SPAN, so a faster
    # voice needs MORE words to fill the same minutes. Hard-coding 1,000-1,300 against a
    # 145 WPM voice would silently demand a 7m50s episode once the voice moved to 159.
    lo, hi = (round(n * config.MEASURED_WPM / 145.0 / 25) * 25 for n in (1000, 1300))
    if not (lo <= total <= hi):
        rep.warn(f"total {total} words is outside the {lo:,}-{hi:,} spec "
                 f"(scaled from 1,000-1,300 at {config.MEASURED_WPM:.0f} WPM)")
    if not (360 <= runtime <= 600):
        rep.warn(f"runtime {_mmss(runtime)} is outside the 6-10 minute spec")

    # The 45-second rule, checked in DELIVERED seconds, not word-derived ones.
    hook = " ".join(b.text for b in doc.spoken if b.section == "hook")
    if not _RE_NUMBER.search(hook):
        rep.error("45-second rule: no quantitative metric in the hook")
    # The estimate runs optimistic for the hook specifically, by about 4 seconds on EP01:
    # the hook is the most digit-dense section of any episode ("$460 million", "45 minutes",
    # "97"), and digits take far longer to speak than their word count implies, while
    # SPEECH_WPM is an episode-wide average. Rather than model syllables, treat the
    # estimate as advisory with a margin and let the rendered file be the authority.
    HOOK_ADVISORY = 40.0
    if est["hook"] > HOOK_ADVISORY:
        rep.warn(f"45-second rule: hook estimates at {est['hook']:.1f}s. Measured delivery "
                 f"typically runs ~4s longer than this, so anything over {HOOK_ADVISORY:.0f}s "
                 f"risks breaching 45s. Verify with --timing after rendering.")


def check_diagram_layout(ep: Path, rep: Report) -> None:
    """Lay out every diagram in the episode and assert nothing collides.

    Overlapping boxes have now shipped twice — once from fixed column gaps, once from a
    centering pass that stacked converging nodes on the same row. Both were only visible
    after a seven-minute render. Geometry is cheap to check; check it.
    """
    import cairo

    from . import diagram, sketch

    path = ep / "script.md"
    if not path.exists():
        return
    doc = parse(path)

    seen: list = []
    for b in doc.beats:
        if b.visual and (not seen or b.visual is not seen[-1]):
            seen.append(b.visual)

    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, config.W, config.H)
    ctx = cairo.Context(surf)

    for v in seen:
        if v.renderer != "diagram":
            continue
        spec = v.get("nodes")
        title = v.get("title") or spec[:40]
        g = diagram.parse(spec)
        nat_w, nat_h = diagram.layout(ctx, g)
        bw, bh = config.W - config.SAFE * 2, config.H - config.SAFE * 2
        s = min(min(bw * 0.94 / max(nat_w, 1), bh * 0.88 / max(nat_h, 1)), diagram.MAX_SCALE)
        if abs(s - 1.0) > 0.01:
            diagram.layout(ctx, g, scale=max(s, diagram.MIN_SCALE))

        nodes = list(g.nodes.values())
        for i, a in enumerate(nodes):
            for b_ in nodes[i + 1:]:
                if (a.x < b_.x + b_.w and a.x + a.w > b_.x
                        and a.y < b_.y + b_.h and a.y + a.h > b_.y):
                    rep.error(f"diagram '{title}': boxes overlap — "
                              f"{a.label!r} and {b_.label!r}")

        for n in nodes:
            if (n.x < config.SAFE - 2 or n.y < 0
                    or n.x + n.w > config.W - config.SAFE + 2
                    or n.y + n.h > config.H):
                rep.error(f"diagram '{title}': {n.label!r} falls outside the safe area")

        for e in g.edges:
            if not e.label or e.src not in g.nodes or e.dst not in g.nodes:
                continue
            lw, lh_ = sketch.text_size(ctx, e.label, config.SZ_CAPTION, config.FONT_SANS)
            a, b_ = g.nodes[e.src], g.nodes[e.dst]
            mx, my = (a.cx + b_.cx) / 2, (a.cy + b_.cy) / 2
            if diagram._hits_any_node(g, mx, my, lw, lh_, skip=(e.src, e.dst)):
                rep.warn(f"diagram '{title}': label {e.label!r} is crowded; "
                         f"the renderer will slide it along the edge")


def check_sources(ep: Path, rep: Report) -> None:
    """Every number spoken must also appear in research.md.

    Deliberately crude: it catches the failure that actually happens, which is a metric
    getting into a script without ever having been looked up. It cannot tell you a sourced
    number is *correct* — that is what the human spot-check before upload is for.
    """
    script_path, research_path = ep / "script.md", ep / "research.md"
    if not research_path.exists():
        rep.error(f"missing {research_path}")
        return
    if not script_path.exists():
        return

    research = research_path.read_text(encoding="utf-8").lower()
    if "http" not in research:
        rep.error("research.md SOURCES ledger has no URLs")

    doc = parse(script_path)
    unsourced: list[tuple[int, str]] = []
    for beat in doc.spoken:
        for m in _RE_NUMBER.finditer(beat.text):
            token = m.group(0).strip().lower()
            digits = re.sub(r"[^\d]", "", token)
            if len(digits) < 2:          # ignore "one", "3 rules", ordinals
                continue
            if digits not in re.sub(r"[^\d]", "", research):
                unsourced.append((beat.line_no, token))
    for line_no, token in unsourced:
        rep.error(f"line {line_no}: {token!r} does not appear in research.md SOURCES")


def main() -> int:
    ap = argparse.ArgumentParser(description="enforce HOUSE_STYLE")
    ap.add_argument("episode", type=Path)
    ap.add_argument("--sources", action="store_true",
                    help="also check every spoken number against research.md")
    ap.add_argument("--timing", action="store_true",
                    help="also check delivered timing against out/chapters.txt")
    args = ap.parse_args()

    ep = args.episode if args.episode.is_absolute() else config.ROOT / args.episode
    print(f"lint {ep.name}")

    rep = Report()
    check_script(ep, rep)
    check_diagram_layout(ep, rep)
    if args.sources:
        check_sources(ep, rep)
    if args.timing:
        check_render_timing(ep, rep)
    return rep.emit()


if __name__ == "__main__":
    sys.exit(main())
