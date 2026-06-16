// Generates the Stenokeyboards Uni v4 layout presets for the SVG Layout Display
// plugin. The stock plugin only ships the classic split board; these draw the
// Uni's unibody-split ortholinear geometry.
//
// Emits a matrix of presets: 3 styles x {labels on/off} x {finger guides on/off}
// = 12 SVGs, plus a shared uni_convert.py. The plugin's "Layout Preset" dropdown
// (style) + "Labels" / "Finger guides" checkboxes resolve to one of these files.
//
// Plugin convention (opensteno/plover_svg_layout_display):
//   * Each physical key = two top-level <g> groups, `id` (pressed) and `id_n`
//     (neutral). convert_stroke() returns exactly one per key, so the whole
//     board is drawn and pressed keys swap to the highlight.
//   * Only top-level <g id> children survive subset rendering - no shared
//     <defs>/filters. The always-on finger-guide dots live in their own
//     <g id="guides"> that convert_stroke appends every stroke.
//
// Run:  node generate.mjs   (writes alongside this file)

import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));

// Physical keys: { steno, gid, label, row, col }. The Uni has duplicate steno
// keys (2x S-, 4x *, 2x #), so each physical cell gets its own group id and
// convert_stroke lights every copy of a pressed steno key.
const KEYS = [
  { steno: "S-", gid: "ls1", label: "S", row: 0, col: 0 },
  { steno: "S-", gid: "ls2", label: "S", row: 1, col: 0 },
  { steno: "T-", gid: "lt", label: "T", row: 0, col: 1 },
  { steno: "K-", gid: "lk", label: "K", row: 1, col: 1 },
  { steno: "P-", gid: "lp", label: "P", row: 0, col: 2 },
  { steno: "W-", gid: "lw", label: "W", row: 1, col: 2 },
  { steno: "H-", gid: "lh", label: "H", row: 0, col: 3 },
  { steno: "R-", gid: "lr", label: "R", row: 1, col: 3 },

  { steno: "*", gid: "star1", label: "*", row: 0, col: 4 },
  { steno: "*", gid: "star2", label: "*", row: 1, col: 4 },
  { steno: "*", gid: "star3", label: "*", row: 0, col: 7 },
  { steno: "*", gid: "star4", label: "*", row: 1, col: 7 },

  { steno: "-F", gid: "rf", label: "F", row: 0, col: 8 },
  { steno: "-R", gid: "rr", label: "R", row: 1, col: 8 },
  { steno: "-P", gid: "rp", label: "P", row: 0, col: 9 },
  { steno: "-B", gid: "rb", label: "B", row: 1, col: 9 },
  { steno: "-L", gid: "rl", label: "L", row: 0, col: 10 },
  { steno: "-G", gid: "rg", label: "G", row: 1, col: 10 },
  { steno: "-T", gid: "rt", label: "T", row: 0, col: 11 },
  { steno: "-S", gid: "rs", label: "S", row: 1, col: 11 },
  { steno: "-D", gid: "rd", label: "D", row: 0, col: 12 },
  { steno: "-Z", gid: "rz", label: "Z", row: 1, col: 12 },

  { steno: "#", gid: "num1", label: "#", row: 2, col: 2 },
  { steno: "A-", gid: "la", label: "A", row: 2, col: 3 },
  { steno: "O-", gid: "lo", label: "O", row: 2, col: 4 },
  { steno: "-E", gid: "re", label: "E", row: 2, col: 7 },
  { steno: "-U", gid: "ru", label: "U", row: 2, col: 8 },
  { steno: "#", gid: "num2", label: "#", row: 2, col: 9 },
];

const KEY = 12; // cap size
const PITCH = 14; // cap + gap
const M = 6; // outer margin
const R = 2.5; // corner radius
const FONT = 5.4; // label size
const BASELINE_DY = FONT * 0.35; // QtSvg ignores dominant-baseline; nudge baseline to optical centre

const COLS = 13;
const ROWS = 3;
const W = M * 2 + (COLS - 1) * PITCH + KEY;
const H = M * 2 + (ROWS - 1) * PITCH + KEY;

const xc = (col) => M + col * PITCH + KEY / 2; // cap centre x
const between = (a, b) => (xc(a) + xc(b)) / 2;
const DIV_Y = M + KEY + (PITCH - KEY) / 2; // row0/row1 divider
const THUMB_Y = M + 2 * PITCH + KEY / 2; // thumb-row centre

const ACCENT = "#f4b400";
const GUIDE_RED = "#f41933";
const DOT = 5; // finger-guide marker size
const DOT_R = 1.4;

