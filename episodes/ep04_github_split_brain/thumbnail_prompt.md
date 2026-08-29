# EP04 — thumbnail prompt for ChatGPT

One prompt, with text baked in (HOUSE_STYLE §12, "Publishing assets, trimmed"). Generate
wide, then crop to 1280×720 with `python -m pipeline.thumbnail --fit <file>`. If the
lettering comes back mangled twice, strip the text clause and lay type with
`python -m pipeline.thumbnail --compose art.png --top "43 SECONDS" --bottom "24 HOURS DOWN"`.

**Channel-page note.** EP01 is a lit object on a dark wall, EP02 a typographic line under
a slab, EP03 a row of five objects with a count. This one is a *single object torn in
two* — a fourth kind of image; the tear is the subject.

---

> A dramatic 16:9 cinematic illustration on a near-black background. A single tall
> ledger book drawn in clean off-white outline, standing upright in the centre, torn
> violently in half down the middle. The two halves lean away from each other, and the
> jagged tear between them glows hot red, the only strong light in the image. Inside the
> left half, a few faint lines of illegible handwriting texture; inside the right half,
> many dense lines of illegible handwriting texture in warm amber, as if the two halves
> kept being written separately. Hard light from the upper left, long shadows, vast empty
> darkness above. Large bold condensed off-white sans-serif text in the upper left,
> stacked on two lines: "43 SECONDS" in off-white, and "24 HOURS DOWN" in hot red beneath
> it. Extreme contrast, poster-like, cinematic editorial illustration, no clutter.
> Palette strictly near-black #0E1013, off-white #F2F0EA, amber #F5A623 and one hot red
> #FF4757. No logos, no brand names, no watermarks, no people, no readable small text
> anywhere.

## Binding rules

- Palette locked to the video's: near-black `#0E1013`, off-white `#F2F0EA`, amber
  `#F5A623`, one hot red `#FF4757`. Amber = the thread, red = the failure — never both
  doing the same job.
- ChatGPT outputs 1536×1024 (3:2); crop to 16:9 with `pipeline.thumbnail --fit`, never
  letterbox.
- **No GitHub logo, no Octocat, no recognisable real person.** Factual reporting about a
  real company; the image must not look issued by them.
- **No fabricated screenshots** of a real dashboard, status page or console, and no
  readable command text — code or writing in the image is texture, "illegible", always.
- Text ≤ 4 words per line, 2 lines maximum.
- Check it at 168×94 against a dark-mode phone feed, and put it NEXT TO EP01–EP03 on the
  channel page before committing — if it reads as any of their three kinds of image, it
  is doing no work.
