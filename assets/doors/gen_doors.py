#!/usr/bin/env python3
"""Door art for the Hall (door-choice) screen — 100% code, no photos,
no AI images. SVG filters do the work that used to need a painter:
feTurbulence for noise/grain instead of flat color fields, feGaussianBlur
for glow and soft depth, layered blurred shapes for foliage/cloud/embers.
CSS @keyframes (ANIM_STYLE, embedded directly in each SVG) keep it
actually alive rather than a still image — cracks flicker, vines sway
from their rooted base, clouds drift — and keep animating even though
the SVG is only ever used as a plain CSS background-image on the site's
own .door-leaf element, not inlined into the page."""

import math
import random

W, H = 400, 700

FILTERS = '''
    <filter id="glowSoft" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="6"/>
    </filter>
    <filter id="glowTight" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="2.2"/>
    </filter>
    <filter id="softBlur" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="5"/>
    </filter>
    <filter id="grainStone" x="-10%" y="-10%" width="120%" height="120%">
      <feTurbulence type="fractalNoise" baseFrequency="0.012 0.02" numOctaves="4" seed="7" result="n"/>
      <feColorMatrix in="n" type="matrix"
        values="0.15 0.15 0.15 0 0.62  0.15 0.15 0.15 0 0.62  0.15 0.15 0.15 0 0.62  0 0 0 0 1" result="ng"/>
      <feComposite in="ng" in2="SourceAlpha" operator="in" result="grain"/>
      <feBlend in="SourceGraphic" in2="grain" mode="multiply"/>
    </filter>
    <filter id="grainWood" x="-10%" y="-10%" width="120%" height="120%">
      <feTurbulence type="fractalNoise" baseFrequency="0.008 0.09" numOctaves="3" seed="3" result="n"/>
      <feColorMatrix in="n" type="matrix"
        values="0.12 0.12 0.12 0 0.68  0.12 0.12 0.12 0 0.68  0.12 0.12 0.12 0 0.68  0 0 0 0 1" result="ng"/>
      <feComposite in="ng" in2="SourceAlpha" operator="in" result="grain"/>
      <feBlend in="SourceGraphic" in2="grain" mode="multiply"/>
    </filter>
'''

# CSS animation continues to run when an SVG is used as a plain CSS
# background-image (this is the one embedded in each door's <svg>, not
# a filter) — kept as one shared block so all three doors' motion reads
# as the same "living world" language the rest of the site already has
# (particle drift in the 2D explore area, rotating symbols in the 3D
# scenes) rather than three unrelated effects.
ANIM_STYLE = '''
  <style>
    .ember, .crackglow{ animation-name:flicker; animation-timing-function:ease-in-out; animation-iteration-count:infinite; }
    @keyframes flicker{ 0%,100%{opacity:var(--lo)} 50%{opacity:var(--hi)} }
    .vine{ animation-name:sway; animation-timing-function:ease-in-out; animation-iteration-count:infinite; transform-box:fill-box; }
    @keyframes sway{ 0%,100%{transform:rotate(-2.2deg)} 50%{transform:rotate(2.2deg)} }
    .cloud{ animation-name:drift; animation-timing-function:ease-in-out; animation-iteration-count:infinite; }
    @keyframes drift{ 0%,100%{transform:translateX(-7px)} 50%{transform:translateX(7px)} }
  </style>
'''

def svg_open():
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">'

def svg_close():
    return '</svg>'

