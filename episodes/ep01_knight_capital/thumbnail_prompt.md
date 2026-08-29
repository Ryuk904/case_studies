# EP01 — thumbnail prompts for ChatGPT

Paste one of these into ChatGPT with image generation. Concept A is the recommended one.

**Three things to know before you start.**

1. ChatGPT's image tool outputs 1536×1024 (3:2), not 16:9. Generate it wide, then crop to
   1280×720. `python -m pipeline.thumbnail --fit <file>` does the crop.
2. Image models still mangle text at small sizes, and the words are the part that has to
   survive being 168px wide in the phone feed. So each concept below comes in two forms:
   **with text** (one prompt, fastest) and **art only** (generate the picture, then
   `python -m pipeline.thumbnail --compose <art.png> --top "..." --bottom "..."` lays the
   channel's own type over it, crisp and on-brand every time). Try the with-text version
   first; if the lettering comes back wonky after two attempts, switch to art-only.
3. **The palette below is the video's palette.** A warm cream thumbnail on a near-black
   episode is a bait-and-switch the viewer feels in the first second, and the first second
   is the one that decides whether they stay. Every prompt here is written for the dark
   direction on purpose — don't soften it back toward paper.

**The palette, verbatim for the prompt:** near-black `#0E1013`, off-white `#F2F0EA`,
amber `#F5A623`, one hot red `#FF4757`. Amber is the thread the eye follows; red means the
failure. Never both doing the same job in one image.

---

## Concept A — the switch *(recommended)*

The switch is the spine of the episode, it reads instantly at any size, and a light switch
next to a nine-figure number is a question the viewer wants answered.

### A — with text

> A dramatic 16:9 YouTube thumbnail illustration on a near-black background. A single old
> wall light switch, shown large and slightly off-centre to the left, photographed close and
> low so it feels monumental. The faceplate is pale bone-white and scuffed, the only bright
> object in a very dark frame. The switch is caught mid-flip, tilted, toggle just leaving the
> OFF position. A hot red glow spills from behind the faceplate and rakes across the wall in
> a hard wedge, as if something enormous just powered on inside the wall. The wall is
> near-black with faint texture, hairline cracks around the plate. Below the switch a strip
> of tape carries handwritten marker reading "2003", lit amber. The right third of the frame
> falls into near-black and stays empty for text. Large bold condensed sans-serif text in
> that empty space, stacked on two lines: "$460,000,000" in off-white, and "45 MINUTES" in
> hot red beneath it. Cinematic, extreme contrast, hard rim light from one side, deep shadow
> everywhere else. Palette strictly near-black #0E1013, off-white #F2F0EA, amber #F5A623 and
> one hot red #FF4757. Editorial illustration meets photography, no clutter. No logos, no
> brand names, no watermarks, no people.

### A — art only

> A dramatic 16:9 cinematic illustration on a near-black background, no text anywhere in the
> image. A single old wall light switch, large, positioned in the left third, shot close and
> slightly from below so it feels monumental. Pale bone-white faceplate, scuffed, the only
> bright object in a very dark frame. The switch is caught mid-flip, toggle just leaving the
> OFF position. A hot red glow spills from behind the faceplate and rakes across the wall in
> a hard wedge. Near-black wall with faint texture and hairline cracks around the plate. A
> strip of tape below the switch with handwritten marker reading "2003", lit amber. The right
> two-thirds of the frame falls into near-black and stays completely empty. Extreme contrast,
> hard rim light from one side, deep shadow everywhere else. Palette strictly near-black
> #0E1013, off-white #F2F0EA, amber #F5A623 and one hot red #FF4757. No text, no letters, no
> numbers except the taped "2003", no logos, no watermarks, no people.

Then:

```
python -m pipeline.thumbnail --compose art.png --top "$460,000,000" --bottom "45 MINUTES"
```

---

## Concept B — seven of eight

Better if you want the "spot the odd one out" instinct doing the work. Weaker than A on a
small screen because eight objects is a lot of detail to survive the crop.

> A 16:9 YouTube thumbnail illustration on a near-black background. Eight identical tall
> server cabinets in a single row, drawn in a clean bold editorial style with heavy off-white
> outlines and flat fills. Seven of them are outlined in calm off-white and perfectly
> aligned. The eighth, at the right end, is knocked out of line and outlined in hot red, with
> red light spilling onto the floor beneath it. Dramatic side lighting, long shadows, strong
> perspective, the background falling to pure near-black at the edges. Large bold condensed
> off-white sans-serif text across the top reading "7 OF 8", and smaller hot red text beneath
> it reading "$460M IN 45 MINUTES". Palette strictly near-black #0E1013, off-white #F2F0EA
> and one hot red #FF4757. Extreme contrast, poster-like, uncluttered. No logos, no brand
> names, no watermarks, no people.

---

## Concept C — the unread inbox

The most emotionally specific of the three and the most unusual in a feed of tech
thumbnails, but it needs the title to carry the stakes, since the image alone doesn't say
"money".

> A 16:9 YouTube thumbnail illustration on a near-black background. A towering, precarious
> stack of unopened envelopes filling the left half of the frame, seen close and from
> slightly below so the pile looms. The envelopes are pale bone-white, every one sealed,
> catching a single hard light from the left. The topmost envelope is stamped in hot red ink
> with a small warning triangle. The right half of the frame falls into near-black and stays
> empty. Large bold condensed sans-serif text in that empty space: "97 WARNINGS" in off-white
> and beneath it "NOBODY READ ONE" in hot red. Editorial poster style, flat but dramatic,
> extreme contrast, uncluttered. Palette strictly near-black #0E1013, off-white #F2F0EA and
> one hot red #FF4757. No logos, no brand names, no watermarks, no people.

---

## If you want to iterate

The single most useful follow-up instruction to ChatGPT is:

> Make it read at thumbnail size. Fewer objects, bigger subject, higher contrast, and push
> the text larger. Assume it will be viewed 170 pixels wide.

Others that reliably help:

- "Make the background darker and the red hotter." — models drift toward mid-grey, which is
  the one value that kills a dark thumbnail. Push it back to near-black every round.
- "Crop tighter on the switch." — almost every first draft is too wide.
- "Remove the [thing]." — image models add clutter; subtracting beats describing.

## Rules that must hold whichever you pick

- **No Knight Capital logo, no NYSE branding, no recognisable real person.** The video is
  factual reporting about a real firm; the thumbnail must not look like it was issued by
  them, and image models will refuse or invent a fake logo anyway.
- **No fabricated screenshots** of real trading terminals or news chyrons. A made-up
  interface that looks like a real one is the one thing here that could genuinely mislead.
- Text ≤ 4 words per line, 2 lines maximum.
- Check it at 168×94. If you cannot tell what the object is, the concept has failed
  regardless of how good it looks full size.
- Check it against a black phone UI, not a white desktop one. A near-black thumbnail can
  disappear into a dark-mode feed if its subject is not lit hard — that is the specific
  failure mode of this palette, and the fix is always more contrast on the subject, never a
  lighter background.
