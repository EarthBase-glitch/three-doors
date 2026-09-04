# Explore area (C++ / WebAssembly)

`explore.cpp` is a small top-down exploration area — one map per realm —
compiled to WebAssembly and rendered onto a `<canvas>` from the
"Explore" screen in `index.html`. `explore.js` and `explore.wasm` are
the build output; both are committed so the site works without anyone
needing the C++ toolchain to just run it.

## Rebuilding

You only need to rebuild if you change `explore.cpp`.

1. Install [Emscripten](https://emscripten.org/docs/getting_started/downloads.html)
   (requires Python 3.10+):
   ```
   git clone https://github.com/emscripten-core/emsdk.git
   cd emsdk && ./emsdk install latest && ./emsdk activate latest
   source ./emsdk_env.sh
   ```
2. From this directory: `./build.sh`

That regenerates `explore.js` and `explore.wasm` — commit both.

## How it's wired into the site

`index.html`'s `ExploreScreen` component loads `game/explore.js` once
(a MODULARIZE build exposing a global `ExploreModule` factory), then
calls `ExploreModule({ canvas })` to get an independent module instance
per visit, bound to that visit's `<canvas id="explore-canvas">`. It then
calls the exported `explore_start(realmKey)` to load the right map.
`explore_pause()` is called when the screen unmounts so the render loop
doesn't keep running against a detached canvas.

Marker text (the short flavor lines shown when you walk onto a glowing
dot) is pushed from C++ back up to React through
`Module.onExploreCaption(text, markerIdx)`, which the component sets
before starting the module. `markerIdx` (0/1/2, which marker in the
realm) is what picks the right one of the nine "Enter game" 3D scenes —
see below.

Touch devices get an on-screen D-pad (`.explore-dpad`, CSS-hidden behind
`@media (hover:hover) and (pointer:fine)` so mouse/keyboard users never
see it). Its four buttons call the exported `explore_set_touch(dir, down)`
— `dir` is 0=left, 1=right, 2=up, 3=down — which sets the same movement
flags WASD does, just from a separate touch-only set so neither input
source can clobber the other.

## The "Enter game" 3D scenes are not part of this wasm module

Standing on a marker in the 2D area surfaces an "Enter game" button.
Clicking it goes to a completely separate system: `Explore3DScreen` in
`index.html`, rendered with [three.js](https://threejs.org/) (loaded
from cdnjs, pinned to r128) — plain JS, not C++/wasm. Bridging a full
3D renderer through Emscripten would fight the library instead of using
it, so the 2D area (this directory) and the 3D scenes are two
independent engines that just happen to live in the same file.

The nine scenes (3 markers × 3 realms) are hand-authored data in the
`SCENE3D` object — sky/fog/floor colors, a lighting setup, a small list
of primitive props (boxes/spheres/cones/cylinders with position, scale,
color), and a particle style — the same "one engine, many hand-placed
maps" pattern as `DAILY_TASKS`/`VISIONS`/the 2D realm maps elsewhere in
this project. Two scenes (`heaven:2`) also carry `backdrop` / `floorTexture`
— real, license-verified images loaded via `THREE.TextureLoader` instead
of a solid color (see `game/textures/heaven/CREDITS.md`). No external 3D
*models*; everything is procedural geometry. Movement is drag-to-look +
WASD/D-pad with simple room-boundary clamping (no per-prop collision yet).

## Every scene also shifts on its own, outside player control

`TIME_PHASES` (dawn/day/dusk/night, keyed off the visitor's local clock
via `getTimePhase()`) retints each scene's sky/fog/ambient light and
nudges particle opacity — applied uniformly in `Explore3DScreen`, not
authored per scene. Separately, each scene's `mysterySpot` gets one of
four procedurally-built sacred-geometry symbols (`buildFlowerOfLife`,
`buildTreeOfLife`, `buildMerkaba`, `buildMetatronsCube` — no external
assets, just primitives arranged into the real pattern each symbol
actually has), picked by `dayOfYear()` the same way `DAILY_TASKS`
rotates, tinted to that scene's own light color. Both are deliberately
outside the player's control — the point is you can't know what a scene
looks like right now without going to look.
