"""Parse script.md into an ordered list of beats.

Everything before the first `## SECTION:` marker is front-matter and is ignored, so an
episode file can carry as much explanatory prose at the top as it likes without any of it
leaking into the voiceover. That rule is what lets episodes/_template/script.md document
itself and still parse correctly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

SECTIONS = ("hook", "context", "breakdown", "takeaway")

_RE_SECTION = re.compile(r"^##\s*SECTION:\s*(\w+)\s*$", re.I)
_RE_VISUAL = re.compile(r"^\[VISUAL:\s*(\w+)\s*(.*?)\s*\]$", re.I)
_RE_PAUSE = re.compile(r"^\[PAUSE:\s*([\d.]+)\s*\]$", re.I)
_RE_SFX = re.compile(r"^\[SFX:\s*([\w-]+)\s*\]$", re.I)
_RE_PARAM = re.compile(r'(\w+)\s*=\s*"([^"]*)"')
_RE_COMMENT = re.compile(r"^(<!--|-->|#|\||```)")


@dataclass
class Visual:
    renderer: str
    params: dict[str, str] = field(default_factory=dict)

    def get(self, key: str, default: str = "") -> str:
        return self.params.get(key, default)

    def num(self, key: str, default: float = 0.0) -> float:
        try:
            return float(self.params[key])
        except (KeyError, ValueError):
            return default


@dataclass
class Beat:
    kind: str                      # "speak" | "pause" | "sfx"
    section: str
    visual: Visual | None
    text: str = ""                 # speak
    seconds: float = 0.0           # pause
    name: str = ""                 # sfx
    line_no: int = 0


@dataclass
class Script:
    beats: list[Beat]
    path: Path

    @property
    def spoken(self) -> list[Beat]:
        return [b for b in self.beats if b.kind == "speak"]

    def words_by_section(self) -> dict[str, int]:
        out = {s: 0 for s in SECTIONS}
        for b in self.spoken:
            out[b.section] = out.get(b.section, 0) + len(b.text.split())
        return out


def parse(path: Path) -> Script:
    beats: list[Beat] = []
    section = ""
    visual: Visual | None = None
    started = False
    n_visuals = 0

    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue

        if m := _RE_SECTION.match(line):
            section, started = m.group(1).lower(), True
            continue

        # Front-matter: nothing counts until the first SECTION marker.
        if not started or _RE_COMMENT.match(line):
            continue

        if m := _RE_VISUAL.match(line):
            params = dict(_RE_PARAM.findall(m.group(2)))
            # Stamp the section onto the visual. Renderers colour-key off it — each section
            # gets its own field colour so chapters are visible — and a Visual is otherwise
            # handed to scenes.render() with no idea where in the episode it sits.
            params.setdefault("section", section)
            # Ordinal position in the episode. Layout alternation keys off this rather than
            # off a hash of the title: a hash is deterministic but clumpy, and on EP01 it
            # produced eight consecutive left-aligned headlines — a long enough stretch to
            # read as the fixed layout the alternation exists to break up.
            params.setdefault("ord", str(n_visuals))
            # Where this script lives, so a renderer can load a sidecar file. Param values
            # are delimited by double quotes, which means any literal text containing one
            # cannot be written inline at all — and the thing EP02 has to put on screen is a
            # regular expression containing both kinds of quote. Rather than escape-encode
            # the param grammar, a renderer can name a file next to the episode, which also
            # keeps episode content out of pipeline/.
            params.setdefault("_dir", str(path.parent))
            n_visuals += 1
            visual = Visual(m.group(1).lower(), params)
            continue
        if m := _RE_PAUSE.match(line):
            beats.append(Beat("pause", section, visual,
                              seconds=float(m.group(1)), line_no=line_no))
            continue
        if m := _RE_SFX.match(line):
            beats.append(Beat("sfx", section, visual, name=m.group(1), line_no=line_no))
            continue
        if line.startswith("[") and line.endswith("]"):
            raise ValueError(f"{path.name}:{line_no}: unrecognised directive {line!r}")

        beats.append(Beat("speak", section, visual, text=line, line_no=line_no))

    return Script(beats=beats, path=path)
