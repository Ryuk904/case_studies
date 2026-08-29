"""Operator tools. Not imported by the render path — these are the things a human runs.

    python -m pipeline.tools.solve_rate    episodes/ep01_knight_capital
    python -m pipeline.tools.sheet         --episode episodes/ep01_knight_capital
    python -m pipeline.tools.frames        episodes/ep01_knight_capital
    python -m pipeline.tools.voice_bakeoff

They live in the package rather than in scratch/ because every one of them exists to answer
a question that recurs each episode: is the pace right, do the visuals lay out, does the
finished video actually look like it should, which voice.
"""
