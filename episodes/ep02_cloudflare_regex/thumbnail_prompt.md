# EP02 — thumbnail prompts for ChatGPT

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

**The EP01 problem this has to avoid.** EP01's thumbnail is a lit object on a dark wall.
Two of those in a row on a channel page look like the same video twice. Concept A is
deliberately a *different kind of image* — typographic and architectural rather than a
single lit prop.

---

## Concept A — the line that broke the floor *(recommended)*

The episode's whole idea in one picture: a single line of text, and the enormous thing
resting on it giving way. It reads at 168px because there are exactly two elements.

### A — with text

> A dramatic 16:9 illustration on a near-black background. A single thin horizontal line of
> dense monospace code runs across the lower third of the frame, glowing hot amber, tiny
> against the scale of the image. The line is buckling downward at its centre under an
> enormous weight, sagging like a cable about to part, with hairline fractures of hot red
> light splitting outward from the sag. Resting on top of that one line is a vast dark
> architectural slab that fills the upper two-thirds of the frame, its underside catching
> faint amber rim light, its bulk disappearing into blackness at the top. The slab is
> featureless and heavy, like the underside of a bridge deck. Deep shadow everywhere,
> extreme contrast, a single hard light source from the lower left. Large bold condensed
> off-white sans-serif text in the dark space in the upper right, stacked on two lines:
> "132 CHARACTERS" in off-white, and "27 MINUTES" in hot red beneath it. Palette strictly
> near-black #0E1013, off-white #F2F0EA, amber #F5A623 and one hot red #FF4757. Cinematic
> editorial illustration, no clutter. No logos, no brand names, no watermarks, no people,
> no readable words inside the code line.

### A — art only

> A dramatic 16:9 cinematic illustration on a near-black background, no text anywhere. A
> single thin horizontal line of dense monospace code runs across the lower third of the
> frame, glowing hot amber, tiny against the scale of the image, and it is buckling downward
> at its centre under an enormous weight, sagging like a cable about to part, with hairline
> fractures of hot red light splitting outward from the sag. Resting on that one line is a
> vast dark architectural slab filling the upper two-thirds of the frame, its underside
> catching faint amber rim light, its bulk disappearing into blackness. Featureless, heavy,
> like the underside of a bridge deck. The right third of the frame falls into pure
> near-black and stays completely empty. Deep shadow, extreme contrast, single hard light
> from the lower left. Palette strictly near-black #0E1013, off-white #F2F0EA, amber #F5A623
> and one hot red #FF4757. No text, no letters, no numbers, no logos, no watermarks, no
> people.

Then:

```
python -m pipeline.thumbnail --compose art.png --top "132 CHARACTERS" --bottom "27 MINUTES"
```

---

## Concept B — the wall of 502s

The literal symptom, and the most immediately legible of the three. Weaker than A because a
grid of small rectangles loses its detail at phone size, so it needs the red to be violent.

> A 16:9 YouTube thumbnail illustration on a near-black background. A dense grid of small
> browser windows fills the frame in strong perspective, receding toward the upper right.
> Almost every window is blown out in hot red and shows a stark error state; three or four
> scattered windows remain calm off-white and intact, and they are the only cool colour in
> the image. Hard red light spills between the windows and pools in the gaps. Extreme
> contrast, poster-like, the edges of the frame falling to pure near-black. Large bold
> condensed off-white sans-serif text across the top left reading "80% GONE", and smaller
> hot red text beneath it reading "IN 27 MINUTES". Palette strictly near-black #0E1013,
> off-white #F2F0EA and one hot red #FF4757. Uncluttered, no clutter in the corners. No
> logos, no brand names, no watermarks, no people.

---

## Concept C — the missing bar

The one that carries the actual lesson rather than the symptom. Best long-tail thumbnail,
worst cold-open thumbnail, because a viewer has to think for half a second.

> A 16:9 cinematic illustration on a near-black background. A heavy row of thick vertical
> steel bars runs across the whole frame like a barrier, lit hard from the left in cold
> off-white. One bar in the centre-left is missing, snapped off, leaving bright torn stubs
> at the top and bottom of the gap. A blazing hot red sphere is caught in mid-flight exactly
> in that gap, trailing a comet-like streak of red light behind it, passing cleanly through
> the one place the barrier does not exist. Deep shadow, volumetric red glow around the
> sphere, extreme contrast. Large bold condensed off-white sans-serif text in the dark upper
> right reading "THE GUARD WAS GONE", and beneath it in hot red "SO WAS 80% OF THE INTERNET".
> Palette strictly near-black #0E1013, off-white #F2F0EA, amber #F5A623 and one hot red
> #FF4757. No logos, no brand names, no watermarks, no people.

---

## If you want to iterate

The single most useful follow-up instruction to ChatGPT is:

> Make it read at thumbnail size. Fewer objects, bigger subject, higher contrast, and push
> the text larger. Assume it will be viewed 170 pixels wide.

Others that reliably help:

- "Make the background darker and the red hotter." — models drift toward mid-grey, which is
  the one value that kills a dark thumbnail. Push it back to near-black every round.
- "Make the slab heavier and the line thinner." — for Concept A the whole idea is the ratio
  between the two, and first drafts always under-sell it.
- "Remove the [thing]." — image models add clutter; subtracting beats describing.

## Rules that must hold whichever you pick

- **No Cloudflare logo, no orange cloud, no recognisable real person.** This is factual
  reporting about a real company; the thumbnail must not look like it was issued by them,
  and image models will refuse or invent a fake logo anyway.
- **No fabricated screenshots** of a real dashboard, status page, or news chyron. A made-up
  interface that looks like a real one is the one thing here that could genuinely mislead.
- **No real regular expression rendered as legible text.** Concept A's code line is texture,
  not content — if the model produces readable characters, ask for "illegible dense code
  texture, no readable characters". A thumbnail is not a source citation and nobody can
  check it.
- Text ≤ 4 words per line, 2 lines maximum.
- Check it at 168×94. If you cannot tell what the object is, the concept has failed
  regardless of how good it looks full size.
- Check it against a black phone UI, not a white desktop one. A near-black thumbnail can
  disappear into a dark-mode feed if its subject is not lit hard — that is the specific
  failure mode of this palette, and the fix is always more contrast on the subject, never a
  lighter background.
- **Put it next to the EP01 thumbnail before you commit.** They will sit side by side on the
  channel page for the life of the channel, and if both are "one lit object on a dark wall"
  the second one is doing no work.
