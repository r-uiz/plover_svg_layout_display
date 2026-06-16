# CLAUDE.md

Ruiz's **fork** of [`opensteno/plover_svg_layout_display`](https://github.com/opensteno/plover_svg_layout_display)
- a Plover tool that floats an SVG of the last stroke over other windows. The
fork adds **Stenokeyboards Uni v4** layouts (upstream only ships the classic
split board) plus a few quality-of-life features. Ruiz is learning steno on a
Uni v4 and uses this as a live key display.

- **Remotes:** `origin` = `git@github.com:r-uiz/plover_svg_layout_display` (our fork),
  `upstream` = `opensteno/...`. Work lands on `origin/main`. A PR to upstream is optional.
- **Origin of this work:** started in the sibling Witsilog repo (`~/Desktop/Projects/Witsilog`,
  under `apps/chordle/plover/`) and moved here so it's tracked as a real fork. Chordle
  ([`witsilog.com/code/chordle`](https://witsilog.com/code/chordle)) is Ruiz's steno trainer; this plugin is a separate companion.

## What the fork adds

- **Layout Preset** dropdown (`Ctrl+S` in the display): **House** (B&W + egg-yolk gold
  `#f4b400`), **Mono** (pure monochrome), **Inverted** (dark caps, gold rim, for a floating
  overlay), or **Custom** (hand-set SVG/script paths).
- **Labels** and **Finger guides** checkboxes compose on top of the style. Finger guides =
  red dots at the steno resting position (traced from a reference diagram by pixel-detecting
  the markers).
- **Auto-clear After** (ms, `0` = Off, default 3000): Plover emits `stroked` per *committed
  chord*, not key up/down, so a highlight persists until the next stroke; this clears it.
- **Fade out on clear** (default on): snappy cross-fade of the chord back to neutral.
- **Double-click to close** the frameless display (alongside the stock `Ctrl+X`).

## Architecture

**Plugin convention (load via group swapping):**
- An SVG holds two top-level `<g>` per physical key: `id` (pressed) and `id_n` (neutral).
- `convert_stroke(stroke, translation) -> list[str]` returns one id per key (pressed or `_n`);
  the plugin re-emits only those groups, so pressed keys swap to the highlight. **Only
  top-level `<g id>` children survive subset rendering** - no shared `<defs>`/filters; any
  always-on overlay (the `guides` group, appended every stroke) must be self-contained.
- The Uni has duplicate physical keys (2x `S-`, 4x `*`, 2x `#`); `uni_convert.py` lights every
  copy of a pressed steno key.

**QtSvg is an SVG-Tiny subset** (Plover renders with `QSvgWidget`): **no blur filters, no
`dominant-baseline`, no fancy gradients.** Keep effects to solid fills, strokes, `rx` rounding.
Labels are vertically centred by offsetting the baseline (`dominant-baseline` is ignored).

**Uni presets** (`plover_svg_layout_display/resources/uni/`):
- `generate.mjs` emits 3 styles x {labels} x {guides} = **12 SVGs** + a shared `uni_convert.py`,
  from one inlined geometry table. Run: `node generate.mjs`. The geometry mirrors Witsilog's
  `apps/chordle/lib/steno/layouts.ts` (`uniLayout`) - keep them in sync by hand if it changes.
- `preview.html` renders all presets in a browser with a sample stroke lit.
- Presets **ship on disk** as `package_data` (`zip_safe=False`) and load via a `__file__`-relative
  filesystem path - NOT the Qt `.qrc`. The stock `en` defaults still load via `:/svgld/...`
  (compiled into `resources_rc.py`, which is gitignored and rebuilt at install).

**Key files:** `layout_config.py` (config schema: items, choices, names, order), `config_ui.py`
(builds the settings dialog from that schema), `layout_ui.py` (the Tool: preset resolution,
auto-clear `QTimer`, fade `QVariantAnimation`), `svg_parser.py` (`get_blend_svg` for the fade),
`svg_widget.py` (`update_blend`, `DUMMY_PATH`).

## Dev workflow

There is no standalone run; the plugin runs inside Plover. Edit -> regenerate if needed ->
dev-install -> restart Plover.

```bash
node plover_svg_layout_display/resources/uni/generate.mjs   # only if geometry/styles changed
./dev-install.sh                                            # copy package + presets into Plover
# then restart Plover (or toggle the SVG Layout Display tool off/on)
```

`dev-install.sh` copies the patched modules + `resources/uni/` over the installed plugin,
**preserving the compiled `resources_rc.py`** (the stock `:/svgld` defaults).

**Checks (no automated tests):**
- Syntax: `python3 -m py_compile plover_svg_layout_display/*.py`
- Import / Qt-API smoke test with Plover's own Python:
  ```bash
  PLPY="/Applications/Plover.app/Contents/Frameworks/Python.framework/Versions/3.13/bin/python3.13"
  SP="$HOME/Library/Application Support/plover/plugins/mac/lib/python/site-packages"
  PYTHONPATH="$SP" "$PLPY" -c "from plover_svg_layout_display import config_ui, svg_parser, svg_widget; print('ok')"
  ```
  (`layout_ui` imports `plover.gui_qt.tool`, which needs a running Qt app - test it by loading Plover.)

## Debugging

- **Plover log:** `~/Library/Application Support/plover/plover.log` - `grep -iE "svgld|svg_layout|Traceback"`.
  This is how the recursion crash (below) was found.
- **Installed plugin dir:** `~/Library/Application Support/plover/plugins/mac/lib/python/site-packages/plover_svg_layout_display/`.
- **Fixed bug (commit de8674d):** upstream `DUMMY_PATH` was `:/svgld/invalid.svg` but the resource
  is registered at `:/svgld/resources/invalid.svg`; a failed SVG load fell into
  `load_invalid -> load_svg -> load_invalid` forever (`RecursionError`). Fixed the path + guarded
  the fallback + fall back to the stock board when a system has no preset/custom SVG.

## Conventions (Ruiz's, vault-wide)

- **No em dashes** in any prose/UI - use a regular hyphen `-`.
- **No comments in source unless explaining a non-obvious WHY.**
- Prefer parameterized data (one geometry table -> generated SVGs) over duplicated render code.
- End git commit messages with the `Co-Authored-By: Claude ...` trailer. Push to `origin` (the fork).

## Current state

Uni presets + Labels/Finger-guides checkboxes + auto-clear + fade + double-click-close shipped;
recursion crash fixed. After updating, an old Plover config that used the previous `system_variant`
key won't match the new `system_style` - **re-pick the preset once in `Ctrl+S`** (the fix falls back
to the stock board until you do, instead of crashing).
