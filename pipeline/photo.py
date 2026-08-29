"""Free-licence photography, fetched once and treated into the channel's palette.

Added 2026-08-12 on the channel owner's call ("you can always add stock free images"),
because the honest diagnosis of EP04's first cut was that a near-black frame with vector
line art on it reads as the same empty stage every episode, however good the line art.
A photographic plate behind the drawing is the one thing that puts a real place on screen.

Three rules make this safe on a factual channel, and they are not negotiable:

1. **Licence.** Only CC0 / public-domain / PDM results are downloaded. Every fetched file
   gets a `.json` sidecar with the source URL, licence and creator, and `credits()`
   renders the ledger that goes into research.md.
2. **Generic illustration, never evidence.** A photo here depicts a *kind* of place (a
   server room, a night skyline), never "this is the room where it happened". It is
   composited dark and defocused underneath the channel's own drawing, so it reads as
   atmosphere. HOUSE_STYLE §4 still forbids a fabricated artefact — no invented
   screenshots, dashboards or documents, photographic or otherwise.
3. **It never carries the meaning.** The drawing carries the meaning; the plate carries
   the room. Treated to sit 4-5x darker than the ink over it.

    python -m pipeline.photo --fetch          # populate assets/photo/ from the manifest
    python -m pipeline.photo --list           # what is cached, with licences
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

import cairo

from . import config

CACHE = config.ASSETS / "photo"
API = "https://api.openverse.org/v1/images/"
UA = {"User-Agent": "postmortem-channel/1.0 (educational video essay; contact via channel)"}

# name -> search query. One entry per plate the episodes actually use; fetching is
# deliberately manifest-driven rather than ad-hoc so a render can never depend on a live
# API call, and so the licence ledger is complete by construction.
MANIFEST = {
    "server_room":   "server room data center racks",
    "server_aisle":  "data center corridor servers",
    "night_city":    "city at night skyline",
    "fiber":         "fiber optic cable",
    "cables":        "network cables",
    "office_night":  "office at night",
    "ledger":        "old ledger book",
    "tape_backup":   "magnetic tape reel storage",
    "control_room":  "control room",
    "sunrise_city":  "sunrise over city skyline",
    # EP05 (Roblox). The story is a warehouse that never gives space back, one doorway
    # everything funnels through, and fifty million people outside a closed door.
    "warehouse":     "warehouse shelves storage racks",
    "archive_papers": "archive shelves paper files",
    "crowd_queue":   "crowd of people queue waiting",
    "turnstile":     "turnstile gates entrance",
    "arcade":        "arcade machines neon",
}


def _sidecar(name: str) -> Path:
    return CACHE / f"{name}.json"


def path(name: str) -> Path | None:
    """Cached JPEG for `name`, or None if it was never fetched."""
    p = CACHE / f"{name}.jpg"
    return p if p.exists() else None


def fetch(name: str, query: str, *, force: bool = False) -> bool:
    """Download the best CC0 result for `query`. Returns True if a file is on disk."""
    if not force and path(name):
        return True
    CACHE.mkdir(parents=True, exist_ok=True)
    url = API + "?" + urllib.parse.urlencode(
        {"q": query, "license": "cc0,pdm,by", "page_size": 12, "mature": "false"})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
            results = json.load(r).get("results", [])
    except Exception as exc:                       # noqa: BLE001 - network is best effort
        print(f"[photo] search failed for {name}: {exc}")
        return False

    for item in results:
        # Landscape and big enough to fill 1920 wide after a crop.
        w, h = item.get("width") or 0, item.get("height") or 0
        # 900px is enough: every plate is defocused and darkened, so an upscale
        # is invisible while a too-strict floor rejected 8 of 10 subjects.
        if w < 900 or h < 560 or w < h * 0.9:
            continue
        src = item.get("url")
        if not src:
            continue
        try:
            with urllib.request.urlopen(urllib.request.Request(src, headers=UA), timeout=60) as r:
                data = r.read()
        except Exception as exc:                   # noqa: BLE001
            print(f"[photo] download failed for {name}: {exc}")
            continue
        (CACHE / f"{name}.jpg").write_bytes(data)
        _sidecar(name).write_text(json.dumps({
            "name": name, "query": query,
            "title": item.get("title"), "creator": item.get("creator"),
            "license": item.get("license"), "license_version": item.get("license_version"),
            "source": item.get("foreign_landing_url"), "file": src,
            "width": w, "height": h,
        }, indent=1), encoding="utf-8")
        print(f"[photo] {name}: {item.get('license')} · {w}x{h} · {item.get('title')}")
        return True
    print(f"[photo] no usable CC0 result for {name!r}")
    return False


def credits() -> str:
    """Markdown ledger of every cached plate, for research.md."""
    rows = ["| Plate | Licence | Source |", "|---|---|---|"]
    for sc in sorted(CACHE.glob("*.json")):
        d = json.loads(sc.read_text(encoding="utf-8"))
        rows.append(f"| `{d['name']}` | {(d.get('license') or '?').upper()} "
                    f"{d.get('license_version') or ''} | {d.get('source') or d.get('file')} |")
    return "\n".join(rows)


# ---------------------------------------------------------------- treatment
_TREATED: dict[tuple, tuple[cairo.ImageSurface, bytearray]] = {}


def plate(name: str, *, w: int = config.W, h: int = config.H,
          darken: float = 0.72, blur: int = 0, tint: tuple | None = None,
          desat: float = 0.82) -> cairo.ImageSurface | None:
    """A treated photographic plate, cropped to fill (w, h). Cached per parameter set.

    The treatment is what makes a stock photo belong to this channel rather than look
    pasted in: desaturate hard, crush toward the palette's near-black, tint into the
    section's hue, and optionally defocus so it never competes with the line art.
    """
    src = path(name)
    if src is None:
        return None
    key = (name, w, h, darken, blur, tint, desat)
    if key in _TREATED:
        return _TREATED[key][0]

    from PIL import Image, ImageEnhance, ImageFilter
    im = Image.open(src).convert("RGB")

    # Cover-crop to the target aspect, centred.
    tr, ir = w / h, im.width / im.height
    if ir > tr:
        nw = int(im.height * tr)
        im = im.crop(((im.width - nw) // 2, 0, (im.width + nw) // 2, im.height))
    else:
        nh = int(im.width / tr)
        im = im.crop((0, (im.height - nh) // 2, im.width, (im.height + nh) // 2))
    im = im.resize((w, h), Image.LANCZOS)

    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    im = ImageEnhance.Color(im).enhance(1.0 - desat)
    im = ImageEnhance.Brightness(im).enhance(1.0 - darken)

    import numpy as np
    arr = np.asarray(im).astype(np.float32) / 255.0
    if tint is not None:
        # Push the midtones toward the tint without lifting the blacks.
        lum = arr.mean(axis=2, keepdims=True)
        arr = arr * (1 - 0.55 * lum) + np.array(tint, dtype=np.float32) * (0.55 * lum)
    # Seat the darkest values on the channel's ground so the plate and the bare
    # backdrop are the same black.
    arr = np.clip(arr, 0.0, 1.0) * 0.92 + np.array(config.BG, dtype=np.float32) * 0.08

    rgba = np.empty((h, w, 4), dtype=np.uint8)
    rgba[:, :, 2] = (arr[:, :, 0] * 255).astype(np.uint8)   # cairo is BGRA
    rgba[:, :, 1] = (arr[:, :, 1] * 255).astype(np.uint8)
    rgba[:, :, 0] = (arr[:, :, 2] * 255).astype(np.uint8)
    rgba[:, :, 3] = 255
    # create_for_data does NOT copy: the surface points straight at this buffer, so the
    # buffer has to outlive it. cairo.ImageSurface has no __dict__, so it cannot carry the
    # reference itself — the cache holds both, and drawing from a freed buffer is exactly
    # the kind of bug that renders garbage on one frame in a thousand.
    buf = bytearray(rgba.tobytes())
    surf = cairo.ImageSurface.create_for_data(
        memoryview(buf), cairo.FORMAT_ARGB32, w, h, w * 4)
    _TREATED[key] = (surf, buf)
    return surf


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="free-licence photo plates")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    if args.fetch:
        ok = sum(fetch(n, q, force=args.force) for n, q in MANIFEST.items())
        print(f"[photo] {ok}/{len(MANIFEST)} plates available in {CACHE}")
    if args.list:
        print(credits())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
