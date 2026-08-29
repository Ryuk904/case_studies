# script.md — Phase 2 + 3 + 4 in one file

This file is the single source of truth for the render. `visuals.md` is generated from it,
so the voiceover and the picture can never drift apart.

Rules (full list in HOUSE_STYLE.md §5–6):
- One sentence per line. Blank line between beats.
- No em-dashes, no parentheses in spoken lines.
- `[VISUAL:]` holds until the next `[VISUAL:]`.
- Every number spoken here must exist in research.md → SOURCES.

---

## SECTION: hook

[VISUAL: metric_card value="$460,000,000" sub="45 minutes" ]
On August 1st, 2012, Knight Capital lost $460 million in 45 minutes.
[PAUSE:0.9]

[VISUAL: diagram nodes="[NYSE] --(orders)--> [SMARS] --(routes)--> [8 servers]" ]
The cause was not a bad algorithm and not a hardware failure.
It was a deployment that reached seven of its eight servers.
[SFX: thud]

## SECTION: context

[VISUAL: timeline from="2003" to="2012" marks="Power Peg written|2005 check moved|Jul 2012 RLP deploy" ]
To understand what the eighth server did, you have to go back nine years.

## SECTION: breakdown

[VISUAL: code lang="text" highlight=3 body="if (flag_set) {\n    // 2012: call RLP\n    powerPeg.execute(order);\n}" ]
The flag that once switched on Power Peg was now the flag that switched on the new code.

## SECTION: takeaway

[VISUAL: title_card text="delete dead code the day you retire it" ]
Dead code is not inert.
It is a loaded gun with a nine-year fuse.

[VISUAL: end_card next="the regex that took down Cloudflare" ]
If you want the next one, it is about the regular expression that cost Cloudflare 80% of its traffic.
Subscribe and it will show up.
