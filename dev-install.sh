#!/usr/bin/env bash
# Dev-install this fork into Plover's bundled site-packages without a full pip
# reinstall: copies the patched modules + the Uni presets over the installed
# plugin, preserving the compiled resources_rc.py (the stock :/svgld defaults).
#
# For a real install instead, point Plover's Plugins Manager / pip at this repo.
# Restart Plover (or toggle the SVG Layout Display tool) afterwards.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/plover_svg_layout_display"
PLOVER="$HOME/Library/Application Support/plover"
DST="$PLOVER/plugins/mac/lib/python/site-packages/plover_svg_layout_display"

if [ ! -d "$DST" ]; then
  echo "error: plugin not installed at $DST" >&2
  echo "       install 'plover_svg_layout_display' from Plover's Plugins Manager first." >&2
  exit 1
fi

echo "modules -> $DST"
for f in __init__.py qt_utils.py layout_config.py config_ui.py layout_ui.py svg_parser.py svg_widget.py; do
  cp "$SRC/$f" "$DST/$f"
done

echo "presets -> $DST/resources/uni"
mkdir -p "$DST/resources/uni"
cp "$SRC/resources/uni/"*.svg "$DST/resources/uni/"
cp "$SRC/resources/uni/uni_convert.py" "$DST/resources/uni/"

rm -rf "$DST/__pycache__"
# Drop the old data-dir from the pre-fork patch (presets now ship in-package).
rm -rf "$PLOVER/svgld_uni"

echo
echo "Done. In Plover: restart (or toggle the SVG Layout Display tool), then"
echo "Ctrl+S -> Layout Preset = House/Mono/Inverted, tick Labels / Finger guides."
