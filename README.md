# Plover SVG Layout Display (Uni fork)

> **Fork of [opensteno/plover_svg_layout_display](https://github.com/opensteno/plover_svg_layout_display)** with
> built-in **Stenokeyboards Uni v4** layouts and a few quality-of-life features.
> Upstream only ships the classic split board.

## What this fork adds

- **Bundled Uni v4 presets.** A **Layout Preset** dropdown (`Ctrl+S`) picks a
  style - **House** (B&W + egg-yolk gold), **Mono** (pure monochrome), or
  **Inverted** (dark caps that glow gold, for a floating overlay). No file paths
  to wire up; the SVGs ship in the package (`resources/uni/`).
- **Labels** and **Finger guides** checkboxes compose on top of the style.
  Finger guides are red dots marking the steno home/resting position.
- **Auto-clear After** (ms, `0` = Off): Plover emits `stroked` per committed
  chord, not key up/down, so a highlight otherwise stays lit until the next
  stroke. This clears it after a delay.
- **Fade out on clear**: a snappy cross-fade of the chord back to neutral
  instead of a hard cut (toggle).
- **Double-click to close** the frameless display (in addition to `Ctrl+X`).

The Uni presets are generated from one geometry definition by
`resources/uni/generate.mjs` (`node generate.mjs`) - 3 styles x labels x guides
= 12 SVGs plus a shared `uni_convert.py`. Install into Plover for development
with `./dev-install.sh`.

---

Display the last stroke in Plover, but ✨ *fancier* ✨

![svgld_1](https://user-images.githubusercontent.com/30435273/178503439-d0a2e839-0586-4c92-98bf-ba6df1727a25.png)

SVG Layout Display is based on the original [Layout Display Plugin](https://github.com/morinted/plover_layout_display) by [@morinted](https://github.com/morinted); it was designed to be more customizable than the original plugin, allowing the user to use custom shapes, and to define the behavior of these shapes using a custom script. The widget floats above other windows without a window frame, and can be configured to be translucent, which means that users have full control over how the display looks like.

If the display window looks like a black rectangle to you, you may need to install a compositor such as [picom](https://github.com/yshui/picom) for transparency to work.

## Settings

To open the settings page, focus on the display window and press `Ctrl + S` (or `Cmd + S` on mac). System settings are different for each stenographic system and will be recorded independently for each system.

To use the default purple layout, use `:/svgld/en_layout.svg` as the layout path and `:/svgld/en_convert.py` as the script path.

## Customization

![svgld_2](https://user-images.githubusercontent.com/30435273/178503535-26bcdb13-d74b-40cf-ab64-e6c0c8e6d4dc.png)

Layouts are defined by two separate files - the svg file, which defines all the shapes and their respective positions, and the py script, which defines which shapes are drawn based on the latest stroke and translation. 

In the svg file, shapes are defined based on top-level `<g>` elements, identified by the `id` attribute. IDs should be unique between different groups, but there is no limit on the number of groups you can add in the svg file.

The python script should contain a `convert_stroke`, which takes a tuple of strokes and a translation, and outputs a list of shape IDs. The order of the IDs in the list matters, as they are drawn from the head of the list to the tail, and later shapes are drawn above earlier ones.

```py
def convert_stroke(stroke: Tuple[str, ...], translation: str) -> List[str]:
    return ...
```

Note that the `stroke` parameter is a tuple of individual keys, such as `("K-", "W-", "-U", "-P")`