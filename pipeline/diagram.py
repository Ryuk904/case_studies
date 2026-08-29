"""Node syntax -> laid-out, drawn diagram.

    [Client] --(HTTP POST)--> [Load Balancer] --(SQL)--> [DB Primary]

Chains are separated by `;` and stack vertically. A node repeated in a later chain is the
same node, so branching and fan-out work without any extra syntax:

    [SMARS] --> [server 1..7]; [SMARS] --(same flag)--> [server 8]

This module only computes geometry and calls sketch.py. It has no idea what a server is.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

import cairo

from . import config, sketch

# Matches BOTH `-->` and `--(label)-->`, yielding one entry per arrow so labels line up
# with arrow positions. The earlier pattern could only match the labelled form, so in a
# chain mixing the two, findall() returned fewer labels than arrows and every label after
# the first unlabelled edge attached to the wrong arrow.
#
# Note the trailing `--` lives INSIDE the optional group: `--(x)-->` is dash dash, the
# parenthesised label, dash dash, then `>`. Putting it outside (`--(?:\(...\))?->`) fails
# to match either form.
_RE_EDGE = re.compile(r"--(?:\(([^)]*)\)--)?>")
_RE_NODE = re.compile(r"\[([^\]]+)\]")

BOX_PAD_X = 30.0
BOX_PAD_Y = 22.0
BOX_MIN_W = 150.0
GAP_X = 110.0
GAP_Y = 60.0


@dataclass
class Node:
    label: str
    col: int
    row: int
    x: float = 0.0
    y: float = 0.0
    w: float = 0.0
    h: float = 0.0

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2


@dataclass
class Edge:
    src: str
    dst: str
    label: str = ""


@dataclass
class Graph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    label_size: float = config.SZ_LABEL   # set by layout() once the scale is known

    @property
    def order(self) -> list[Node]:
        """Reveal order: left to right, then top to bottom."""
        return sorted(self.nodes.values(), key=lambda n: (n.col, n.row))


def parse(spec: str) -> Graph:
    g = Graph()
    for row, chain in enumerate(s for s in spec.split(";") if s.strip()):
        labels = [m.strip() for m in _RE_NODE.findall(chain)]
        edge_labels = _RE_EDGE.findall(chain)
        for label in labels:
            if label not in g.nodes:
                g.nodes[label] = Node(label=label, col=0, row=row)
        for i in range(len(labels) - 1):
            lbl = edge_labels[i] if i < len(edge_labels) else ""
            g.edges.append(Edge(labels[i], labels[i + 1], (lbl or "").strip()))

    _assign_columns(g)

    # Resolve grid collisions: two nodes layered into the same cell would draw at
    # identical coordinates, one invisibly on top of the other.
    occupied: dict[tuple[int, int], str] = {}
    for node in g.nodes.values():
        while (node.col, node.row) in occupied:
            node.row += 1
        occupied[(node.col, node.row)] = node.label
    return g


def _back_edges(g: Graph) -> set[int]:
    """Indices of edges that close a cycle, found by DFS.

    A feedback loop like `[venues] --(fills)--> [Power Peg]` points backwards on purpose.
    Layering it as a forward edge shoves Power Peg to the right of venues and the diagram
    reads as a straight line instead of a loop.
    """
    adj: dict[str, list[tuple[str, int]]] = {k: [] for k in g.nodes}
    for i, e in enumerate(g.edges):
        if e.src in adj and e.dst in g.nodes:
            adj[e.src].append((e.dst, i))

    back: set[int] = set()
    state: dict[str, int] = {}          # 0 unvisited, 1 on stack, 2 done

    def visit(u: str) -> None:
        state[u] = 1
        for v, idx in adj[u]:
            if state.get(v, 0) == 1:
                back.add(idx)           # v is an ancestor: this edge closes a cycle
            elif state.get(v, 0) == 0:
                visit(v)
        state[u] = 2

    for node in g.nodes:
        if state.get(node, 0) == 0:
            visit(node)
    return back


def _assign_columns(g: Graph) -> None:
    """Longest-path layering over forward edges: col(dst) >= col(src) + 1."""
    back = _back_edges(g)
    forward = [e for i, e in enumerate(g.edges) if i not in back]

    for _ in range(len(g.nodes) + 1):    # relax until stable; bounded by node count
        changed = False
        for e in forward:
            if e.src not in g.nodes or e.dst not in g.nodes:
                continue
            want = g.nodes[e.src].col + 1
            if g.nodes[e.dst].col < want:
                g.nodes[e.dst].col = want
                changed = True
        if not changed:
            break


MAX_SCALE = 2.4   # beyond this a 3-node diagram becomes absurd billboard lettering
MIN_SCALE = 0.55  # below this the labels are unreadable; the diagram wants splitting


def layout(ctx: cairo.Context, g: Graph, *, box: tuple[float, float, float, float] | None = None,
           scale: float = 1.0) -> tuple[float, float]:
    """Size every node to its text, centre the graph in `box`, return the total extent.

    `scale` multiplies type and spacing together so the diagram grows as a whole. Scaling
    the cairo matrix instead would scale stroke widths too and the sketch lines would go
    fat and cartoonish at 2x.
    """
    lbl = config.SZ_LABEL * scale
    cap = config.SZ_CAPTION * scale
    pad_x, pad_y = BOX_PAD_X * scale, BOX_PAD_Y * scale
    gap_y = GAP_Y * scale
    g.label_size = lbl

    for n in g.nodes.values():
        tw, th = sketch.text_size(ctx, n.label, lbl, config.FONT_LABEL)
        n.w = max(BOX_MIN_W * scale, tw + pad_x * 2)
        n.h = th + pad_y * 2

    cols = sorted({n.col for n in g.nodes.values()})
    rows = sorted({n.row for n in g.nodes.values()})
    col_w = {c: max(n.w for n in g.nodes.values() if n.col == c) for c in cols}
    row_h = {r: max(n.h for n in g.nodes.values() if n.row == r) for r in rows}

    # Size each column gap to the widest edge label that has to sit in it. A fixed gap is
    # the reason labels printed straight through the boxes: "$3.5bn in 80 stocks" is far
    # wider than 110px, so it spilled over the node on each side.
    gap_after: dict[int, float] = {c: GAP_X * scale for c in cols}
    for e in g.edges:
        if not e.label or e.src not in g.nodes or e.dst not in g.nodes:
            continue
        a, b = g.nodes[e.src], g.nodes[e.dst]
        if a.col == b.col:
            continue                      # vertical edge; label sits beside it, not between
        lo = min(a.col, b.col)
        need = sketch.text_size(ctx, e.label, cap, config.FONT_SANS)[0] + 46 * scale
        span = abs(a.col - b.col)
        # A label crossing several columns only needs its share of each gap.
        gap_after[lo] = max(gap_after.get(lo, 0.0), need / span)

    total_w = sum(col_w.values()) + sum(gap_after.get(c, 0.0) for c in cols[:-1])
    total_h = sum(row_h.values()) + gap_y * (len(rows) - 1)

    bx, by, bw, bh = box or (config.SAFE, config.SAFE,
                             config.W - config.SAFE * 2, config.H - config.SAFE * 2)
    ox = bx + (bw - total_w) / 2
    oy = by + (bh - total_h) / 2

    col_x, acc = {}, ox
    for c in cols:
        col_x[c], acc = acc, acc + col_w[c] + gap_after.get(c, 0.0)
    row_y, acc = {}, oy
    for r in rows:
        row_y[r], acc = acc, acc + row_h[r] + gap_y

    for n in g.nodes.values():
        n.x = col_x[n.col] + (col_w[n.col] - n.w) / 2
        n.y = row_y[n.row] + (row_h[n.row] - n.h) / 2

    # Centre every node against what it feeds, working right to left so the adjustment
    # propagates back up the tree. Doing this only for multi-target nodes left the node
    # UPSTREAM of a fan-out stranded on row 0, with its arrow raking diagonally down.
    #
    # Per column, though, it has to be all-or-nothing: when several nodes CONVERGE on one
    # target they all centre on the same y and stack invisibly on top of each other. So
    # centre a column only if the result leaves its nodes disjoint, else keep the grid.
    for col in sorted({n.col for n in g.nodes.values()}, reverse=True):
        peers = [x for x in g.nodes.values() if x.col == col]
        saved = {id(n): n.y for n in peers}
        for n in peers:
            targets = [g.nodes[e.dst] for e in g.edges
                       if e.src == n.label and e.dst in g.nodes
                       and g.nodes[e.dst].col > n.col]
            if not targets:
                continue
            top = min(t.y for t in targets)
            bottom = max(t.y + t.h for t in targets)
            n.y = (top + bottom) / 2 - n.h / 2

        ordered = sorted(peers, key=lambda n: n.y)
        clash = any(ordered[i].y + ordered[i].h + 12 > ordered[i + 1].y
                    for i in range(len(ordered) - 1))
        if clash:
            for n in peers:
                n.y = saved[id(n)]

    return total_w, total_h


def _hits_any_node(g: Graph, cx: float, cy: float, w: float, h: float,
                   skip: tuple[str, ...] = ()) -> bool:
    """Would a label centred at (cx, cy) overlap a node box other than its own endpoints?"""
    x0, x1 = cx - w / 2 - 6, cx + w / 2 + 6
    y0, y1 = cy - h / 2 - 6, cy + h / 2 + 6
    for n in g.nodes.values():
        if n.label in skip:
            continue
        if x1 > n.x and x0 < n.x + n.w and y1 > n.y and y0 < n.y + n.h:
            return True
    return False


def _edge_ends(a: Node, b: Node) -> tuple[float, float, float, float]:
    """Anchor an arrow on the facing edges of two boxes, not their centres."""
    if abs(a.cy - b.cy) < 1e-6 or a.col != b.col:
        if b.cx > a.cx:
            return a.x + a.w, a.cy, b.x, b.cy
        return a.x, a.cy, b.x + b.w, b.cy
    if b.cy > a.cy:
        return a.cx, a.y + a.h, b.cx, b.y
    return a.cx, a.y, b.cx, b.y + b.h


def draw(ctx: cairo.Context, spec: str, *, highlight: str = "", dim: str = "",
         reveal: float = 1.0, box: tuple[float, float, float, float] | None = None,
         flow_phase: float | None = None, flow_only: bool = True,
         nib: bool = True) -> Graph:
    """Draw the diagram.

    highlight   comma-separated node labels drawn in the failure accent
    dim         comma-separated node labels drawn muted
    reveal      0..1 — draw-on progress across the whole figure, element by element
    flow_phase  0..1 looping phase for dots travelling the edges, or None for none
    flow_only   restrict flow dots to edges touching a highlighted node
    nib         park a pen at the point currently being drawn while reveal < 1
    """
    g = parse(spec)
    bx, by, bw, bh = box or (config.SAFE, config.SAFE,
                             config.W - config.SAFE * 2, config.H - config.SAFE * 2)

    # Grow the diagram to fill its box. Sizing purely to text leaves a 4-node graph
    # marooned in the middle of a 1080p frame, which is what the first preview showed.
    nat_w, nat_h = layout(ctx, g, box=box)
    s = min(bw * 0.94 / max(nat_w, 1), bh * 0.88 / max(nat_h, 1))
    # Clamping the lower bound to 1.0 means an oversized diagram is never shrunk and
    # simply draws off the edge of the frame. Shrinking must be allowed; only the upper
    # bound is a style choice.
    s = min(s, MAX_SCALE)
    if s < MIN_SCALE:
        print(f"[diagram] WARN: {len(g.nodes)} nodes need scale {s:.2f}; "
              f"clamped to {MIN_SCALE}. Split this diagram.")
        s = MIN_SCALE
    if abs(s - 1.0) > 0.01:
        layout(ctx, g, box=box, scale=s)

    hot = {s_.strip() for s_ in highlight.split(",") if s_.strip()}
    cold = {s_.strip() for s_ in dim.split(",") if s_.strip()}

    # Build a draw order that alternates node, then the edges leaving it, so the diagram
    # is traced the way a person would draw it on a board rather than materialising.
    order = g.order
    items: list[tuple[str, object]] = []
    placed: set[int] = set()
    drawn: set[str] = set()
    for n in order:
        items.append(("node", n))
        drawn.add(n.label)
        # An edge may only be drawn once BOTH of its boxes exist. Emitting it as soon as
        # its source appeared drew arrows into empty space, pointing at a box that had
        # not been drawn yet.
        for i, e in enumerate(g.edges):
            if i in placed:
                continue
            if e.src in drawn and e.dst in drawn:
                items.append(("edge", e))
                placed.add(i)
    for i, e in enumerate(g.edges):          # anything left over (dangling endpoints)
        if i not in placed and e.src in g.nodes and e.dst in g.nodes:
            items.append(("edge", e))

    n_items = max(1, len(items))
    span = 1.0 / n_items

    def item_progress(i: int) -> float:
        return max(0.0, min(1.0, (reveal - i * span) / span))

    # Count edges per unordered node pair so bidirectional links can be separated. Drawn
    # naively, A->B and B->A share a midpoint and their labels print on top of each other.
    pair_total: dict[frozenset[str], int] = {}
    for e in g.edges:
        key = frozenset((e.src, e.dst))
        pair_total[key] = pair_total.get(key, 0) + 1
    pair_seen: dict[frozenset[str], int] = {}

    def edge_geometry(e: Edge) -> tuple[float, float, float, float, float, float, float, bool]:
        a, b = g.nodes[e.src], g.nodes[e.dst]
        x1, y1, x2, y2 = _edge_ends(a, b)
        key = frozenset((e.src, e.dst))
        bidir = pair_total[key] > 1
        length = math.hypot(x2 - x1, y2 - y1) or 1.0
        px, py = -(y2 - y1) / length, (x2 - x1) / length   # perpendicular unit vector
        # The perpendicular already flips for the return edge of a bidirectional pair, so
        # alternating a per-edge sign on top of it would cancel the flip and stack both
        # labels in the same place. One constant sign; direction does the separating.
        side = 1.0 if bidir else -1.0   # -1 keeps single edges labelled above / right
        if bidir:
            shift = 15.0 * s * side
            x1, y1, x2, y2 = (x1 + px * shift, y1 + py * shift,
                              x2 + px * shift, y2 + py * shift)
        return x1, y1, x2, y2, px, py, side, bidir

    sketch.reset_tip()

    for idx, (kind, obj) in enumerate(items):
        p = item_progress(idx)
        if p <= 0.0:
            continue

        if kind == "node":
            n: Node = obj                                        # type: ignore[assignment]
            if n.label in hot:
                pen, ink = sketch.FAIL_PEN, config.FAIL
            elif n.label in cold:
                pen, ink = sketch.MUTED_PEN, config.MUTED
            else:
                pen, ink = sketch.INK_PEN, config.INK
            sketch.rect(ctx, n.x, n.y, n.w, n.h, pen,
                        fill=config.BG_DEEP if n.label in hot else None, fill_alpha=0.5,
                        overshoot=4.0 * s, progress=p)
            _, th = sketch.text_size(ctx, n.label, g.label_size, config.FONT_LABEL)
            # Label lags the box slightly: the outline is drawn, then written into.
            sketch.text(ctx, n.label, n.cx, n.cy + th / 2, g.label_size,
                        ink, config.FONT_LABEL, align="center",
                        progress=max(0.0, min(1.0, (p - 0.45) / 0.55)))
        else:
            e: Edge = obj                                        # type: ignore[assignment]
            x1, y1, x2, y2, px, py, side, bidir = edge_geometry(e)
            pen = sketch.FAIL_PEN if (e.dst in hot or e.src in hot) else sketch.MUTED_PEN
            sketch.arrow(ctx, x1, y1, x2, y2, pen, head=16.0 * s, progress=p)
            if e.label:
                cap = config.SZ_CAPTION * s
                gap = cap * (1.15 if bidir else 0.95)
                lw, lh_ = sketch.text_size(ctx, e.label, cap, config.FONT_SANS)
                # Slide the label along the edge until it clears every box. A diagonal
                # edge's midpoint is often sitting on top of an unrelated node, which is
                # how "never arrived" ended up printed across "machines 3 to 7".
                best = 0.5
                for frac in (0.5, 0.36, 0.64, 0.26, 0.74, 0.18, 0.82):
                    cxp = x1 + (x2 - x1) * frac + px * gap * side
                    cyp = y1 + (y2 - y1) * frac + py * gap * side
                    if not _hits_any_node(g, cxp, cyp, lw, lh_, skip=(e.src, e.dst)):
                        best = frac
                        break
                lx = x1 + (x2 - x1) * best + px * gap * side
                ly = y1 + (y2 - y1) * best + py * gap * side + cap * 0.34
                sketch.text(ctx, e.label, lx, ly, cap, config.MUTED, config.FONT_SANS,
                            align="center",
                            progress=max(0.0, min(1.0, (p - 0.5) / 0.5)))

    # Dots travelling the finished edges. Only once everything is drawn, so the motion
    # reads as "this system is running" rather than competing with the drawing itself.
    if flow_phase is not None and reveal >= 0.999:
        for e in g.edges:
            if e.src not in g.nodes or e.dst not in g.nodes:
                continue
            if flow_only and not (e.src in hot or e.dst in hot):
                continue
            x1, y1, x2, y2, *_ = edge_geometry(e)
            colour = config.FAIL if (e.src in hot or e.dst in hot) else config.MUTED
            sketch.flow(ctx, x1, y1, x2, y2, flow_phase, colour, radius=7.0 * s)

    if nib and 0.0 < reveal < 1.0 and sketch.TIP is not None:
        sketch.pen_nib(ctx, sketch.TIP[0], sketch.TIP[1], scale=max(1.0, s * 0.9))

    return g
