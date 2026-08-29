# EPnn — thumbnail prompts

Written **last**, once the cut is final. The thumbnail is the only asset that depends on the
finished video rather than the other way round, and a title that survived the edit is a
better guide to it than the one in research.md.

Two things to know:

1. ChatGPT's image tool outputs 1536×1024 (3:2), not 16:9. Crop it with
   `python -m pipeline.thumbnail --fit <file>`.
2. Image models still mangle small text, and the words have to survive being 170px wide in a
   phone feed. So write each concept twice — **with text** (one prompt, fastest) and **art
   only**, where `python -m pipeline.thumbnail --compose art.png --top "..." --bottom "..."`
   lays the channel's own type over it. Try with-text first; switch after two bad attempts.

---

## Concept A — <the object at the centre of the story>

The strongest concept is usually the episode's central metaphor as a physical object, next
to the number. An object raises a question the number alone does not.

### A — with text

> A dramatic 16:9 YouTube thumbnail illustration. <SUBJECT>, shown large in the left third,
> photographed close and slightly from below so it feels monumental. <THE MOMENT OF
> FAILURE, described physically.> Warm cream background with visible texture, deep shadow to
> the right. Large bold condensed sans-serif text in the empty right third, stacked on two
> lines: "<BIG NUMBER>" in white, and "<TIME SPAN>" in bright red. Cinematic, high contrast,
> strong rim lighting, shallow depth of field. Palette limited to warm cream, deep charcoal,
> and one saturated red. No logos, no brand names, no watermarks, no people.

### A — art only

> Same as above, minus the two text lines, plus: "no text, no letters, no numbers anywhere
> in the image", and "the right two-thirds falls off into deep warm shadow and stays
> completely empty".

---

## Concept B — <the odd one out>

Use when the failure is one element differing from many identical ones. Weaker at small
sizes: many objects means each is tiny.

---

## Concept C — <the human detail>

Use when the story's most memorable beat is an ignored warning, an unread message, an alarm
nobody heard. Most distinctive in a feed; needs the title to carry the stakes.

---

## Iterating

> Make it read at thumbnail size. Fewer objects, bigger subject, higher contrast, and push
> the text larger. Assume it will be viewed 170 pixels wide.

- "Make the red hotter and everything else more desaturated." — one colour should win.
- "Crop tighter." — almost every first draft is too wide.
- "Remove the [thing]." — subtracting beats describing.

## Rules

- **No real company logo, no recognisable real person.** These episodes are factual reporting
  about real firms; the thumbnail must not look like it was issued by one.
- **No fabricated screenshots** of real terminals, dashboards or news chyrons. An invented
  interface that looks genuine is the one thing here that could actually mislead.
- Text ≤ 4 words per line, 2 lines maximum.
- Check it at 168×94. If the subject is unreadable, the concept failed.
