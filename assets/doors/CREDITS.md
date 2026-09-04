# Door art

`hell.svg`, `earth.svg`, `heaven.svg` — procedurally generated, not
photos or AI art. `gen_doors.py` builds all three: branching
heat-fractured cracks for Hell, a scatter of buried root veins and
glowing seeds for Reincarnation (brown soil throughout, no depicted
tree — an earlier version put a tree/sky at the top and that read as
a door drawn inside the door frame), a sunburst for Heaven. All three
carry a Flower of Life at the same height, echoing the mystery symbols
the 3D "Enter game" scenes already rotate through — earlier per-door
motifs (a triangle sigil on Hell, a hexagon rose on Heaven) were
dropped because both constructions read as a hexagram/Star of David,
which has no place there. Re-run it (`python3 gen_doors.py` from this
directory) and commit the regenerated SVGs if you want to tweak the
look.

Each SVG embeds its own `<style>` block (`ANIM_STYLE` in the script) so
the art is actually alive rather than a still image: cracks/embers
flicker, vines sway from their rooted base, clouds drift. This keeps
animating even though the SVG is only ever used as a plain CSS
`background-image` on the site's `.door-leaf` element, not inlined
into the page — confirmed by diffing two screenshots of the live site
a couple seconds apart.

Used as the door-leaf background on the Hall (door-choice) screen in
`index.html`, layered under the existing swing-open animation, glow,
and label.
