#!/usr/bin/env python3
"""Procedurally generates the three door SVGs (hell / earth / heaven) for
the Three Doors Hall screen — no external images, no AI-generated art,
just parametric shapes (branching cracks, an L-system tree, sunburst
rays, a diamond lattice) rendered straight to SVG path/line data."""

import math
import random

W, H = 400, 700

def svg_open(bg_id):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">'

def svg_close():
    return '</svg>'

# ---------------------------------------------------------------- Hell ---

def jagged_segment(x, y, angle, length, rng, out, width):
    """One crack segment, subdivided into a few sharp zigzag kinks —
    reads as fractured glass/rock instead of a smooth branch."""
    steps = rng.randint(2, 4)
    cx, cy, cang = x, y, angle
    for i in range(steps):
        seg_len = length / steps
        cang += rng.uniform(-0.5, 0.5)
        nx = cx + math.cos(cang) * seg_len
        ny = cy + math.sin(cang) * seg_len
        out.append((cx, cy, nx, ny, width))
        cx, cy = nx, ny
    return cx, cy, cang

def branch(x, y, angle, length, depth, rng, out, width):
    if depth <= 0 or length < 6:
        return
    x2, y2, ang2 = jagged_segment(x, y, angle, length, rng, out, width)
    n = 2 if rng.random() < 0.55 else 1
    for _ in range(n):
        a2 = ang2 + rng.choice([-1, 1]) * rng.uniform(0.35, 0.85)
        branch(x2, y2, a2, length * rng.uniform(0.55, 0.75), depth - 1, rng, out, width * 0.68)

def gen_hell():
    rng = random.Random(23)
    segs = []
    # Cracks seeded from a few points along the center seam and low on
    # each panel, branching upward/outward like heat-fractured stone.
    seeds = [(200, 640, -math.pi/2), (110, 660, -math.pi/2 - 0.3), (290, 660, -math.pi/2 + 0.3),
             (200, 420, -math.pi/2), (150, 300, -1.9), (250, 300, -1.25)]
    for (sx, sy, ang) in seeds:
        branch(sx, sy, ang, rng.uniform(60, 85), 4, rng, segs, 3.4)

    lines = []
    glow = []
    for (x1, y1, x2, y2, wd) in segs:
        glow.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#ff6a3d" stroke-width="{wd*3:.1f}" stroke-linecap="round" opacity="0.35"/>')
        lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#ffd9a8" stroke-width="{wd:.1f}" stroke-linecap="round"/>')

    blocks = ""
    for i in range(9):
        y = 40 + i * 68
        blocks += f'<rect x="14" y="{y}" width="34" height="58" rx="4" fill="#241210" stroke="#3a1f19" stroke-width="2"/>'
        blocks += f'<rect x="{W-48}" y="{y}" width="34" height="58" rx="4" fill="#241210" stroke="#3a1f19" stroke-width="2"/>'

    svg = f'''{svg_open("h")}
  <defs>
    <linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#160604"/>
      <stop offset="55%" stop-color="#2a0c08"/>
      <stop offset="100%" stop-color="#150402"/>
    </linearGradient>
    <radialGradient id="hember" cx="50%" cy="92%" r="60%">
      <stop offset="0%" stop-color="#ff8a3d" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="#ff8a3d" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#hbg)"/>
  <rect x="0" y="0" width="{W}" height="{H}" fill="url(#hember)"/>
  {blocks}
  <rect x="48" y="30" width="{W-96}" height="{H-60}" rx="10" fill="#1c0906" stroke="#40201a" stroke-width="4"/>
  <line x1="{W/2}" y1="30" x2="{W/2}" y2="{H-30}" stroke="#40201a" stroke-width="4"/>
  {"".join(glow)}
  {"".join(lines)}
  <circle cx="{W/2-14}" cy="{H*0.52}" r="5" fill="#ffb488"/>
  <circle cx="{W/2+14}" cy="{H*0.52}" r="5" fill="#ffb488"/>
{svg_close()}'''
    return svg

# --------------------------------------------------------------- Earth ---

