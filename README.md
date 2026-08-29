# case_studies

Faceless YouTube channel: data-driven micro case studies of real software engineering
failures and scaling decisions. 6–10 minute visual essays, synthetic voiceover,
code-rendered diagrams. Fully automated build chain.

**Not related to `tiny_rules/`.** Separate channel, separate repo, separate pipeline.

---

## Folder map

```
case_studies/
├── README.md            ← you are here
├── HOUSE_STYLE.md       ← tone lock, word budgets, TTS writing rules, banned phrases
├── PIPELINE.md          ← how the build chain works, end to end
├── TOPICS.md            ← source-verified episode backlog
├── requirements.txt
│
├── pipeline/            ← the reusable engine (episode-independent)
│   ├── config.py        ← channel constants, palette, fonts, voice, layout
│   ├── tts.py           ← swappable TTS backend, trimming, two-stage clip cache
│   ├── script.py        ← parses script.md into beats
│   ├── sketch.py        ← hand-drawn cairo primitives (rough strokes, boxes, arrows)
│   ├── diagram.py       ← node syntax → auto-laid-out, auto-scaled diagram
│   ├── illustrate.py    ← pictorial shapes: switch, mail pile, clock, dot fields, people
│   ├── scenes.py        ← the renderers [VISUAL:] can name; all self-laying-out
│   ├── schedule.py      ← measured clip durations → frame schedule + master audio
│   ├── render.py        ← cairo frames → mp4 via imageio_ffmpeg, + frame-count verify
│   ├── sfx.py           ← synthesised pops/whooshes/thuds (no licensing)
│   ├── thumbnail.py     ← thumbnails: drawn here, or type composed over external art
│   ├── lint.py          ← enforces HOUSE_STYLE + the source ledger at build time
│   └── tools/           ← things a human runs, not part of the render path
│       ├── solve_rate.py     ← solve the speaking rate from a rendered episode
│       ├── sheet.py          ← contact sheet of scenes, before committing to a render
│       ├── frames.py         ← sample frames out of the finished mp4
│       └── voice_bakeoff.py  ← same passage, every candidate voice
│
├── episodes/
│   └── epNN_<slug>/
│       ├── research.md  ← Phase 1: hook, titles + the SOURCES ledger every number cites
│       ├── script.md    ← Phase 2+3+4: verbatim VO with inline visual/SFX directives
│       ├── seo.md       ← Phase 5: description, chapters, tags, pinned comment
│       ├── thumbnail_prompt.md  ← image-generation prompts for the thumbnail
│       ├── build.py     ← episode entry point
│       └── out/         ← episode.mp4, chapters.txt, and the vo/ clip cache
│
├── assets/
│   ├── fonts/
│   └── brand/           ← avatar, banner, channel art
└── scratch/             ← throwaway
```

## Per-episode workflow

```bash
EP=episodes/ep01_knight_capital
python -m pipeline.lint          $EP --sources # style + word budget + sources + layout
python -m pipeline.tools.sheet   --episode $EP # look at every visual before rendering
python $EP/build.py --smoke                    # every scene, ~20s, FREE
python $EP/build.py --dry                      # full length, cached audio only, FREE
python $EP/build.py              > scratch/ep01.log 2>&1    # full render — spends TTS quota
python -m pipeline.tools.frames  $EP           # sample the finished video
python -m pipeline.tools.shimmer $EP --at 30 200 450        # pixel-grid check
python -m pipeline.tools.solve_rate $EP        # confirm the delivered speaking rate
python -m pipeline.lint          $EP --timing  # 45-second rule, measured not estimated
```

**Only the un-flagged build costs anything.** `--smoke` used to synthesise the whole episode
before rendering fifteen seconds of silence, which exhausted a day of Gemini free tier on a
visual check and blocked a real render for ten hours. Cost should fall as confidence falls.
See PIPELINE.md, "The dry runs must not spend quota".

**Finish the script before the first real build.** Clips are content-addressed, so editing a
line after synthesis re-buys its batch, and inserting one re-buys every batch after it.

Then the thumbnail, once the cut is final — see `<episode>/thumbnail_prompt.md`:

```bash
python -m pipeline.thumbnail --compose art.png --top "$460,000,000" --bottom "45 minutes"
```

**Render gotcha (inherited from tiny_rules, cost hours there):** launch long renders through the
Bash tool with a shell redirect (`python build.py > log 2>&1`), never via PowerShell
`Start-Process -RedirectStandardOutput`. That redirection corrupts the child ffmpeg encoder's
stdin pipe and silently drops about half the h264 packets.

`render.run()` counts the frames in the finished mp4 and **exits non-zero** on a mismatch, so a
dropped-frame render can no longer report success. To check by hand:

```bash
ffmpeg -i out/episode.mp4 -map 0:v -f null -
```

## What is manual

1. Upload to YouTube (no API access from the pipeline).
2. Spot-check 2–3 numbers against the SOURCES ledger before publishing.
3. Watch the finished mp4 once.