// Finger resting positions, traced from the reference diagram: left bank on the
// S / T-K / P-W / H-R columns; right bank on the star|F junction, P-B, L-G, and
// the T|D junction; thumbs between A|O and E|U.
const GUIDES = [
  { x: xc(0), y: DIV_Y },
  { x: xc(1), y: DIV_Y },
  { x: xc(2), y: DIV_Y },
  { x: xc(3), y: DIV_Y },
  { x: between(7, 8), y: DIV_Y },
  { x: xc(9), y: DIV_Y },
  { x: xc(10), y: DIV_Y },
  { x: between(11, 12), y: DIV_Y },
  { x: between(3, 4), y: THUMB_Y },
  { x: between(7, 8), y: THUMB_Y },
];

const STYLES = {
  house: {
    neutral: { fill: "#ffffff", stroke: "#141414", strokeWidth: 1, text: "#141414" },
    pressed: { fill: ACCENT, stroke: "#141414", strokeWidth: 1, text: "#141414" },
  },
  mono: {
    neutral: { fill: "#ffffff", stroke: "#000000", strokeWidth: 1.2, text: "#000000" },
    pressed: { fill: "#000000", stroke: "#000000", strokeWidth: 1.2, text: "#ffffff" },
  },
  inverted: {
    neutral: { fill: "#26241f", stroke: "#4a4640", strokeWidth: 1, text: "#cbc6bb" },
    // Bright gold rim (not a halo): QtSvg has no blur, and translucent halos from
    // adjacent keys overlap. The rim stays inside the cap footprint - no bleed.
    pressed: { fill: ACCENT, stroke: "#ffdd72", strokeWidth: 1.4, text: "#141414" },
  },
};

function cap(k, st, showLabel) {
  const kx = M + k.col * PITCH;
  const ky = M + k.row * PITCH;
  const parts = [
    `<rect x="${kx}" y="${ky}" width="${KEY}" height="${KEY}" rx="${R}" fill="${st.fill}" stroke="${st.stroke}" stroke-width="${st.strokeWidth}"/>`,
  ];
  if (showLabel) {
    parts.push(
      `<text x="${kx + KEY / 2}" y="${ky + KEY / 2 + BASELINE_DY}" font-family="Inter, system-ui, sans-serif" font-size="${FONT}" font-weight="600" fill="${st.text}" text-anchor="middle">${k.label}</text>`,
    );
  }
  return parts.join("");
}

function guidesGroup() {
  const dots = GUIDES.map(
    (d) =>
      `<rect x="${d.x - DOT / 2}" y="${d.y - DOT / 2}" width="${DOT}" height="${DOT}" rx="${DOT_R}" fill="${GUIDE_RED}"/>`,
  ).join("");
  return `  <g id="guides">${dots}</g>`;
}

function buildSvg(styleName, labels, guides) {
  const S = STYLES[styleName];
  const groups = [];
  for (const k of KEYS) {
    groups.push(`  <g id="${k.gid}_n">${cap(k, S.neutral, labels)}</g>`);
    groups.push(`  <g id="${k.gid}">${cap(k, S.pressed, labels)}</g>`);
  }
  if (guides) groups.push(guidesGroup());
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}mm" height="${H}mm">\n${groups.join("\n")}\n</svg>\n`;
}

function buildConvert() {
  const map = new Map();
  for (const k of KEYS) {
    if (!map.has(k.steno)) map.set(k.steno, []);
    map.get(k.steno).push(k.gid);
  }
  const lines = [...map.entries()].map(
    ([steno, gids]) => `    ${JSON.stringify(steno)}: [${gids.map((g) => JSON.stringify(g)).join(", ")}],`,
  );
  return `from typing import List, Tuple

# Stenokeyboards Uni v4 - generated by resources/uni/generate.mjs.
# Maps each steno key to its physical SVG group(s); the Uni has duplicate
# physical keys (2x S-, 4x *, 2x #) so one steno key lights several caps.
# "guides" is appended every stroke; preset SVGs without finger guides simply
# lack that group and ignore it.
KEYS = {
${lines.join("\n")}
}


def convert_stroke(stroke: Tuple[str, ...], _: str) -> List[str]:
    shapes = []
    for key, gids in KEYS.items():
        pressed = key in stroke
        for gid in gids:
            shapes.append(gid if pressed else gid + "_n")
    shapes.append("guides")
    return shapes
`;
}

const written = [];
for (const styleName of Object.keys(STYLES)) {
  for (const labels of [false, true]) {
    for (const guides of [false, true]) {
      const name = `uni_${styleName}${labels ? "_labels" : ""}${guides ? "_guides" : ""}.svg`;
      writeFileSync(join(HERE, name), buildSvg(styleName, labels, guides));
      written.push(name);
    }
  }
}
writeFileSync(join(HERE, "uni_convert.py"), buildConvert());
written.push("uni_convert.py");

console.log(`Generated ${written.length} files (viewBox 0 0 ${W} ${H}):`);
for (const f of written) console.log("  " + f);