def tree(x, y, angle, length, depth, rng, out):
    if depth <= 0 or length < 5:
        out.append(('leaf', x, y, 3 + depth))
        return
    x2 = x + math.cos(angle) * length
    y2 = y + math.sin(angle) * length
    out.append(('branch', x, y, x2, y2, max(1, depth * 0.9)))
    for _ in range(2 if depth > 2 else rng.choice([1, 2, 2])):
        a2 = angle + rng.uniform(-0.55, 0.55)
        tree(x2, y2, a2, length * rng.uniform(0.68, 0.82), depth - 1, rng, out)

def gen_earth():
    rng = random.Random(4)
    elems = []
    tree(W*0.56, 430, -math.pi/2, 62, 6, rng, elems)
    branches = ""
    leaves = ""
    for e in elems:
        if e[0] == 'branch':
            _, x1, y1, x2, y2, wd = e
            branches += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#4a3218" stroke-width="{wd:.1f}" stroke-linecap="round"/>'
        else:
            _, x, y, r = e
            leaves += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r*4:.1f}" fill="#5c8a3a" opacity="0.85"/>'

    # Vines climbing the arch border — a bezier spine with small leaves.
    vines = ""
    for side, x0 in ((1, 22), (-1, W-22)):
        py = H - 20
        d = f'M{x0},{py}'
        pts = [(x0, py)]
        y = py
        while y > 60:
            y -= rng.randint(46, 64)
            x0 = x0 + side * rng.randint(-6, 10)
            d += f' Q{x0 + side*14},{y+30} {x0},{y}'
            pts.append((x0, y))
        vines += f'<path d="{d}" fill="none" stroke="#3c6b28" stroke-width="3"/>'
        for (lx, ly) in pts[1:-1]:
            vines += f'<circle cx="{lx+side*9:.1f}" cy="{ly:.1f}" r="6" fill="#4f8a34"/>'

    # Stone arch blocks tracing the doorway.
    blocks = ""
    cx, cy, r = W/2, 230, 168
    for i in range(15):
        t = math.pi * (0.06 + 0.88 * i / 14)
        bx = cx + math.cos(math.pi - t) * r
        by = cy - math.sin(t) * r
        blocks += f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="17" fill="#2c3a26" stroke="#1b2418" stroke-width="2"/>'
    for y in range(int(cy), H-20, 40):
        blocks += f'<rect x="14" y="{y}" width="32" height="34" rx="3" fill="#2c3a26" stroke="#1b2418" stroke-width="2"/>'
        blocks += f'<rect x="{W-46}" y="{y}" width="32" height="34" rx="3" fill="#2c3a26" stroke="#1b2418" stroke-width="2"/>'

    # Path: converging trapezoid strokes toward the horizon.
    path_lines = ""
    for i in range(5):
        t = i / 4
        x1 = W*0.5 - 46*(1-t)
        x2 = W*0.5 + 46*(1-t)
        y = H*0.62 + t*(H*0.30)
        path_lines += f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" stroke="#d8cf9a" stroke-width="1.4" opacity="0.5"/>'

    svg = f'''{svg_open("e")}
  <defs>
    <linearGradient id="esky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#bfe0e6"/>
      <stop offset="45%" stop-color="#f4e3a8"/>
      <stop offset="100%" stop-color="#e8c874"/>
    </linearGradient>
    <linearGradient id="edoor" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#7a5228"/>
      <stop offset="100%" stop-color="#5a3a1c"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="#14200f"/>
  <path d="M{cx-r+18},{cy} A{r-18},{r-18} 0 0 1 {cx+r-18},{cy} L{cx+r-18},{H-20} L{cx-r+18},{H-20} Z" fill="url(#esky)"/>
  {path_lines}
  {branches}
  {leaves}
  <rect x="{cx-r+18}" y="{cy-4}" width="{r-18}" height="{H-20-cy+4}" fill="url(#edoor)"/>
  <rect x="{cx-r+18}" y="{cy-4}" width="{r-18}" height="{H-20-cy+4}" fill="none" stroke="#3a2410" stroke-width="3"/>
  <line x1="{cx-14}" y1="{cy+40}" x2="{cx-14}" y2="{H-70}" stroke="#3a2410" stroke-width="4"/>
  <circle cx="{cx-30}" cy="{H*0.62}" r="5" fill="#e8c874"/>
  {blocks}
  {vines}
{svg_close()}'''
    return svg

