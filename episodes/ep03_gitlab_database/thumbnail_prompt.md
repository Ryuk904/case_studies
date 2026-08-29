# EP03 — thumbnail prompts for ChatGPT

Paste one of these into ChatGPT with image generation. **Concept A is the recommended one.**

**Three things to know before you start.**

1. ChatGPT's image tool outputs 1536×1024 (3:2), not 16:9. Generate it wide, then crop to
   1280×720. `python -m pipeline.thumbnail --fit <file>` does the crop.
2. Image models still mangle text at small sizes, and the words are the part that has to
   survive being 168px wide in the phone feed. So each concept below comes in two forms:
   **with text** (one prompt, fastest) and **art only** (generate the picture, then
   `python -m pipeline.thumbnail --compose <art.png> --top "..." --bottom "..."` lays the
   channel's own type over it, crisp and on-brand every time). Try the with-text version
   first; if the lettering comes back wonky after two attempts, switch to art-only.
3. **The palette below is the video's palette.** Near-black `#0E1013`, off-white `#F2F0EA`,
   amber `#F5A623`, one hot red `#FF4757`. Amber is the thread the eye follows; red means
   the failure. Never both doing the same job in one image.

**The channel-page problem this has to avoid.** EP01 is a lit object on a dark wall and
EP02 is a typographic line buckling under a slab. Concept A is a *row of objects with a
count* — a third kind of image, and the count "0 of 5" does the storytelling on its own.

---

## Concept A — five dead drives *(recommended)*

The episode's whole idea in one picture: five safety nets, none working. Five identical
objects, five red crosses, one glance.

### A — with text

> A dramatic 16:9 illustration on a near-black background. A row of five identical
> external hard drives standing upright like tombstones, evenly spaced across the lower
> half of the frame, drawn in clean off-white outline on near-black, each with a small
> status light. Every drive is stamped with a large rough hot-red X that glows slightly,
> as if marked in light. The row is lit hard from the upper left, throwing long shadows to
> the right. Above the row, vast empty darkness. Large bold condensed off-white sans-serif
> text in the upper left, stacked on two lines: "5 BACKUPS" in off-white, and "0 WORKED"
> in hot red beneath it. Extreme contrast, poster-like, cinematic editorial illustration,
> no clutter. Palette strictly near-black #0E1013, off-white #F2F0EA, amber #F5A623 and
> one hot red #FF4757. No logos, no brand names, no watermarks, no people, no readable
> small text anywhere.

### A — art only

> A dramatic 16:9 cinematic illustration on a near-black background, no text anywhere. A
> row of five identical external hard drives standing upright like tombstones, evenly
> spaced across the lower half of the frame, drawn in clean off-white outline on
> near-black, each with a small status light. Every drive is stamped with a large rough
> hot-red X that glows slightly, as if marked in light. Lit hard from the upper left, long
> shadows to the right. The upper half of the frame falls into pure near-black and stays
> completely empty. Extreme contrast, poster-like. Palette strictly near-black #0E1013,
> off-white #F2F0EA, amber #F5A623 and one hot red #FF4757. No text, no letters, no
> numbers, no logos, no watermarks, no people.

Then:

```
python -m pipeline.thumbnail --compose art.png --top "5 BACKUPS" --bottom "0 WORKED"
```

---

## Concept B — the wrong terminal

The mistake itself: two identical windows, one glowing wrong. Strong cold-open image,
weaker than A at carrying the "everything failed" half of the story.

> A 16:9 YouTube thumbnail illustration on a near-black background. Two identical dark
> terminal windows side by side, drawn in off-white outline, floating on near-black. The
> left window glows hot red from inside, spilling red light onto the darkness around it;
> the right window is calm and dim. Inside each window, a single short line of illegible
> dense code texture, no readable characters. A large amber arrow or cursor hovers over
> the red window, as if a command was just sent to the wrong one. Extreme contrast,
> cinematic, uncluttered. Large bold condensed off-white sans-serif text across the top
> reading "WRONG SERVER", and smaller hot red text beneath it reading "300 GB GONE".
> Palette strictly near-black #0E1013, off-white #F2F0EA, amber #F5A623 and one hot red
> #FF4757. No logos, no brand names, no watermarks, no people.

---

## Concept C — the accidental lifeboat

The twist, for the long tail: everything sunk except one small copy nobody planned.

> A 16:9 cinematic illustration on a near-black background. Four large dark server towers
> sinking at angles into a black void at the bottom of the frame, drawn in dim off-white
> outline, each stamped with a small hot-red X. Above and apart from them, one small plain
> box glows warm amber, intact, floating alone in the darkness, casting the only warm
> light in the image. Deep shadow, volumetric amber glow, extreme contrast. Large bold
> condensed off-white sans-serif text in the dark upper right reading "EVERY BACKUP
> FAILED", and beneath it in amber "EXCEPT THE ACCIDENT". Palette strictly near-black
> #0E1013, off-white #F2F0EA, amber #F5A623 and one hot red #FF4757. No logos, no brand
> names, no watermarks, no people.

---

## If you want to iterate

The single most useful follow-up instruction to ChatGPT is:

> Make it read at thumbnail size. Fewer objects, bigger subject, higher contrast, and push
> the text larger. Assume it will be viewed 170 pixels wide.

Others that reliably help:

- "Make the background darker and the red hotter." — models drift toward mid-grey, which
  is the one value that kills a dark thumbnail. Push it back to near-black every round.
- "Make the drives bigger and the gaps smaller." — for Concept A the row must own the
  frame; first drafts always float five small objects in space, which is the classic
  small-subject failure.
- "Remove the [thing]." — image models add clutter; subtracting beats describing.

## Rules that must hold whichever you pick

- **No GitLab logo, no fox/tanuki mascot, no recognisable real person.** This is factual
  reporting about a real company; the thumbnail must not look like it was issued by them.
- **No fabricated screenshots** of a real dashboard, status page, or news chyron.
- **No literal `rm -rf` rendered as readable text.** The command appears in neither
  primary source (see research.md, "Unverified — do not use"), and a thumbnail is not a
  place to invent a quote. Code in these images is texture — "illegible dense code
  texture, no readable characters".
- Text ≤ 4 words per line, 2 lines maximum.
- Check it at 168×94. If you cannot count five drives at that size, drop to four visible
  and let the text carry the number — the count in the *text* is the sourced one.
  (Better: fewer, bigger drives.)
- Check it against a black phone UI, not a white desktop one. A near-black thumbnail can
  disappear into a dark-mode feed if its subject is not lit hard.
- **Put it next to EP01 and EP02 before you commit.** Three thumbnails will sit in a row
  on the channel page; if any two read as the same kind of image, the later one is doing
  no work.
