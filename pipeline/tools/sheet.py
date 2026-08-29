"""Contact sheets of scenes, so layout bugs are seen before a seven-minute render.

Two modes:

    python -m pipeline.tools.sheet                                  every scene type
    python -m pipeline.tools.sheet --episode episodes/ep01_...      that episode's visuals

The gallery mode is a smoke test: one representative of every renderer, with deliberately
awkward content (a very long metric, a fan-out diagram, a title that wants two lines),
because every layout bug this pipeline has had showed up first as text overflowing a box.
The episode mode is the check that matters before publishing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cairo

from .. import config, scenes, script, sketch
from ..script import Visual

GALLERY = [
    ("metric_card", Visual("metric_card", {
        "value": "$460,000,000", "sub": "in 45 minutes",
        "label": "KNIGHT CAPITAL, 1 AUG 2012"})),
    ("metric_short", Visual("metric_card", {"value": "73 HOURS", "sub": "Roblox offline"})),
    ("title_card", Visual("title_card", {
        "text": "delete dead code the day you retire it", "sub": "the takeaway"})),
    ("diagram", Visual("diagram", {
        "nodes": "[NYSE] --(orders)--> [SMARS] --(RLP flag)--> [servers 1-7]; "
                 "[SMARS] --(same flag)--> [server 8]",
        "highlight": "server 8", "title": "One flag, two code paths"})),
    ("code", Visual("code", {
        "lang": "java", "highlight": "1",
        "body": "if (flagSet) {\\n    powerPeg.execute(order);   // dead since 2003\\n}",
        "caption": "the flag was repurposed, the old code was not removed"})),
    ("timeline", Visual("timeline", {
        "from": "2003", "to": "Aug 2012", "highlight": "cumulative check moved",
        "marks": "Power Peg written|cumulative check moved|RLP deploy begins|8th server missed"})),
    ("quote", Visual("quote", {
        "text": "One of Knight's technicians did not copy the new code to one of the "
                "eight SMARS computer servers.",
        "source": "SEC Order 34-70694"})),
    ("switch_off", Visual("switch", {
        "state": "off", "title": "there was already a switch sitting there",
        "label": "it used to turn on Power Peg"})),
    ("switch_on", Visual("switch", {
        "state": "on", "title": "same switch, new job",
        "label": "from 2012 it turns on the new feature"})),
    ("mail", Visual("mail", {
        "value": "97", "sub": "warnings, before the market even opened", "shown": "7",
        "title": "the smoke alarm nobody heard"})),
    ("scale", Visual("scale", {
        "small": "212", "small_label": "customer orders in",
        "big": "1400", "big_label": "trades out", "title": "212 in, four million out"})),
    ("clock", Visual("clock", {"fraction": "0.75", "title": "45 minutes"})),
    ("people", Visual("people", {
        "n": "10", "highlight": "1", "title": "one trade in ten",
        "caption": "roughly one in ten American stock trades went through Knight"})),
    ("servers", Visual("servers", {
        "n": "8", "bad": "8", "title": "seven of eight",
        "label": "the eighth never got the new code"})),
    ("counter", Visual("counter", {
        "value": "50000", "label": "stop when the tally gets here",
        "title": "and it kept a tally"})),
    ("counter_blank", Visual("counter", {
        "value": "50000", "blank": "on", "label": "nothing there",
        "title": "it goes looking for its tally"})),
    ("alarm", Visual("alarm", {
        "title": "a smoke alarm going off in a room nobody uses",
        "caption": "ninety minutes, in real time"})),
    ("calendar", Visual("calendar", {
        "years": "2003|2004|2005|2006|2007|2008|2009|2010|2011|2012", "mark": "2",
        "title": "nine quiet years", "note": "the tally moved in 2005"})),
    ("checklist", Visual("checklist", {
        "items": "a second person checks the work|a written rule says they must|"
                 "the system compares the eight",
        "title": "nobody checked"})),
    ("dashboard", Visual("dashboard", {
        "title": "because nothing looked broken",
        "caption": "healthy computers, healthy network, orders filling"})),
    ("loop", Visual("loop", {"title": "the loop with no exit", "label": "send. fill."})),
    ("link", Visual("link", {
        "left": "Power Peg", "right": "the tally",
        "title": "the old feature was never reconnected"})),
    ("lock", Visual("lock", {
        "title": "nobody attacked them", "label": "nothing was broken into"})),
    ("end_card", Visual("end_card", {"next": "the regex that took down Cloudflare"})),
    # EP02 set. Sheeted at t=1.0 like everything else, which for these means "after the
    # motion has settled" — the point of the sheet is layout, not choreography.
    ("gauge", Visual("gauge", {
        "value": "0.99", "label": "every core, everywhere",
        "title": "the machines stopped being able to do anything else"})),
    ("world", Visual("world", {
        "title": "and it went everywhere in about two seconds",
        "caption": "more than 180 cities"})),
    ("windows", Visual("windows", {
        "bad": "0.8", "title": "what everyone else saw", "code": "502",
        "caption": "not the site you asked for"})),
    ("barrier", Visual("barrier", {
        "title": "there used to be a guard on this",
        "label": "taken out weeks earlier, while making the filter faster"})),
    ("backtrack", Visual("backtrack", {
        "text": "x=xxxxxxx", "target": "555", "rate": "9",
        "title": "it tries every possible way", "caption": "one short string"})),
    ("door", Visual("door", {
        "title": "then they could not get in", "label": "the door was behind the outage"})),
    ("stick_crowd", Visual("stick", {
        "pose": "panic", "n": "4", "hot": "2", "title": "everybody in one room"})),
]


def _tile(cases: list[tuple[str, Visual]], out: Path, cols: int = 3) -> None:
    tw, th = 640, 360
    rows = (len(cases) + cols - 1) // cols
    sheet = cairo.ImageSurface(cairo.FORMAT_ARGB32, tw * cols, th * rows)
    sctx = cairo.Context(sheet)
    sctx.set_source_rgb(0.10, 0.10, 0.12)     # dark surround: the frames are warm paper
    sctx.paint()
    for i, (_, vis) in enumerate(cases):
        surf, ctx = sketch.new_surface()
        scenes.render(ctx, vis, t=1.0)
        col, row = i % cols, i // cols
        sctx.save()
        sctx.translate(col * tw + 4, row * th + 4)
        sctx.scale((tw - 8) / config.W, (th - 8) / config.H)
        sctx.set_source_surface(surf, 0, 0)
        sctx.paint()
        sctx.restore()
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.write_to_png(str(out))
    print(f"wrote {out}  ({len(cases)} scenes)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--episode", type=Path, help="sheet this episode's visuals instead")
    ap.add_argument("--out", type=Path, help="output png (default beside the episode)")
    ap.add_argument("--per-sheet", type=int, default=9)
    args = ap.parse_args()

    if not args.episode:
        _tile(GALLERY, args.out or config.SCRATCH / "scene_gallery.png")
        return 0

    ep = args.episode if args.episode.is_absolute() else config.ROOT / args.episode
    doc = script.parse(ep / "script.md")
    seen: list[Visual] = []
    for b in doc.beats:
        if b.visual and (not seen or b.visual is not seen[-1]):
            seen.append(b.visual)

    base = args.out or ep / "out" / "visuals.png"
    for i in range(0, len(seen), args.per_sheet):
        chunk = [(f"{i + j}", v) for j, v in enumerate(seen[i:i + args.per_sheet])]
        _tile(chunk, base.with_name(f"{base.stem}_{i // args.per_sheet + 1}{base.suffix}"))
    print(f"{len(seen)} distinct visuals total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
