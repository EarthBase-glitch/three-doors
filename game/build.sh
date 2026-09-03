#!/usr/bin/env bash
# Compiles explore.cpp to WebAssembly (explore.js + explore.wasm), loaded
# by index.html's ExploreScreen. Requires emsdk activated in PATH — see
# README.md in this directory.
set -euo pipefail
cd "$(dirname "$0")"

em++ explore.cpp -o explore.js \
  -O2 \
  -sUSE_SDL=2 \
  -sMODULARIZE=1 \
  -sEXPORT_NAME=ExploreModule \
  -sEXPORTED_FUNCTIONS=_explore_start,_explore_pause,_explore_set_touch,_main \
  -sEXPORTED_RUNTIME_METHODS=ccall,cwrap \
  -sALLOW_MEMORY_GROWTH=1 \
  -sEXIT_RUNTIME=0 \
  -sENVIRONMENT=web \
  -sSINGLE_FILE=0

echo "Built explore.js + explore.wasm"