# -------------------------------------------------------------- Heaven ---

def gen_heaven():
    rng = random.Random(7)
    cx, cy = W/2, H*0.34
    rays = ""
    n = 28
    for i in range(n):
        ang = -math.pi/2 + (i - n/2) * (math.pi*0.9/n)
        length = rng.uniform(240, 420)
        x2 = cx + math.cos(ang) * length
        y2 = cy + math.sin(ang) * length
        rays += f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#ffffff" stroke-width="1.4" opacity="{rng.uniform(0.08,0.22):.2f}"/>'

    # Ornate ironwork: a chain of symmetric scrolls climbing each panel,
    # mirrored left/right of the seam, rather than a flat repeating grid.
    def scroll_column(x0, mirror, rng2):
        out = []
        y = H - 70
        amp = 34
        while y > 190:
            step = rng2.uniform(52, 66)
            y2 = y - step
            sx = x0 + (amp if mirror else -amp)
            out.append(f'<path d="M{x0},{y} C{sx:.1f},{y-step*0.25:.1f} {sx:.1f},{y2+step*0.25:.1f} {x0},{y2:.1f}" fill="none" stroke="#eaf6ff" stroke-width="1.6" opacity="0.75"/>')
            out.append(f'<circle cx="{x0:.1f}" cy="{(y+y2)/2:.1f}" r="4.2" fill="none" stroke="#eaf6ff" stroke-width="1.3" opacity="0.8"/>')
            out.append(f'<circle cx="{x0:.1f}" cy="{y2:.1f}" r="2.6" fill="#eaf6ff" opacity="0.9"/>')
            y = y2
        return "".join(out)

    rng_l = random.Random(3)
    rng_r = random.Random(9)
    lattice = scroll_column(W/2 - 44, False, rng_l) + scroll_column(W/2 + 44, True, rng_r)
    # A center spine of small linked circles ties the two scrolls together.
    for gy in range(190, H-60, 26):
        lattice += f'<circle cx="{W/2}" cy="{gy}" r="2.4" fill="#eaf6ff" opacity="0.7"/>'

    blocks = ""
    for i in range(9):
        y = 40 + i * 68
        blocks += f'<rect x="10" y="{y}" width="30" height="58" rx="6" fill="#3a4a58" stroke="#20303c" stroke-width="2"/>'
        blocks += f'<rect x="{W-40}" y="{y}" width="30" height="58" rx="6" fill="#3a4a58" stroke="#20303c" stroke-width="2"/>'

    svg = f'''{svg_open("hv")}
  <defs>
    <radialGradient id="hvglow" cx="50%" cy="30%" r="75%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="35%" stop-color="#dff0fb"/>
      <stop offset="100%" stop-color="#0d1b2a"/>
    </radialGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#hvglow)"/>
  {rays}
  {blocks}
  <rect x="46" y="140" width="{W-92}" height="{H-180}" rx="18" fill="#0e1c28" opacity="0.35" stroke="#cfe6f7" stroke-width="3"/>
  <line x1="{W/2}" y1="140" x2="{W/2}" y2="{H-40}" stroke="#cfe6f7" stroke-width="2" opacity="0.6"/>
  {lattice}
  <circle cx="{W/2-16}" cy="{H*0.55}" r="5" fill="#ffffff"/>
  <circle cx="{W/2+16}" cy="{H*0.55}" r="5" fill="#ffffff"/>
{svg_close()}'''
    return svg

with open('hell.svg', 'w') as f:
    f.write(gen_hell())
with open('earth.svg', 'w') as f:
    f.write(gen_earth())
with open('heaven.svg', 'w') as f:
    f.write(gen_heaven())

print("wrote hell.svg, earth.svg, heaven.svg")
