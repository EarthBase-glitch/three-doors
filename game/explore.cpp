// Three Doors — Explore
//
// A small top-down exploration area, one per realm, compiled to
// WebAssembly with Emscripten and rendered onto a <canvas> that the
// React shell (index.html) mounts inside the "explore" game phase.
//
// The realm to load is passed in from JS before the module boots
// (see explore_boot.js / the ExploreScreen component), so a single
// build serves all three doors — no rebuild needed to add realm
// content, only to change the engine itself.
//
// Movement: WASD / arrow keys. Walking onto a marker tile shows a
// short line of realm-flavored text in an on-screen caption, matching
// the terse second-person voice used everywhere else in the game
// (DAILY_TASKS, VISIONS in index.html).

#include <SDL2/SDL.h>
#include <emscripten.h>
#include <emscripten/html5.h>
#include <string>
#include <vector>
#include <cstring>
#include <cstdlib>
#include <cmath>

namespace {

constexpr int TILE = 16;
constexpr int MAP_W = 20;
constexpr int MAP_H = 14;
constexpr int SCREEN_W = MAP_W * TILE; // 320
constexpr int SCREEN_H = MAP_H * TILE; // 224
constexpr float MOVE_SPEED = 62.0f;    // px/sec

enum TileType : unsigned char { FLOOR = 0, WALL = 1 };

struct Marker {
  int x, y; // tile coords
  const char* text;
};

struct RealmMap {
  const char* key;
  unsigned char tiles[MAP_H][MAP_W];
  int startX, startY; // tile coords
  Uint8 floorR, floorG, floorB;
  Uint8 wallR, wallG, wallB;
  Uint8 playerR, playerG, playerB;
  Uint8 markerR, markerG, markerB;
  std::vector<Marker> markers;
  // Ambient particles — the thing that keeps a realm from reading as a
  // static box of walls. "Rise" realms (Hell) spawn at the bottom and
  // drift upward, recycling off the top edge; non-rise realms drift
  // gently and wrap on all four edges instead.
  Uint8 particleR, particleG, particleB, particleA;
  float particleVX, particleVY;             // base drift velocity, px/sec
  float particleVXJitter, particleVYJitter;  // +/- random spread per particle
  int particleCount;
  bool particleRise;
};

// Border walls plus a handful of interior obstacles, hand-placed per
// realm so each area reads differently even though the engine is shared.
void carveBorder(unsigned char (&t)[MAP_H][MAP_W]) {
  for (int y = 0; y < MAP_H; y++) {
    for (int x = 0; x < MAP_W; x++) {
      t[y][x] = (x == 0 || y == 0 || x == MAP_W - 1 || y == MAP_H - 1) ? WALL : FLOOR;
    }
  }
}

RealmMap makeHeaven() {
  RealmMap m;
  m.key = "heaven";
  carveBorder(m.tiles);
  // A ring of pillars around an open center.
  // Offset from the player's spawn column (x=10) so the first few steps
  // aren't an immediate wall bump — confirmed by a real playtest where a
  // symmetric {9,10},{10,10} pair sat directly in the spawn path.
  int ring[][2] = {{5,4},{14,4},{5,9},{14,9},{9,3},{10,3},{8,10},{11,10}};
  for (auto& p : ring) m.tiles[p[1]][p[0]] = WALL;
  m.startX = 10; m.startY = 12;
  m.floorR=0x17; m.floorG=0x34; m.floorB=0x47;
  m.wallR=0xbf; m.wallG=0xea; m.wallB=0xff;
  m.playerR=0xee; m.playerG=0xf9; m.playerB=0xff;
  m.markerR=0xee; m.markerG=0xf9; m.markerB=0xff;
  m.markers = {
    {10, 6, "The light here doesn't cast a shadow."},
    {5, 11, "A name you almost remember, just out of reach."},
    {14, 2, "Something up here is still being built."}
  };
  // Slow, aimless motes drifting in every direction — dust caught in light.
  m.particleR=0xee; m.particleG=0xf9; m.particleB=0xff; m.particleA=130;
  m.particleVX=0; m.particleVY=-2; m.particleVXJitter=5; m.particleVYJitter=4;
  m.particleCount=22; m.particleRise=false;
  return m;
}

RealmMap makeEarth() {
  RealmMap m;
  m.key = "earth";
  carveBorder(m.tiles);
  // A loose field of scattered rocks/rows, like tilled ground.
  int rows[][2] = {{3,3},{3,5},{3,7},{3,9},{6,3},{6,5},{6,7},{6,9},
                    {13,4},{13,6},{13,8},{16,4},{16,6},{16,8}};
  for (auto& p : rows) m.tiles[p[1]][p[0]] = WALL;
  m.startX = 10; m.startY = 11;
  m.floorR=0x1c; m.floorG=0x31; m.floorB=0x17;
  m.wallR=0x7f; m.wallG=0xc2; m.wallB=0x6a;
  m.playerR=0xc7; m.playerG=0xf0; m.playerB=0xb8;
  m.markerR=0xc7; m.markerG=0xf0; m.markerB=0xb8;
  m.markers = {
    {4, 6, "The soil is soft here — something was buried and dug back up."},
    {17, 6, "A row that doesn't match the others. Someone planted it by hand."},
    {10, 2, "Footprints, going one direction only."}
  };
  // Pollen/dust drifting sideways with a faint downward settle.
  m.particleR=0xc7; m.particleG=0xf0; m.particleB=0xb8; m.particleA=110;
  m.particleVX=4; m.particleVY=3; m.particleVXJitter=6; m.particleVYJitter=2;
  m.particleCount=18; m.particleRise=false;
  return m;
}

RealmMap makeHell() {
  RealmMap m;
  m.key = "hell";
  carveBorder(m.tiles);
  // A cramped, maze-ish layout — narrower paths than the other two realms.
  int walls[][2] = {
    {4,2},{4,3},{4,4},{4,5},{4,6},
    {8,11},{8,10},{8,9},{8,8},{8,7},
    {12,2},{12,3},{12,4},{12,5},
    {15,11},{15,10},{15,9},{15,8}
  };
  for (auto& p : walls) m.tiles[p[1]][p[0]] = WALL;
  m.startX = 2; m.startY = 2;
  m.floorR=0x43; m.floorG=0x11; m.floorB=0x0b;
  m.wallR=0xff; m.wallG=0x6a; m.wallB=0x3d;
  m.playerR=0xff; m.playerG=0xb4; m.playerB=0x88;
  m.markerR=0xff; m.markerG=0xb4; m.markerB=0x88;
  m.markers = {
    {17, 2, "The fire is quieter in the corners. That's not comfort — it's aim."},
    {2, 11, "Something was scratched into the wall here, then burned away."},
    {10, 6, "A voice, close by, that stops the moment you turn toward it."}
  };
  // Embers rising from the floor, flickering side to side as they go.
  m.particleR=0xff; m.particleG=0x8a; m.particleB=0x3d; m.particleA=200;
  m.particleVX=0; m.particleVY=-26; m.particleVXJitter=8; m.particleVYJitter=10;
  m.particleCount=16; m.particleRise=true;
  return m;
}

RealmMap g_map;
SDL_Window* g_window = nullptr;
SDL_Renderer* g_renderer = nullptr;

float g_px, g_py; // player position, pixel coords (top-left of 12x12 sprite)
constexpr int PLAYER_SIZE = 12;

bool g_keyLeft=false, g_keyRight=false, g_keyUp=false, g_keyDown=false;
// Set from JS by the on-screen D-pad (see explore_set_touch), kept
// separate from the keyboard flags above so the two input sources never
// clobber each other — movement is just whichever ORs true.
bool g_touchLeft=false, g_touchRight=false, g_touchUp=false, g_touchDown=false;

std::string g_caption;
int g_captionMarkerIdx = -1;

double g_lastTime = 0;
bool g_paused = false;
float g_time = 0;          // seconds, accumulated — drives all animation
int g_facingDir = 0;       // 0=down, 1=up, 2=left, 3=right; for the player's facing dot
bool g_randSeeded = false;

struct Particle { float x, y, vx, vy; };
std::vector<Particle> g_particles;

float randSpread(float jitter) {
  if (jitter <= 0) return 0;
  return ((rand() % 2001) / 1000.0f - 1.0f) * jitter; // -jitter..+jitter
}

void populateParticles(const RealmMap& m) {
  g_particles.clear();
  g_particles.reserve(m.particleCount);
  for (int i = 0; i < m.particleCount; i++) {
    Particle p;
    p.x = (float)(rand() % SCREEN_W);
    p.y = (float)(rand() % SCREEN_H);
    p.vx = m.particleVX + randSpread(m.particleVXJitter);
    p.vy = m.particleVY + randSpread(m.particleVYJitter);
    g_particles.push_back(p);
  }
}

void updateParticles(float dt) {
  for (auto& p : g_particles) {
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    if (g_map.particleRise) {
      // Recycle off the top back to the bottom with a fresh random x —
      // keeps embers looking like a continuous rise, not a fixed set.
      if (p.y < -4) {
        p.y = (float)(SCREEN_H + (rand() % 8));
        p.x = (float)(rand() % SCREEN_W);
      }
    } else {
      if (p.x < -4) p.x = SCREEN_W + 4;
      else if (p.x > SCREEN_W + 4) p.x = -4;
      if (p.y < -4) p.y = SCREEN_H + 4;
      else if (p.y > SCREEN_H + 4) p.y = -4;
    }
  }
}

bool tileSolid(int tx, int ty) {
  if (tx < 0 || ty < 0 || tx >= MAP_W || ty >= MAP_H) return true;
  return g_map.tiles[ty][tx] == WALL;
}

bool rectHitsWall(float x, float y) {
  // Check the four corners of the player's bounding box against the tile grid.
  float corners[4][2] = {
    {x, y}, {x + PLAYER_SIZE - 1, y},
    {x, y + PLAYER_SIZE - 1}, {x + PLAYER_SIZE - 1, y + PLAYER_SIZE - 1}
  };
  for (auto& c : corners) {
    int tx = (int)(c[0] / TILE);
    int ty = (int)(c[1] / TILE);
    if (tileSolid(tx, ty)) return true;
  }
  return false;
}

void updateMarkerCaption() {
  int centerTx = (int)((g_px + PLAYER_SIZE / 2) / TILE);
  int centerTy = (int)((g_py + PLAYER_SIZE / 2) / TILE);
  for (size_t i = 0; i < g_map.markers.size(); i++) {
    if (g_map.markers[i].x == centerTx && g_map.markers[i].y == centerTy) {
      if (g_captionMarkerIdx != (int)i) {
        g_captionMarkerIdx = (int)i;
        g_caption = g_map.markers[i].text;
        // Second arg is the marker index — the JS side uses it to know
        // which of the three per-realm "Enter game" 3D scenes to load.
        EM_ASM({ if (Module.onExploreCaption) Module.onExploreCaption(UTF8ToString($0), $1); }, g_caption.c_str(), (int)i);
      }
      return;
    }
  }
  if (g_captionMarkerIdx != -1) {
    g_captionMarkerIdx = -1;
    g_caption.clear();
    EM_ASM({ if (Module.onExploreCaption) Module.onExploreCaption("", -1); });
  }
}

void fillRect(int x, int y, int w, int h, Uint8 r, Uint8 g, Uint8 b, Uint8 a = 255) {
  SDL_SetRenderDrawColor(g_renderer, r, g, b, a);
  SDL_Rect rc = { x, y, w, h };
  SDL_RenderFillRect(g_renderer, &rc);
}

void render() {
  SDL_SetRenderDrawColor(g_renderer, g_map.floorR, g_map.floorG, g_map.floorB, 255);
  SDL_RenderClear(g_renderer);

  for (auto& p : g_particles) {
    fillRect((int)p.x, (int)p.y, 2, 2, g_map.particleR, g_map.particleG, g_map.particleB, g_map.particleA);
  }

  for (int ty = 0; ty < MAP_H; ty++) {
    for (int tx = 0; tx < MAP_W; tx++) {
      if (g_map.tiles[ty][tx] == WALL) {
        fillRect(tx * TILE, ty * TILE, TILE, TILE, g_map.wallR, g_map.wallG, g_map.wallB);
      }
    }
  }

  // Markers pulse gently (out of phase with each other) so the world feels
  // like it's breathing rather than just sitting there waiting to be found.
  for (size_t i = 0; i < g_map.markers.size(); i++) {
    auto& mk = g_map.markers[i];
    int cx = mk.x * TILE + TILE / 2;
    int cy = mk.y * TILE + TILE / 2;
    int half = 2 + (int)(2.0f * (0.5f + 0.5f * sinf(g_time * 3.0f + (float)i * 2.1f)));
    fillRect(cx - half, cy - half, half * 2, half * 2, g_map.markerR, g_map.markerG, g_map.markerB);
  }

  // The player idles with a slow breathing bob and picks up a snappier,
  // more pronounced one while actually moving — the same sprite either
  // way, just animated instead of a dead square.
  bool moving = g_keyLeft || g_keyRight || g_keyUp || g_keyDown ||
                g_touchLeft || g_touchRight || g_touchUp || g_touchDown;
  float bob = sinf(g_time * (moving ? 9.0f : 2.2f)) * (moving ? 1.6f : 0.8f);
  int py = (int)(g_py + bob);
  fillRect((int)g_px, py, PLAYER_SIZE, PLAYER_SIZE, g_map.playerR, g_map.playerG, g_map.playerB);

  // A small facing dot, in the floor color for contrast against the
  // (always light) player fill — cheap, but it's the difference between
  // "a square" and "a character that's looking somewhere."
  int fx = (int)g_px, fy = py;
  switch (g_facingDir) {
    case 0: fx += PLAYER_SIZE / 2 - 2; fy += PLAYER_SIZE - 4; break; // down
    case 1: fx += PLAYER_SIZE / 2 - 2; fy += 2; break;               // up
    case 2: fx += 2; fy += PLAYER_SIZE / 2 - 2; break;               // left
    default: fx += PLAYER_SIZE - 6; fy += PLAYER_SIZE / 2 - 2; break; // right
  }
  fillRect(fx, fy, 4, 4, g_map.floorR, g_map.floorG, g_map.floorB);

  SDL_RenderPresent(g_renderer);
}

void mainLoop() {
  double now = emscripten_get_now();
  float dt = g_lastTime > 0 ? (float)((now - g_lastTime) / 1000.0) : 0.0f;
  if (dt > 0.05f) dt = 0.05f; // clamp after tab-away hitches
  g_lastTime = now;
  g_time += dt;

  float dx = 0, dy = 0;
  if (g_keyLeft || g_touchLeft) dx -= 1;
  if (g_keyRight || g_touchRight) dx += 1;
  if (g_keyUp || g_touchUp) dy -= 1;
  if (g_keyDown || g_touchDown) dy += 1;
  if (dx != 0 || dy != 0) {
    float len = SDL_sqrtf(dx * dx + dy * dy);
    dx /= len; dy /= len;
    g_facingDir = fabsf(dx) >= fabsf(dy) ? (dx > 0 ? 3 : 2) : (dy > 0 ? 0 : 1);
    float nx = g_px + dx * MOVE_SPEED * dt;
    float ny = g_py + dy * MOVE_SPEED * dt;
    if (!rectHitsWall(nx, g_py)) g_px = nx;
    if (!rectHitsWall(g_px, ny)) g_py = ny;
    updateMarkerCaption();
  }

  updateParticles(dt);
  render();
}

EM_BOOL onKey(int eventType, const EmscriptenKeyboardEvent* e, void*) {
  bool down = eventType == EMSCRIPTEN_EVENT_KEYDOWN;
  bool handled = true;
  if (!strcmp(e->code, "KeyA") || !strcmp(e->code, "ArrowLeft")) g_keyLeft = down;
  else if (!strcmp(e->code, "KeyD") || !strcmp(e->code, "ArrowRight")) g_keyRight = down;
  else if (!strcmp(e->code, "KeyW") || !strcmp(e->code, "ArrowUp")) g_keyUp = down;
  else if (!strcmp(e->code, "KeyS") || !strcmp(e->code, "ArrowDown")) g_keyDown = down;
  else handled = false;
  return handled ? EM_TRUE : EM_FALSE;
}

RealmMap mapForKey(const std::string& key) {
  if (key == "heaven") return makeHeaven();
  if (key == "hell") return makeHell();
  return makeEarth();
}

} // namespace

