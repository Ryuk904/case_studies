# Channel identity — POSTMORTEM

Everything needed to create the channel. Assets are generated, not drawn by hand:

```bash
python -m pipeline.brand        # -> assets/brand/
```

Regenerate after any palette change in `config.py` and the identity stays in step with the
videos automatically. That is the reason these are code and not exported images.

---

## Name and handle

**Channel name:** `POSTMORTEM`

Keep it. It is already stamped on all 14,440 frames of EP01 via `config.CHANNEL`, so changing
it means a re-render, and it is a good name regardless: one word, it names the format exactly,
and it is a normal English phrase ("let's do a postmortem on that") rather than engineer
jargon — which matters, because the whole channel is written for people who are not engineers.

**Handle:** `@postmortem.eng` *(or another dotted variant — see below)*

`@postmortem` is taken, by a channel styling itself "PosTMorteM". So are `@postmortemshow`
and `@howitbroke`. `@postmortem.eng` returned a clean 404, meaning unclaimed at the time of
checking.

**This is not the problem it first looks like.** YouTube's *display name* does not have to be
unique — only the handle does. So the channel is called POSTMORTEM on screen, in search
results, and everywhere a viewer looks; the handle is a URL slug they will rarely type.

Dotted handles are far less contested than bare words, so if `.eng` is gone by the time you
sign up, try `@postmortem.studio`, `@postmortem.cases`, `@postmortem.files`. Verify at signup
— availability moves, and the check above was indirect (HTTP 404 vs a live page), not the
signup form.

---

## Avatar

Upload **`assets/brand/avatar_icon_800.png`** — the symbol-only version.

Two versions are generated and the icon is the right pick. Tested by circle-cropping both at
the three sizes YouTube actually renders:

| | 150px (channel page) | 98px (search) | 48px (comments) |
|---|---|---|---|
| with wordmark | sharp | sharp | **wordmark turns to mush** |
| icon only | sharp | sharp | **sharp** |

The wordmark inside the circle is redundant anyway: YouTube prints the channel name next to
the avatar in every single placement.

The mark is a pulse that spikes once and then flatlines. It survives being shrunk because it
is one stroke, it means the same thing to an engineer and to someone who has never written
code, and the two colours are load-bearing — amber for the live trace, red for the flatline,
the same amber-and-red the videos use for "the thread" and "the failure".

---

## Banner

Upload **`assets/brand/banner_2560x1440.png`** (137 KB, limit is 6 MB).

`banner_safe_area_proof.png` is the same image with the device crops drawn on. Do not upload
that one.

**The geometry is a spec, not a preference**, and it has one trap in it:

| device | shows |
|---|---|
| phone | centre **1546×423** — the safe area |
| desktop | **2560×423** |
| TV | the whole **2560×1440** |

Desktop and phone share the *same 423px vertical band* and differ only in width. So anything
placed above or below that band is seen on televisions and nowhere else. The first draft put
a full-width rule at `cy+250`, comfortably outside the band, where essentially no one would
ever have seen it. Decoration you actually want on desktop has to be inside the 423px band
and extend *sideways*.

Verified clearances for the mark and type inside the phone-safe box: top 101px, bottom 64px,
left 42px, right 339px.

---

## Video watermark

Upload **`assets/brand/watermark_150.png`** under *Customisation → Branding → Video watermark*.
Transparent PNG, ink only, so it reads on the dark frames without fighting them.

Set display time to **"Entire video"**. On a channel with no subscribers the watermark is a
persistent subscribe button; there is no reason to hide it.

---

## Channel description (About)

Paste as-is. First 100-odd characters are what surfaces in search, so the hook is front-loaded.

```
Engineering disasters, explained properly — for anyone, not just engineers.

Every episode takes one real failure and works out exactly how it happened: what was built,
why that was reasonable at the time, and the small ordinary decision that turned out to be
load-bearing. $460 million lost in 45 minutes. 80% of a network offline in 27. One line of
code, one flag, one server that got missed.

No hype, no blame, no "and that's why you should monitor your systems". Just the mechanism,
drawn out step by step until it makes sense.

Every number spoken in a video is quoted from a primary source — the company's own
postmortem, an SEC filing, an NTSB report — and the source is linked in the description. If
two sources disagree, the video says so.

New case study every other week.
```

## Channel keywords

*Settings → Channel → Basic info → Keywords.* Comma-separated:

```
engineering disasters, software failure, case study, postmortem, incident analysis,
tech explained, how it broke, system failure, outage, root cause, computer history,
technology documentary
```

## Links

Add under *Customisation → Basic info → Links*. At minimum a contact email. If you add
anything else, make it something you will actually maintain — an abandoned link on a
three-video channel reads worse than none.

---

## Settings to get right before the first upload

| Setting | Value | Why |
|---|---|---|
| Category | Science & Technology | |
| Language | English | |
| Made for kids | **No** | Getting this wrong disables comments and suggested traffic |
| Comments | Hold potentially inappropriate for review | Sensible default; you are inviting corrections |
| Channel trailer | EP01 | For non-subscribers. A dedicated trailer can wait until there are 3+ episodes |
| Featured video | EP01 | For returning subscribers |
| Watermark | Entire video | |

## Playlists

Do not create empty playlists yet — a playlist with one video in it looks like an abandoned
channel. Once EP03 exists, one playlist is enough: **"Case studies"**, in upload order.
Split by theme only when there is enough to split.

---

## What is deliberately not here

**Prompts for an image model.** These assets are almost entirely typography, and diffusion
models still mangle letterforms — which would be most visible exactly where it hurts, in a
98px avatar. Drawing them in cairo also means they share the episode palette and font stack
by construction rather than by eye, and regenerate for free when the palette changes.

If you ever do want an illustrated banner — a photographic scene behind the lockup rather
than a flat field — that is the one part worth generating, and `episodes/*/thumbnail_prompt.md`
shows the house prompt format to copy: state the palette in hex, keep the text out of the
generated image, and composite the type in code afterwards.
