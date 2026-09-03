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
`Module.onExploreCaption(text)`, which the component sets before
starting the module.

Touch devices get an on-screen D-pad (`.explore-dpad`, CSS-hidden behind
`@media (hover:hover) and (pointer:fine)` so mouse/keyboard users never
see it). Its four buttons call the exported `explore_set_touch(dir, down)`
— `dir` is 0=left, 1=right, 2=up, 3=down — which sets the same movement
flags WASD does, just from a separate touch-only set so neither input
source can clobber the other.