extern "C" {

// Called once from JS right after the module is instantiated, with the
// realm key ("heaven" | "earth" | "hell") chosen on the site.
EMSCRIPTEN_KEEPALIVE
void explore_start(const char* realmKey) {
  if (!g_randSeeded) {
    srand((unsigned)emscripten_get_now());
    g_randSeeded = true;
  }
  g_map = mapForKey(realmKey ? std::string(realmKey) : std::string("earth"));
  g_px = g_map.startX * TILE + (TILE - PLAYER_SIZE) / 2.0f;
  g_py = g_map.startY * TILE + (TILE - PLAYER_SIZE) / 2.0f;
  g_captionMarkerIdx = -1;
  g_caption.clear();
  g_lastTime = 0;
  g_time = 0;
  g_facingDir = 0;
  g_keyLeft = g_keyRight = g_keyUp = g_keyDown = false;
  g_touchLeft = g_touchRight = g_touchUp = g_touchDown = false;
  populateParticles(g_map);

  if (!g_window) {
    SDL_Init(SDL_INIT_VIDEO);
    g_window = SDL_CreateWindow("explore", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED,
                                 SCREEN_W, SCREEN_H, SDL_WINDOW_SHOWN);
    g_renderer = SDL_CreateRenderer(g_window, -1, SDL_RENDERER_ACCELERATED);
    SDL_SetRenderDrawBlendMode(g_renderer, SDL_BLENDMODE_BLEND);
    // Bound to the canvas itself (not the window) so WASD/arrows only
    // move the character while the canvas has focus — otherwise typing
    // in the lore textarea or character name field elsewhere on the
    // site would get eaten by this module every time it's mounted.
    emscripten_set_keydown_callback("#explore-canvas", nullptr, EM_TRUE, onKey);
    emscripten_set_keyup_callback("#explore-canvas", nullptr, EM_TRUE, onKey);
    // simulate_infinite_loop=0: this is called from a plain ccall'd
    // function, not from main(), so the loop must be registered via
    // requestAnimationFrame and return normally rather than unwinding
    // the stack (which is only safe to do from within main()).
    emscripten_set_main_loop(mainLoop, 0, 0);
  } else if (g_paused) {
    emscripten_resume_main_loop();
    g_paused = false;
  }
}

// Stops the render/input loop without tearing down the SDL window, so
// leaving the Explore screen (React unmounts ExploreScreen on phase
// change) doesn't keep spending CPU on a hidden canvas. explore_start()
// resumes it and reloads whichever realm is passed in.
EMSCRIPTEN_KEEPALIVE
void explore_pause() {
  if (g_window && !g_paused) {
    emscripten_pause_main_loop();
    g_paused = true;
  }
}

// Driven by the on-screen D-pad for touch devices (see the .explore-dpad
// buttons in ExploreScreen). dir: 0=left, 1=right, 2=up, 3=down.
// down: 1 while pressed, 0 on release — the JS side calls this on every
// pointerup/pointerleave/pointercancel too, so a finger dragging off a
// button can't leave movement stuck on.
EMSCRIPTEN_KEEPALIVE
void explore_set_touch(int dir, int down) {
  bool v = down != 0;
  switch (dir) {
    case 0: g_touchLeft = v; break;
    case 1: g_touchRight = v; break;
    case 2: g_touchUp = v; break;
    case 3: g_touchDown = v; break;
    default: break;
  }
}

} // extern "C"

int main() {
  // The React shell calls explore_start() explicitly once it knows which
  // realm to load, so main() just keeps the runtime alive without
  // starting a render loop of its own.
  return 0;
}