def soft_blob(cx, cy, rx, ry, color, opacity, blur='glowSoft', extra=''):
    return f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{color}" opacity="{opacity}" filter="url(#{blur})" {extra}/>'

# ---------------------------------------------------------- Sacred geometry ---
# Flower of Life on all three doors, same height on each — echoing the
# mystery symbols the 3D "Enter game" scenes already rotate through.
# (An earlier pass gave each door its own motif — a triangle-based
# "sigil" on Hell, a hexagon compass-rose on Heaven — but both of those
# constructions turned out to read as a hexagram/Star of David, which
# has no place on a Hell door or scattered around decoratively, so
# they were dropped rather than reworked.)

def sg_hexpoints(cx, cy, r, rot=0.0):
    return [(cx + r*math.cos(rot + i*math.pi/3), cy + r*math.sin(rot + i*math.pi/3)) for i in range(6)]

def sg_flower_of_life(cx, cy, r, color):
    """Center circle + one ring of six, classic seed/flower-of-life
    layout — organic, fits Earth's growth-and-return theme."""
    out = [f'<circle cx="{cx}" cy="{cy}" r="{r*1.5:.1f}" fill="none" stroke="{color}" stroke-width="1.2" opacity="0.35"/>']
    centers = [(cx, cy)] + sg_hexpoints(cx, cy, r)
    for (x, y) in centers:
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="none" stroke="{color}" stroke-width="1.6" opacity="0.6" filter="url(#glowTight)"/>')
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="none" stroke="{color}" stroke-width="0.7" opacity="0.8"/>')
    return "".join(out)

# ---------------------------------------------------------------- Hell ---

def jagged_segment(x, y, angle, length, rng, out, width):
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
    seeds = [(200, 640, -math.pi/2), (110, 660, -math.pi/2 - 0.3), (290, 660, -math.pi/2 + 0.3),
             (200, 420, -math.pi/2), (150, 300, -1.9), (250, 300, -1.25)]
    for (sx, sy, ang) in seeds:
        branch(sx, sy, ang, rng.uniform(60, 85), 4, rng, segs, 3.4)

    glow, bloom, core = [], [], []
    for (x1, y1, x2, y2, wd) in segs:
        d = rng.uniform(0, 2.4)
        bloom.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#ff7a3d" stroke-width="{wd*4:.1f}" stroke-linecap="round" filter="url(#glowSoft)" class="crackglow" style="--lo:0.3;--hi:0.6;animation-duration:{rng.uniform(1.8,2.6):.2f}s;animation-delay:{d:.2f}s"/>')
        glow.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#ffb066" stroke-width="{wd*1.8:.1f}" stroke-linecap="round" filter="url(#glowTight)" class="crackglow" style="--lo:0.55;--hi:0.9;animation-duration:{rng.uniform(1.8,2.6):.2f}s;animation-delay:{d:.2f}s"/>')
        core.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#fff3e0" stroke-width="{wd*0.55:.1f}" stroke-linecap="round"/>')

    # Scattered embers, flickering like heat/sparks off the cracks.
    embers = []
    for _ in range(26):
        ex = rng.uniform(40, W-40)
        ey = rng.uniform(60, H-40)
        r = rng.uniform(1.2, 3.2)
        dur = rng.uniform(1.1, 2.2)
        delay = rng.uniform(0, 2.2)
        embers.append(
            f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{r:.1f}" fill="#ffb066" filter="url(#glowTight)" '
            f'class="ember" style="--lo:0.25;--hi:0.9;animation-duration:{dur:.2f}s;animation-delay:{delay:.2f}s"/>'
        )

    blocks = ""
    for i in range(9):
        y = 40 + i * 68
        blocks += f'<rect x="14" y="{y}" width="34" height="58" rx="4" fill="#2c1410" stroke="#4a2418" stroke-width="2" filter="url(#grainStone)"/>'
        blocks += f'<rect x="{W-48}" y="{y}" width="34" height="58" rx="4" fill="#2c1410" stroke="#4a2418" stroke-width="2" filter="url(#grainStone)"/>'

    svg = f'''{svg_open()}{ANIM_STYLE}
  <defs>
    {FILTERS}
    <linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0d0302"/>
      <stop offset="35%" stop-color="#220a06"/>
      <stop offset="68%" stop-color="#3a1108"/>
      <stop offset="100%" stop-color="#170502"/>
    </linearGradient>
    <radialGradient id="hember" cx="50%" cy="94%" r="65%">
      <stop offset="0%" stop-color="#ff8a3d" stop-opacity="0.6"/>
      <stop offset="45%" stop-color="#a83a12" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="#ff8a3d" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#hbg)"/>
  {blocks}
  <rect width="{W}" height="{H}" fill="url(#hember)"/>
  {"".join(bloom)}
  {"".join(glow)}
  {"".join(core)}
  {"".join(embers)}
  {sg_flower_of_life(W/2, H*0.5, 30, "#ff9d5c")}
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
    cx, cy, r = W/2, 230, 168
    # No tree, no sky — the whole door is soil/wood brown, same
    # "texture the full surface" approach as Hell and Heaven, just the
    # earth-toned version of it. A scatter of independent root veins
    # (not attached to any visible trunk) breaks up the brown instead.
    roots = ""
    for _ in range(5):
        rx = cx + rng.uniform(-(r-50), r-50)
        ry = rng.uniform(cy-r+40, H-90)
        rlen = []
        branch(rx, ry, rng.uniform(0, math.pi*2), rng.uniform(26, 40), 3, rng, rlen, 2.2)
        for (x1, y1, x2, y2, wd) in rlen:
            roots += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#5c4322" stroke-width="{wd*0.7:.1f}" stroke-linecap="round" opacity="0.55"/>'
    seeds = ""
    for _ in range(9):
        sx = cx + rng.uniform(-(r-40), r-40)
        sy = rng.uniform(cy-r+50, H-50)
        seeds += f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="3.4" fill="#e8d98a" opacity="{rng.uniform(0.5,0.9):.2f}" filter="url(#glowTight)"/>'

    vines = ""
    for vi, (side, x0) in enumerate(((1, 22), (-1, W-22))):
        py = H - 20
        base_x, base_y = x0, py  # pivot for the sway animation — rooted at the ground
        d = f'M{x0},{py}'
        pts = [(x0, py)]
        y = py
        while y > 60:
            y -= rng.randint(46, 64)
            x0 = x0 + side * rng.randint(-6, 10)
            d += f' Q{x0 + side*14},{y+30} {x0},{y}'
            pts.append((x0, y))
        leaves = ""
        for (lx, ly) in pts[1:-1]:
            leaves += f'<ellipse cx="{lx+side*9:.1f}" cy="{ly:.1f}" rx="8" ry="5.5" fill="#4f8a34"/>'
        vines += (
            f'<g class="vine" style="transform-origin:{base_x}px {base_y}px;'
            f'animation-duration:{3.4+vi*0.6:.1f}s;animation-delay:{vi*0.5:.1f}s">'
            f'<path d="{d}" fill="none" stroke="#2f5a1e" stroke-width="3.5"/>{leaves}</g>'
        )

    blocks = ""
    for i in range(15):
        t = math.pi * (0.06 + 0.88 * i / 14)
        bx = cx + math.cos(math.pi - t) * r
        by = cy - math.sin(t) * r
        blocks += f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="17" fill="#33421f" stroke="#1e2812" stroke-width="2" filter="url(#grainStone)"/>'
    for y in range(int(cy), H-20, 40):
        blocks += f'<rect x="14" y="{y}" width="32" height="34" rx="3" fill="#33421f" stroke="#1e2812" stroke-width="2" filter="url(#grainStone)"/>'
        blocks += f'<rect x="{W-46}" y="{y}" width="32" height="34" rx="3" fill="#33421f" stroke="#1e2812" stroke-width="2" filter="url(#grainStone)"/>'

    door_shape = f'M{cx-r+18},{cy} A{r-18},{r-18} 0 0 1 {cx+r-18},{cy} L{cx+r-18},{H-20} L{cx-r+18},{H-20} Z'
    svg = f'''{svg_open()}{ANIM_STYLE}
  <defs>
    {FILTERS}
    <linearGradient id="esoil" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#5a4423"/>
      <stop offset="55%" stop-color="#4a3a1c"/>
      <stop offset="100%" stop-color="#241a0c"/>
    </linearGradient>
    <radialGradient id="evign" cx="50%" cy="20%" r="85%">
      <stop offset="0%" stop-color="#0a1206" stop-opacity="0"/>
      <stop offset="100%" stop-color="#0a1206" stop-opacity="0.5"/>
    </radialGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="#0f1a0a"/>
  <path d="{door_shape}" fill="url(#esoil)" filter="url(#grainWood)"/>
  {roots}
  {seeds}
  {sg_flower_of_life(cx, H*0.5, 30, "#cddc9a")}
  {blocks}
  {vines}
  <path d="{door_shape}" fill="url(#evign)"/>
{svg_close()}'''
    return svg

# -------------------------------------------------------------- Heaven ---

def gen_heaven():
    rng = random.Random(7)
    cx, cy = W/2, H*0.34
    rays_bloom, rays = [], []
    n = 26
    for i in range(n):
        ang = -math.pi/2 + (i - n/2) * (math.pi*0.9/n)
        length = rng.uniform(240, 420)
        x2 = cx + math.cos(ang) * length
        y2 = cy + math.sin(ang) * length
        rays_bloom.append(f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#ffffff" stroke-width="5" opacity="{rng.uniform(0.05,0.12):.2f}" filter="url(#glowSoft)"/>')
        rays.append(f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#ffffff" stroke-width="1.2" opacity="{rng.uniform(0.1,0.28):.2f}"/>')

    # Cloud bank across the bottom, standing-above-the-world feel —
    # each blob drifts side to side on its own timing.
    clouds = ""
    for i in range(10):
        cx2 = rng.uniform(0, W)
        cy2 = H - rng.uniform(10, 70)
        rx = rng.uniform(50, 110)
        style = f'class="cloud" style="animation-duration:{rng.uniform(5,9):.1f}s;animation-delay:{rng.uniform(0,4):.1f}s"'
        clouds += soft_blob(cx2, cy2, rx, rx*0.45, "#ffffff", rng.uniform(0.5, 0.85), 'softBlur', style)

    blocks = ""
    for i in range(9):
        y = 40 + i * 68
        blocks += f'<rect x="10" y="{y}" width="30" height="58" rx="6" fill="#3a4a58" stroke="#20303c" stroke-width="2" filter="url(#grainStone)"/>'
        blocks += f'<rect x="{W-40}" y="{y}" width="30" height="58" rx="6" fill="#3a4a58" stroke="#20303c" stroke-width="2" filter="url(#grainStone)"/>'

    svg = f'''{svg_open()}{ANIM_STYLE}
  <defs>
    {FILTERS}
    <radialGradient id="hvglow" cx="50%" cy="20%" r="65%">
      <stop offset="0%" stop-color="#eef8ff"/>
      <stop offset="20%" stop-color="#c3ddef"/>
      <stop offset="50%" stop-color="#5f7d94"/>
      <stop offset="100%" stop-color="#0c1822"/>
    </radialGradient>
    <linearGradient id="hvbody" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#22374a" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#0a141c" stop-opacity="0.75"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#hvglow)"/>
  {"".join(rays_bloom)}
  {"".join(rays)}
  <rect width="{W}" height="{H}" fill="url(#hvbody)"/>
  {blocks}
  {sg_flower_of_life(W/2, H*0.5, 30, "#eaf6ff")}
  {clouds}
{svg_close()}'''
    return svg

with open('hell.svg', 'w') as f:
    f.write(gen_hell())
with open('earth.svg', 'w') as f:
    f.write(gen_earth())
with open('heaven.svg', 'w') as f:
    f.write(gen_heaven())

print("wrote hell.svg, earth.svg, heaven.svg")
